"""
Enhanced Error Handler for RAG

This module provides centralized error handling and user-friendly error messages.
"""

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, Union
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Enhanced error handler for providing detailed user-friendly error messages."""
    
    # Error categories and their user-friendly messages
    ERROR_MESSAGES = {
        # Authentication Errors
        "AUTH_INVALID_CREDENTIALS": {
            "title": "Authentication Failed",
            "message": "The email or password you entered is incorrect. Please check your credentials and try again.",
            "suggestion": "Make sure your email is spelled correctly and your password meets the requirements.",
            "category": "authentication"
        },
        "AUTH_USER_NOT_FOUND": {
            "title": "User Not Found",
            "message": "No account found with the provided email address.",
            "suggestion": "Please check your email address or register a new account.",
            "category": "authentication"
        },
        "AUTH_USER_ALREADY_EXISTS": {
            "title": "Account Already Exists",
            "message": "An account with this email address already exists.",
            "suggestion": "Try logging in instead, or use a different email address to register.",
            "category": "authentication"
        },
        "AUTH_INACTIVE_USER": {
            "title": "Account Inactive",
            "message": "Your account has been deactivated.",
            "suggestion": "Please contact support to reactivate your account.",
            "category": "authentication"
        },
        "AUTH_TOKEN_EXPIRED": {
            "title": "Session Expired",
            "message": "Your login session has expired. Please log in again.",
            "suggestion": "For security reasons, sessions expire after a period of inactivity.",
            "category": "authentication"
        },
        "AUTH_INVALID_TOKEN": {
            "title": "Invalid Session",
            "message": "Your login session is invalid or corrupted.",
            "suggestion": "Please log out and log in again to refresh your session.",
            "category": "authentication"
        },
        
        # Project Management Errors
        "PROJECT_NOT_FOUND": {
            "title": "Project Not Found",
            "message": "The requested project could not be found or you don't have access to it.",
            "suggestion": "Check the project ID or create a new project if needed.",
            "category": "project"
        },
        "PROJECT_ACCESS_DENIED": {
            "title": "Access Denied",
            "message": "You don't have permission to access this project.",
            "suggestion": "Make sure you're logged in with the correct account that owns this project.",
            "category": "project"
        },
        "PROJECT_ALREADY_EXISTS": {
            "title": "Project Already Exists",
            "message": "A project with this ID already exists in your account.",
            "suggestion": "Use a different project ID or access the existing project.",
            "category": "project"
        },
        "PROJECT_CREATION_FAILED": {
            "title": "Project Creation Failed",
            "message": "Unable to create the project due to a system error.",
            "suggestion": "Please try again in a few moments. If the problem persists, contact support.",
            "category": "project"
        },
        
        # File Upload Errors
        "FILE_UPLOAD_FAILED": {
            "title": "File Upload Failed",
            "message": "The file could not be uploaded due to a system error.",
            "suggestion": "Check your internet connection and try again. Make sure the file is not corrupted.",
            "category": "file"
        },
        "FILE_TYPE_NOT_SUPPORTED": {
            "title": "Unsupported File Type",
            "message": "This file type is not supported. We currently support PDF and text files.",
            "suggestion": "Please convert your file to PDF or text format before uploading.",
            "category": "file"
        },
        "FILE_SIZE_EXCEEDED": {
            "title": "File Too Large",
            "message": "The file size exceeds the maximum allowed limit.",
            "suggestion": "Please compress the file or split it into smaller parts before uploading.",
            "category": "file"
        },
        "FILE_NOT_FOUND": {
            "title": "File Not Found",
            "message": "The requested file could not be found in the project.",
            "suggestion": "Check if the file was uploaded successfully or try uploading it again.",
            "category": "file"
        },
        "FILE_PROCESSING_FAILED": {
            "title": "File Processing Failed",
            "message": "The file could not be processed due to an error in the content.",
            "suggestion": "Check if the file is readable and not corrupted. Try with a different file.",
            "category": "file"
        },
        
        # Processing Errors
        "PROCESSING_NO_FILES": {
            "title": "No Files to Process",
            "message": "There are no files in this project to process.",
            "suggestion": "Upload some files to the project before attempting to process them.",
            "category": "processing"
        },
        "PROCESSING_FAILED": {
            "title": "Processing Failed",
            "message": "Failed to process the files due to a system error.",
            "suggestion": "Please try again. If the problem persists, contact support.",
            "category": "processing"
        },
        "PROCESSING_PARTIAL_SUCCESS": {
            "title": "Partial Processing Success",
            "message": "Some files were processed successfully, but others failed.",
            "suggestion": "Check the failed files list and try processing them again.",
            "category": "processing"
        },
        
        # Vector Database Errors
        "VECTORDB_CONNECTION_FAILED": {
            "title": "Database Connection Failed",
            "message": "Unable to connect to the vector database.",
            "suggestion": "Please try again in a few moments. If the problem persists, contact support.",
            "category": "database"
        },
        "VECTORDB_INSERT_FAILED": {
            "title": "Database Insert Failed",
            "message": "Failed to store the processed data in the database.",
            "suggestion": "Please try again. If the problem persists, contact support.",
            "category": "database"
        },
        "VECTORDB_SEARCH_FAILED": {
            "title": "Search Failed",
            "message": "Unable to search the database for relevant information.",
            "suggestion": "Please try again. If the problem persists, contact support.",
            "category": "database"
        },
        "VECTORDB_COLLECTION_NOT_FOUND": {
            "title": "Project Not Indexed",
            "message": "This project has not been indexed yet or the index was corrupted.",
            "suggestion": "Process and index the project files before searching.",
            "category": "database"
        },
        
        # NLP/LLM Errors
        "NLP_SERVICE_UNAVAILABLE": {
            "title": "AI Service Unavailable",
            "message": "The AI service is currently unavailable or not properly configured.",
            "suggestion": "Please try again later or check your API configuration.",
            "category": "nlp"
        },
        "NLP_GENERATION_FAILED": {
            "title": "Answer Generation Failed",
            "message": "Unable to generate an answer to your question.",
            "suggestion": "Try rephrasing your question or try again later.",
            "category": "nlp"
        },
        "NLP_NO_RELEVANT_CONTENT": {
            "title": "No Relevant Content Found",
            "message": "No relevant information was found to answer your question.",
            "suggestion": "Try a different question or upload more relevant documents.",
            "category": "nlp"
        },
        
        # System Errors
        "INTERNAL_ERROR": {
            "title": "System Error",
            "message": "An unexpected error occurred in the system.",
            "suggestion": "Please try again. If the problem persists, contact support.",
            "category": "system"
        },
        "SERVICE_UNAVAILABLE": {
            "title": "Service Unavailable",
            "message": "The service is temporarily unavailable.",
            "suggestion": "Please try again in a few moments.",
            "category": "system"
        },
        "VALIDATION_ERROR": {
            "title": "Invalid Request",
            "message": "The request contains invalid data or parameters.",
            "suggestion": "Please check your input and try again.",
            "category": "system"
        }
    }
    
    @classmethod
    def get_error_response(
        cls,
        error_code: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ) -> JSONResponse:
        """
        Create a detailed error response with user-friendly information.
        
        Args:
            error_code: The error code from ERROR_MESSAGES
            status_code: HTTP status code
            details: Additional error details
            exception: Original exception for logging
            
        Returns:
            JSONResponse with detailed error information
        """
        error_info = cls.ERROR_MESSAGES.get(error_code, {
            "title": "Unknown Error",
            "message": "An unexpected error occurred.",
            "suggestion": "Please try again or contact support.",
            "category": "unknown"
        })
        
        # Log the error for debugging
        if exception:
            logger.error(f"Error {error_code}: {str(exception)}")
            logger.debug(f"Exception traceback: {traceback.format_exc()}")
        
        response_content = {
            "error": {
                "code": error_code,
                "title": error_info["title"],
                "message": error_info["message"],
                "suggestion": error_info["suggestion"],
                "category": error_info["category"],
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": status_code
            }
        }
        
        # Add additional details if provided
        if details:
            response_content["error"]["details"] = details
        
        return JSONResponse(
            status_code=status_code,
            content=response_content
        )
    
    @classmethod
    def handle_exception(
        cls,
        exception: Exception,
        context: str = "unknown",
        user_id: Optional[int] = None
    ) -> JSONResponse:
        """
        Handle exceptions and convert them to user-friendly error responses.
        
        Args:
            exception: The exception that occurred
            context: Context where the error occurred
            user_id: User ID for logging purposes
            
        Returns:
            JSONResponse with appropriate error information
        """
        error_msg = str(exception).lower()
        logger.error(f"ErrorHandler.handle_exception - Error message: {error_msg}")
        logger.error(f"ErrorHandler.handle_exception - Context: {context}")
        logger.error(f"ErrorHandler.handle_exception - Contains 'duplicate': {'duplicate' in error_msg}")
        logger.error(f"ErrorHandler.handle_exception - Contains 'already exists': {'already exists' in error_msg}")
        
        # Map common exceptions to error codes
        if "not found" in error_msg or "does not exist" in error_msg:
            if "project" in context:
                return cls.get_error_response("PROJECT_NOT_FOUND", 404, exception=exception)
            elif "file" in context:
                return cls.get_error_response("FILE_NOT_FOUND", 404, exception=exception)
            else:
                return cls.get_error_response("INTERNAL_ERROR", 404, exception=exception)
        
        elif "permission" in error_msg or "access" in error_msg:
            return cls.get_error_response("PROJECT_ACCESS_DENIED", 403, exception=exception)
        
        elif "duplicate" in error_msg or "already exists" in error_msg:
            logger.error("ErrorHandler.handle_exception - Duplicate detected!")
            if "project" in context:
                logger.error("ErrorHandler.handle_exception - Returning PROJECT_ALREADY_EXISTS")
                return cls.get_error_response("PROJECT_ALREADY_EXISTS", 409, exception=exception)
            elif "user" in context:
                return cls.get_error_response("AUTH_USER_ALREADY_EXISTS", 409, exception=exception)
            else:
                return cls.get_error_response("INTERNAL_ERROR", 409, exception=exception)
        
        elif "connection" in error_msg or "unavailable" in error_msg:
            return cls.get_error_response("SERVICE_UNAVAILABLE", 503, exception=exception)
        
        elif "validation" in error_msg or "invalid" in error_msg:
            return cls.get_error_response("VALIDATION_ERROR", 400, exception=exception)
        
        else:
            # Default to internal error
            logger.error("ErrorHandler.handle_exception - Defaulting to INTERNAL_ERROR")
            return cls.get_error_response("INTERNAL_ERROR", 500, exception=exception)
    
    @classmethod
    def create_success_response(
        cls,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        status_code: int = 200
    ) -> JSONResponse:
        """
        Create a standardized success response.
        
        Args:
            message: Success message
            data: Response data
            status_code: HTTP status code
            
        Returns:
            JSONResponse with success information
        """
        response_content = {
            "success": {
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": status_code
            }
        }
        
        if data:
            response_content["data"] = data
        
        return JSONResponse(
            status_code=status_code,
            content=response_content
        )

# Convenience functions for common error scenarios
def handle_auth_error(error_type: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Handle authentication-related errors."""
    return ErrorHandler.get_error_response(f"AUTH_{error_type}", 401, details)

def handle_project_error(error_type: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Handle project-related errors."""
    return ErrorHandler.get_error_response(f"PROJECT_{error_type}", 400, details)

def handle_file_error(error_type: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Handle file-related errors."""
    return ErrorHandler.get_error_response(f"FILE_{error_type}", 400, details)

def handle_processing_error(error_type: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Handle processing-related errors."""
    return ErrorHandler.get_error_response(f"PROCESSING_{error_type}", 400, details)

def handle_vectordb_error(error_type: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Handle vector database-related errors."""
    return ErrorHandler.get_error_response(f"VECTORDB_{error_type}", 500, details)

def handle_nlp_error(error_type: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Handle NLP/LLM-related errors."""
    return ErrorHandler.get_error_response(f"NLP_{error_type}", 503, details) 