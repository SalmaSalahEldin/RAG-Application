from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import aiofiles
from models import ResponseSignal
import logging
from .schemes.data import ProcessRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemes import DataChunk, Asset, User
from models.enums.AssetTypeEnum import AssetTypeEnum
from controllers import NLPController
from utils.auth import get_current_active_user

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["data"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: int, file: UploadFile,
                      app_settings: Settings = Depends(get_settings),
                      current_user: User = Depends(get_current_active_user)):
        
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
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

    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
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

@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id: int, process_request: ProcessRequest,
                          current_user: User = Depends(get_current_active_user)):
    """
    Process uploaded files in a project and convert them into searchable chunks.
    
    Args:
        project_id: Project ID to process files for
        process_request: Processing configuration (chunk_size, overlap_size, do_reset, file_id)
        
    Returns:
        JSON response with processing results or error details
        
    Raises:
        400: If no files found, invalid file_id, or processing fails
    """
    
    # Validate input parameters
    chunk_size = process_request.chunk_size or 100
    overlap_size = process_request.overlap_size or 20
    do_reset = process_request.do_reset or 0
    
    # Log processing request for debugging
    logger.info(f"Processing request for project {project_id}: chunk_size={chunk_size}, overlap_size={overlap_size}, do_reset={do_reset}, file_id={process_request.file_id}")

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

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
            logger.warning(f"File with ID '{process_request.file_id}' not found in project {project_id}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value,
                    "message": f"File with ID '{process_request.file_id}' not found in project {project_id}",
                    "suggestion": "Check if the file was uploaded correctly or use a valid file_id"
                }
            )

        project_files_ids = {
            asset_record.asset_id: asset_record.asset_name
        }
    
    else:
        

        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value,
        )

        project_files_ids = {
            record.asset_id: record.asset_name
            for record in project_files
        }

    if len(project_files_ids) == 0:
        logger.warning(f"No files found in project {project_id} for processing")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.NO_FILES_ERROR.value,
                "message": f"No files found in project {project_id}",
                "suggestion": f"Upload files first using POST /api/v1/data/upload/{project_id}"
            }
        )
    
    process_controller = ProcessController(project_id=project_id)

    no_records = 0
    no_files = 0

    chunk_model = await ChunkModel.create_instance(
                        db_client=request.app.db_client
                    )

    if do_reset == 1:
        # delete associated vectors collection
        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        _ = await request.app.vectordb_client.delete_collection(collection_name=collection_name)

        # delete associated chunks
        _ = await chunk_model.delete_chunks_by_project_id(
            project_id=project.project_id
        )

    failed_files = []
    processed_files_details = []
    
    for asset_id, file_id in project_files_ids.items():
        logger.info(f"Processing file: {file_id} (asset_id: {asset_id})")

        file_content = process_controller.get_file_content(file_id=file_id)

        if file_content is None:
            error_msg = f"Failed to load content from file: {file_id}"
            logger.error(error_msg)
            failed_files.append({"file_id": file_id, "reason": "Could not load file content", "asset_id": asset_id})
            continue

        file_chunks = process_controller.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )

        if file_chunks is None or len(file_chunks) == 0:
            error_msg = f"No chunks generated for file {file_id} in project {project_id}"
            logger.error(error_msg)
            failed_files.append({"file_id": file_id, "reason": "No text chunks generated", "asset_id": asset_id})
            continue

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

        chunk_count = await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_records += chunk_count
        no_files += 1
        
        processed_files_details.append({
            "file_id": file_id, 
            "asset_id": asset_id, 
            "chunks_created": len(file_chunks),
            "chunks_inserted": chunk_count
        })
        
        logger.info(f"Successfully processed file {file_id}: {len(file_chunks)} chunks created, {chunk_count} inserted")

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
