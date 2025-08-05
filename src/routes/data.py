from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from models.db_schemes.minirag.schemes import User, Asset, DataChunk
from models.enums.ResponseEnums import ResponseSignal
from models.enums.ProcessingEnum import ProcessingEnum
from models.enums.AssetTypeEnum import AssetTypeEnum
from models import ProjectModel, AssetModel, ChunkModel
from routes.schemes.data import ProcessRequest
from utils.auth import get_current_active_user
from utils.error_handler import ErrorHandler, handle_project_error, handle_file_error, handle_processing_error
from controllers import NLPController, DataController, ProjectController, ProcessController
from helpers.config import get_settings, Settings
from database import get_db
import aiofiles
import os

logger = logging.getLogger(__name__)

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["data"],
)

@data_router.get("/projects")
async def get_user_projects(request: Request, page: int = 1, page_size: int = 10,
                          current_user: User = Depends(get_current_active_user)):
    """
    Get all projects for the current user with pagination.
    Provides detailed project information and better error handling.
    """
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10
            
        project_model = await ProjectModel.create_instance(
            db_client=request.app.db_client
        )
        
        projects, total_pages = await project_model.get_user_projects(
            user_id=current_user.user_id, page=page, page_size=page_size
        )
        
        # Get additional information for each project
        project_list = []
        for project in projects:
            # Get asset count for this project
            asset_model = await AssetModel.create_instance(
                db_client=request.app.db_client
            )
            
            try:
                assets = await asset_model.get_project_assets(project_id=project.project_id)
                asset_count = len(assets) if assets else 0
            except Exception as e:
                logger.warning(f"Could not get asset count for project {project.project_id}: {e}")
                asset_count = 0
            
            # Get chunk count for this project
            chunk_model = await ChunkModel.create_instance(
                db_client=request.app.db_client
            )
            
            try:
                total_chunks = await chunk_model.get_total_chunks_count(project_id=project.project_id)
            except Exception as e:
                logger.warning(f"Could not get chunk count for project {project.project_id}: {e}")
                total_chunks = 0
            
            project_info = {
                "project_id": project.project_id,
                "project_uuid": str(project.project_uuid),
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "asset_count": asset_count,
                "chunk_count": total_chunks,
                "status": "active"  # You can add more status logic here
            }
            project_list.append(project_info)
        
        return JSONResponse(
            content={
                "signal": "PROJECTS_RETRIEVED",
                "projects": project_list,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "total_projects": len(project_list),
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                },
                "user_info": {
                    "user_id": current_user.user_id,
                    "email": current_user.email
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving projects for user {current_user.user_id}: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": "PROJECTS_RETRIEVAL_FAILED",
                "error": "Failed to retrieve projects",
                "message": "An error occurred while retrieving your projects. Please try again.",
                "projects": [],
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "total_projects": 0,
                    "has_next": False,
                    "has_previous": False
                }
            }
        )

