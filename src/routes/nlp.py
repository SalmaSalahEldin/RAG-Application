from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
import time

from models.db_schemes.minirag.schemes import User, QueryLog
from models.enums.ResponseEnums import ResponseSignal
from models import ProjectModel, ChunkModel
from routes.schemes.nlp import SearchRequest, PushRequest
from utils.auth import get_current_active_user
from utils.error_handler import ErrorHandler, handle_project_error, handle_nlp_error, handle_vectordb_error
from controllers import NLPController
from database import get_db
from tqdm.auto import tqdm
from sqlalchemy import select

logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["nlp"],
)

@nlp_router.post("/index/push/{project_code}")
async def index_project(request: Request, project_code: int, push_request: PushRequest,
                       current_user: User = Depends(get_current_active_user)):

    # Check if vector database client is available
    if request.app.vectordb_client is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "signal": "SERVICE_UNAVAILABLE",
                "error": "Vector database client is not initialized. Please check your configuration.",
                "message": "NLP features are currently unavailable. Please ensure OpenAI API key is configured."
            }
        )

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    # Get project with user access validation
    project = await project_model.get_user_project(
        project_code=project_code,
        user_id=current_user.user_id
    )

    # Check if user has access to this project
    if not project:
        return handle_project_error("ACCESS_DENIED", {
            "project_code": project_code,
            "user_id": current_user.user_id,
            "message": "Project not found or access denied"
        })
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    try:
        has_records = True
        page_no = 1
        inserted_items_count = 0
        idx = 0

        # create collection if not exists
        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)

        _ = await request.app.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=request.app.embedding_client.embedding_size,
            do_reset=push_request.do_reset,
        )

        # setup batching
        total_chunks_count = await chunk_model.get_total_chunks_count(project_id=project.project_id)
        pbar = tqdm(total=total_chunks_count, desc="Vector Indexing", position=0)

        while has_records:
            page_chunks = await chunk_model.get_project_chunks(project_id=project.project_id, page_no=page_no)
            if len(page_chunks):
                page_no += 1
            
            if not page_chunks or len(page_chunks) == 0:
                has_records = False
                break

            chunks_ids =  [ c.chunk_id for c in page_chunks ]
            idx += len(page_chunks)
            
            is_inserted = await nlp_controller.index_into_vector_db(
                project=project,
                chunks=page_chunks,
                chunks_ids=chunks_ids
            )

            if not is_inserted:
                return handle_vectordb_error("INSERT_FAILED", {
                    "project_id": project.project_id,
                    "message": "Failed to insert data into vector database"
                })

            pbar.update(len(page_chunks))
            inserted_items_count += len(page_chunks)
            
        return JSONResponse(
            content={
                "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
                "inserted_items_count": inserted_items_count
            }
        )
    
    except ValueError as e:
        return handle_nlp_error("SERVICE_UNAVAILABLE", {
            "project_id": project.project_id,
            "error": str(e),
            "message": "NLP features are currently unavailable. Please check your configuration."
        })
    except Exception as e:
        return ErrorHandler.handle_exception(e, context="nlp", user_id=current_user.user_id)

@nlp_router.get("/index/info/{project_code}")
async def get_project_index_info(request: Request, project_code: int,
                               current_user: User = Depends(get_current_active_user)):
    
    # Check if vector database client is available
    if request.app.vectordb_client is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "signal": "SERVICE_UNAVAILABLE",
                "error": "Vector database client is not initialized. Please check your configuration.",
                "message": "NLP features are currently unavailable. Please ensure OpenAI API key is configured."
            }
        )

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    # Get project with user access validation
    project = await project_model.get_user_project(
        project_code=project_code,
        user_id=current_user.user_id
    )

    # Check if user has access to this project
    if not project:
        return handle_project_error("ACCESS_DENIED", {
            "project_code": project_code,
            "user_id": current_user.user_id,
            "message": "Project not found or access denied"
        })

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    try:
        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        collection_info = request.app.vectordb_client.get_collection_info(collection_name=collection_name)
        
        # Convert CollectionInfo to dict for JSON serialization
        # Handle both Qdrant CollectionInfo object and dict responses
        if hasattr(collection_info, '__dict__'):
            # It's an object, try to access common attributes
            collection_info_dict = {
                "collection_name": collection_name,
                "vectors_count": getattr(collection_info, 'vectors_count', 0) or 0,
                "points_count": getattr(collection_info, 'points_count', 0) or 0,
                "segments_count": getattr(collection_info, 'segments_count', 0) or 0,
                "status": getattr(collection_info, 'status', 'unknown')
            }
        elif isinstance(collection_info, dict):
            # It's already a dict
            collection_info_dict = {
                "collection_name": collection_name,
                "vectors_count": collection_info.get('vectors_count', 0),
                "points_count": collection_info.get('points_count', 0),
                "segments_count": collection_info.get('segments_count', 0),
                "status": collection_info.get('status', 'unknown')
            }
        else:
            # Fallback for unknown types
            collection_info_dict = {
                "collection_name": collection_name,
                "vectors_count": 0,
                "points_count": 0,
                "segments_count": 0,
                "status": "unknown"
            }

        return JSONResponse(
            content={
                "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
                "collection_info": collection_info_dict
            }
        )
    
    except ValueError as e:
        return handle_nlp_error("SERVICE_UNAVAILABLE", {
            "project_id": project_code,
            "error": str(e),
            "message": "NLP features are currently unavailable. Please check your configuration."
        })
    except Exception as e:
        return ErrorHandler.handle_exception(e, context="nlp", user_id=current_user.user_id)