@data_router.post("/projects/create/{project_code}")
async def create_project(request: Request, project_code: int,
                       current_user: User = Depends(get_current_active_user)):
    """
    Create a new project for the current user using project_code.
    Handles race conditions and provides detailed error responses.
    """
    try:
        project_model = await ProjectModel.create_instance(
            db_client=request.app.db_client
        )

        # Check if project already exists for this user
        existing_project = await project_model.get_user_project(
            project_code=project_code,
            user_id=current_user.user_id
        )

        if existing_project:
            return handle_project_error("ALREADY_EXISTS", {
                "project_code": project_code,
                "user_id": current_user.user_id,
                "message": f"Project {project_code} already exists for this user",
                "project": {
                    "project_id": existing_project.project_id,
                    "project_code": existing_project.project_code,
                    "project_uuid": str(existing_project.project_uuid),
                    "created_at": existing_project.created_at.isoformat() if existing_project.created_at else None,
                    "updated_at": existing_project.updated_at.isoformat() if existing_project.updated_at else None
                }
            })

        # Create new project with user association
        project = await project_model.get_project_or_create_one(
            project_code=project_code,
            user_id=current_user.user_id
        )
        
        return ErrorHandler.create_success_response(
            message=f"Project {project_code} created successfully",
            data={
                "project": {
                    "project_id": project.project_id,
                    "project_code": project.project_code,
                    "project_uuid": str(project.project_uuid),
                    "created_at": project.created_at.isoformat() if project.created_at else None,
                    "updated_at": project.updated_at.isoformat() if project.updated_at else None
                }
            },
            status_code=201
        )
            
    except Exception as e:
        # Handle race condition or other database errors
        error_msg = str(e).lower()
        
        # Check for duplicate key errors first
        if "duplicate key" in error_msg or "unique constraint" in error_msg or "uniqueviolationerror" in error_msg or "duplicate" in error_msg:
            # Project was created by another request, try to get it
            try:
                existing_project = await project_model.get_user_project(
                    project_code=project_code,
                    user_id=current_user.user_id
                )
                
                if existing_project:
                    return handle_project_error("ALREADY_EXISTS", {
                        "project_code": project_code,
                        "user_id": current_user.user_id,
                        "message": f"Project {project_code} already exists for this user",
                        "project": {
                            "project_id": existing_project.project_id,
                            "project_code": existing_project.project_code,
                            "project_uuid": str(existing_project.project_uuid),
                            "created_at": existing_project.created_at.isoformat() if existing_project.created_at else None,
                            "updated_at": existing_project.updated_at.isoformat() if existing_project.updated_at else None
                        }
                    })
            except Exception as get_error:
                logger.error(f"Error getting existing project: {get_error}")
        
        # If not a duplicate key error, use the generic error handler
        logger.error(f"Unexpected error in create_project: {e}")
        return ErrorHandler.handle_exception(e, context="project", user_id=current_user.user_id)

@data_router.post("/upload/{project_code}")
async def upload_data(request: Request, project_code: int, file: UploadFile,
                      app_settings: Settings = Depends(get_settings),
                      current_user: User = Depends(get_current_active_user)):
        
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    # Get or create project with user association
    project = await project_model.get_project_or_create_one(
        project_code=project_code,
        user_id=current_user.user_id
    )

    # validate the file properties
    data_controller = DataController()

    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )

    project_dir_path = ProjectController().get_project_path(project_id=project.project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project.project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )

    # store the assets into the database
    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )

    asset_resource = Asset(
        asset_project_id=project.project_id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset=asset_resource)

    return JSONResponse(
            content={
                "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                "file_id": str(asset_record.asset_id),
            }
        )

@data_router.post("/process/{project_code}")
async def process_endpoint(request: Request, project_code: int, process_request: ProcessRequest,
                          current_user: User = Depends(get_current_active_user)):
    """
    Process uploaded files in a project and convert them into searchable chunks.
    
    Args:
        project_code: Project code to process files for
        process_request: Processing configuration (chunk_size, overlap_size, do_reset, file_id)
        
    Returns:
        JSON response with processing results or error details
        
    Raises:
        400: If no files found, invalid file_id, or processing fails
        403: If user doesn't have access to the project
    """
    
    # Validate input parameters
    chunk_size = process_request.chunk_size or 100
    overlap_size = process_request.overlap_size or 20
    do_reset = process_request.do_reset or 0
    
    # Log processing request for debugging
    logger.info(f"Processing request for project {project_code}: chunk_size={chunk_size}, overlap_size={overlap_size}, do_reset={do_reset}, file_id={process_request.file_id}")

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

    asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
        )

    project_files_ids = {}
    if process_request.file_id:
        # Try to find asset by asset_name first
        asset_record = await asset_model.get_asset_record(
            asset_project_id=project.project_id,
            asset_name=process_request.file_id
        )
        
        # If not found by asset_name, try to find by asset_id
        if asset_record is None:
            try:
                asset_id = int(process_request.file_id)
                # Get asset by asset_id
                asset_record = await asset_model.get_asset_by_id(
                    asset_id=asset_id,
                    asset_project_id=project.project_id
                )
            except (ValueError, TypeError):
                asset_record = None

        if asset_record is None:
            logger.warning(f"File with ID '{process_request.file_id}' not found in project {project_code}")
            return handle_file_error("NOT_FOUND", {
                "file_id": process_request.file_id,
                "project_id": project_code,
                "message": f"File with ID '{process_request.file_id}' not found in project {project_code}",
                "suggestion": "Check if the file was uploaded correctly or use a valid file_id"
            })

        project_files_ids = {
            asset_record.asset_id: asset_record.asset_name
        }
    
    else:
        # Get all files in the project
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value,
        )

        project_files_ids = {
            record.asset_id: record.asset_name
            for record in project_files
        }

    if len(project_files_ids) == 0:
        logger.warning(f"No files found in project {project_code} for processing")
        return handle_processing_error("NO_FILES", {
            "project_id": project_code,
            "message": f"No files found in project {project_code}",
            "suggestion": "Upload files to the project before processing"
        })
    
    # Process files using ProcessController
    process_controller = ProcessController(project_id=project.project_id)
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    if do_reset == 1:
        # delete associated vectors collection
        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        _ = await request.app.vectordb_client.delete_collection(collection_name=collection_name)

        # delete associated chunks
        _ = await chunk_model.delete_chunks_by_project_id(project_id=project.project_id)

    failed_files = []
    no_files = 0
    no_records = 0

    for asset_id, file_name in project_files_ids.items():
        try:
            # Get file content using ProcessController
            file_content = process_controller.get_file_content(file_id=file_name)

            if file_content is None:
                failed_files.append({
                    "file_id": str(asset_id),
                    "file_name": file_name,
                    "error": "Could not load file content"
                })
                continue

            # Process the file content
            file_chunks = process_controller.process_file_content(
                file_content=file_content,
                file_id=file_name,
                chunk_size=chunk_size,
                overlap_size=overlap_size
            )

            if not file_chunks or len(file_chunks) == 0:
                failed_files.append({
                    "file_id": str(asset_id),
                    "file_name": file_name,
                    "error": "No chunks generated"
                })
                continue

            # Create chunk records
            file_chunks_records = [
                DataChunk(
                    chunk_text=chunk.page_content,
                    chunk_metadata=chunk.metadata,
                    chunk_order=i+1,
                    chunk_project_id=project.project_id,
                    chunk_asset_id=asset_id
                )
                for i, chunk in enumerate(file_chunks)
            ]

            # Insert chunks into database
            chunk_count = await chunk_model.insert_many_chunks(chunks=file_chunks_records)
            no_files += 1
            no_records += chunk_count
            logger.info(f"Successfully processed file {file_name}: {len(file_chunks)} chunks created, {chunk_count} inserted")

        except Exception as e:
            logger.error(f"Error processing file {file_name}: {e}")
            failed_files.append({
                "file_id": str(asset_id),
                "file_name": file_name,
                "error": str(e)
            })

    # Log summary
    total_files = len(project_files_ids)
    logger.info(f"Processing complete: {no_files}/{total_files} files processed successfully, {len(failed_files)} failed")
    
    if failed_files:
        logger.warning(f"Failed files: {[f['file_id'] for f in failed_files]}")

    # Return detailed response
    response_content = {
        "signal": ResponseSignal.PROCESSING_SUCCESS.value,
        "inserted_chunks": no_records,
        "processed_files": no_files,
        "total_files": total_files,
    }
    
    # Include failed files info if any
    if failed_files:
        response_content["failed_files"] = failed_files
        response_content["warning"] = f"{len(failed_files)} file(s) could not be processed"
    
    return JSONResponse(content=response_content)