@nlp_router.post("/index/search/{project_code}")
async def search_index(request: Request, project_code: int, search_request: SearchRequest,
                      current_user: User = Depends(get_current_active_user)):
    
    # Check if vector database client is available
    if request.app.vectordb_client is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "signal": "SERVICE_UNAVAILABLE",
                "error": "Vector database client is not initialized. Please check your configuration.",
                "message": "NLP features are currently unavailable. Please ensure OpenAI API key is configured."
            }
        )

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    # Get project with user access validation
    project = await project_model.get_user_project(
        project_code=project_code,
        user_id=current_user.user_id
    )

    # Check if user has access to this project
    if not project:
        return handle_project_error("ACCESS_DENIED", {
            "project_code": project_code,
            "user_id": current_user.user_id,
            "message": "Project not found or access denied"
        })

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    try:
        results = await nlp_controller.search_vector_db_collection(
            project=project, text=search_request.text, limit=search_request.limit
        )

        if not results:
            return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value
                    }
                )
        
        return JSONResponse(
            content={
                "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
                "results": [ result.dict()  for result in results ]
            }
        )
    
    except ValueError as e:
        return handle_nlp_error("SERVICE_UNAVAILABLE", {
            "project_id": project_code,
            "error": str(e),
            "message": "NLP features are currently unavailable. Please check your configuration."
        })
    except Exception as e:
        return ErrorHandler.handle_exception(e, context="nlp", user_id=current_user.user_id)

@nlp_router.post("/index/answer/{project_code}")
async def answer_rag(request: Request, project_code: int, search_request: SearchRequest,
                    current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    
    # Check if vector database client is available
    if request.app.vectordb_client is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "signal": "SERVICE_UNAVAILABLE",
                "error": "Vector database client is not initialized. Please check your configuration.",
                "message": "NLP features are currently unavailable. Please ensure OpenAI API key is configured."
            }
        )

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    # Get project with user access validation
    project = await project_model.get_user_project(
        project_code=project_code,
        user_id=current_user.user_id
    )

    # Check if user has access to this project
    if not project:
        return handle_project_error("ACCESS_DENIED", {
            "project_code": project_code,
            "user_id": current_user.user_id,
            "message": "Project not found or access denied"
        })

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    try:
        # Start timing
        start_time = time.time()
        
        answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
            project=project,
            query=search_request.text,
            limit=search_request.limit,
        )

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        if not answer:
            return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.RAG_ANSWER_ERROR.value,
                        "error": "Failed to generate answer"
                    }
            )
        
        # Log the query
        query_log = QueryLog(
            user_id=current_user.user_id,
            question=search_request.text,
            llm_response=answer,
            response_time_ms=response_time_ms
        )
        
        db.add(query_log)
        await db.commit()
        
        return JSONResponse(
            content={
                "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
                "answer": answer,
                "full_prompt": full_prompt,
                "chat_history": chat_history,
                "response_time_ms": response_time_ms
            }
        )
    
    except ValueError as e:
        return handle_nlp_error("SERVICE_UNAVAILABLE", {
            "project_id": project_code,
            "error": str(e),
            "message": "NLP features are currently unavailable. Please check your configuration."
        })
    except Exception as e:
        return ErrorHandler.handle_exception(e, context="nlp", user_id=current_user.user_id)