@data_router.get("/file/content/{project_code}/{asset_id}")
async def get_file_content(request: Request, project_code: int, asset_id: int,
                          current_user: User = Depends(get_current_active_user)):
    """
    Get file content for display in the UI.
    """
    try:
        project_model = await ProjectModel.create_instance(
            db_client=request.app.db_client
        )

        # Get project with user access validation
        project = await project_model.get_user_project(
            project_code=project_code,
            user_id=current_user.user_id
        )

        if not project:
            return handle_project_error("ACCESS_DENIED", {
                "project_code": project_code,
                "user_id": current_user.user_id,
                "message": "Project not found or access denied"
            })

        # Get asset details
        asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
        )
        
        asset = await asset_model.get_asset_by_id(asset_id=asset_id, asset_project_id=project.project_id)
        
        if not asset or asset.asset_project_id != project.project_id:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "signal": "FILE_NOT_FOUND",
                    "error": "File not found or access denied"
                }
            )

        # Get file content using ProcessController
        process_controller = ProcessController(project_id=str(project.project_id))
        file_content = process_controller.get_file_content(file_id=asset.asset_name)

        if file_content is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "signal": "FILE_CONTENT_NOT_FOUND",
                    "error": "Could not load file content"
                }
            )

        # Extract text content from file
        text_content = ""
        for doc in file_content:
            text_content += doc.page_content + "\n"

        return JSONResponse(
            content={
                "signal": "FILE_CONTENT_RETRIEVED",
                "file_name": asset.asset_name,
                "file_size": asset.asset_size,
                "content": text_content,
                "content_length": len(text_content)
            }
        )

    except Exception as e:
        return ErrorHandler.handle_exception(e, context="file_content", user_id=current_user.user_id)

@data_router.get("/projects/{project_code}")
async def get_project_details(request: Request, project_code: int,
                            current_user: User = Depends(get_current_active_user)):
    """
    Get detailed information about a specific project.
    Includes project metadata, asset count, chunk count, and processing status.
    """
    try:
        project_model = await ProjectModel.create_instance(
            db_client=request.app.db_client
        )
        
        # Get project with user access validation
        project = await project_model.get_user_project(
            project_code=project_code,
            user_id=current_user.user_id
        )
        
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "signal": "PROJECT_NOT_FOUND",
                    "error": "Project not found",
                    "message": f"Project {project_code} not found or you don't have access to it"
                }
            )
        
        # Get additional project information
        asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
        )
        
        chunk_model = await ChunkModel.create_instance(
            db_client=request.app.db_client
        )
        
        try:
            assets = await asset_model.get_project_assets(project_id=project.project_id)
            asset_count = len(assets) if assets else 0
            asset_details = [
                {
                    "asset_id": asset.asset_id,
                    "asset_name": asset.asset_name,
                    "asset_type": asset.asset_type,
                    "asset_size": asset.asset_size,
                    "created_at": asset.created_at.isoformat() if asset.created_at else None
                }
                for asset in assets
            ] if assets else []
        except Exception as e:
            logger.warning(f"Could not get asset details for project {project.project_id}: {e}")
            asset_count = 0
            asset_details = []
        
        try:
            total_chunks = await chunk_model.get_total_chunks_count(project_id=project.project_id)
        except Exception as e:
            logger.warning(f"Could not get chunk count for project {project.project_id}: {e}")
            total_chunks = 0
        
        # Check if project has been indexed (has vector collection)
        try:
            nlp_controller = NLPController(
                vectordb_client=request.app.vectordb_client,
                generation_client=request.app.generation_client,
                embedding_client=request.app.embedding_client,
                template_parser=request.app.template_parser,
            )
            
            collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
            collection_exists = await request.app.vectordb_client.is_collection_existed(collection_name=collection_name)
            
            if collection_exists:
                collection_info = request.app.vectordb_client.get_collection_info(collection_name=collection_name)
                vector_count = getattr(collection_info, 'vectors_count', 0) or 0
                points_count = getattr(collection_info, 'points_count', 0) or 0
                is_indexed = True
            else:
                vector_count = 0
                points_count = 0
                is_indexed = False
                
        except Exception as e:
            logger.warning(f"Could not check indexing status for project {project.project_id}: {e}")
            vector_count = 0
            points_count = 0
            is_indexed = False
        
        project_details = {
            "project_id": project.project_id,
            "project_code": project.project_code,
            "project_uuid": str(project.project_uuid),
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "asset_count": asset_count,
            "chunk_count": total_chunks,
            "vector_count": vector_count,
            "points_count": points_count,
            "is_indexed": is_indexed,
            "status": "active" if is_indexed else "pending_indexing",
            "assets": asset_details
        }
        
        return JSONResponse(
            content={
                "signal": "PROJECT_DETAILS_RETRIEVED",
                "project": project_details,
                "user_info": {
                    "user_id": current_user.user_id,
                    "email": current_user.email
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving project details for project {project_code}, user {current_user.user_id}: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": "PROJECT_DETAILS_RETRIEVAL_FAILED",
                "error": "Failed to retrieve project details",
                "message": "An error occurred while retrieving project details. Please try again."
            }
        )

@data_router.delete("/projects/{project_code}")
async def delete_project(request: Request, project_code: int,
                       current_user: User = Depends(get_current_active_user)):
    """
    Delete a project and all its associated data.
    This will remove the project, its assets, chunks, and vector data.
    """
    try:
        project_model = await ProjectModel.create_instance(
            db_client=request.app.db_client
        )
        
        # Get project with user access validation
        project = await project_model.get_user_project(
            project_code=project_code,
            user_id=current_user.user_id
        )
        
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "signal": "PROJECT_NOT_FOUND",
                    "error": "Project not found",
                    "message": f"Project {project_code} not found or you don't have access to it"
                }
            )
        
        # Get project details before deletion
        asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
        )
        
        chunk_model = await ChunkModel.create_instance(
            db_client=request.app.db_client
        )
        
        try:
            assets = await asset_model.get_project_assets(project_id=project.project_id)
            asset_count = len(assets) if assets else 0
        except Exception as e:
            logger.warning(f"Could not get asset count for project {project.project_id}: {e}")
            asset_count = 0
        
        try:
            total_chunks = await chunk_model.get_total_chunks_count(project_id=project.project_id)
        except Exception as e:
            logger.warning(f"Could not get chunk count for project {project.project_id}: {e}")
            total_chunks = 0
        
        # Delete vector collection if it exists
        try:
            nlp_controller = NLPController(
                vectordb_client=request.app.vectordb_client,
                generation_client=request.app.generation_client,
                embedding_client=request.app.embedding_client,
                template_parser=request.app.template_parser,
            )
            
            collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
            collection_exists = await request.app.vectordb_client.is_collection_existed(collection_name=collection_name)
            
            if collection_exists:
                await request.app.vectordb_client.delete_collection(collection_name=collection_name)
                logger.info(f"Deleted vector collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Could not delete vector collection for project {project.project_id}: {e}")
        
        # Delete project from database (this will cascade to assets and chunks)
        try:
            await project_model.delete_project(project_id=project.project_id)
            logger.info(f"Deleted project {project.project_id} (code: {project_code}) for user {current_user.user_id}")
        except Exception as e:
            logger.error(f"Error deleting project {project.project_id}: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "signal": "PROJECT_DELETION_FAILED",
                    "error": "Failed to delete project",
                    "message": "An error occurred while deleting the project. Please try again."
                }
            )
        
        return JSONResponse(
            content={
                "signal": "PROJECT_DELETED",
                "message": f"Project {project_code} deleted successfully",
                "deleted_project": {
                    "project_id": project.project_id,
                    "project_code": project.project_code,
                    "project_uuid": str(project.project_uuid),
                    "asset_count": asset_count,
                    "chunk_count": total_chunks,
                    "deleted_at": project.updated_at.isoformat() if project.updated_at else None
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error deleting project {project_code} for user {current_user.user_id}: {e}")
