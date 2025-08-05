"""
Tests for ErrorHandler utility.
"""

import pytest
from unittest.mock import Mock, patch
from utils.error_handler import ErrorHandler
from fastapi import HTTPException
from fastapi.responses import JSONResponse

class TestErrorHandler:
    """Test cases for ErrorHandler class."""

    def test_handle_exception_general_error(self):
        """Test handling general exceptions."""
        exception = Exception("Test error")
        
        result = ErrorHandler.handle_exception(exception, context="test", user_id=1)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        data = result.body.decode()
        assert "INTERNAL_ERROR" in data
        assert "Test error" in data

    def test_handle_exception_with_user_id(self):
        """Test handling exceptions with user ID."""
        exception = Exception("Test error")
        
        result = ErrorHandler.handle_exception(exception, context="test", user_id=123)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        data = result.body.decode()
        assert "INTERNAL_ERROR" in data

    def test_handle_exception_without_user_id(self):
        """Test handling exceptions without user ID."""
        exception = Exception("Test error")
        
        result = ErrorHandler.handle_exception(exception, context="test")
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

    def test_handle_exception_database_error(self):
        """Test handling database exceptions."""
        from sqlalchemy.exc import SQLAlchemyError
        exception = SQLAlchemyError("Database error")
        
        result = ErrorHandler.handle_exception(exception, context="database", user_id=1)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        data = result.body.decode()
        assert "DATABASE_ERROR" in data

    def test_handle_exception_validation_error(self):
        """Test handling validation exceptions."""
        from pydantic import ValidationError
        exception = ValidationError.from_exception_data("Test", [])
        
        result = ErrorHandler.handle_exception(exception, context="validation", user_id=1)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422
        data = result.body.decode()
        assert "VALIDATION_ERROR" in data

    def test_handle_exception_authentication_error(self):
        """Test handling authentication exceptions."""
        from fastapi import HTTPException
        exception = HTTPException(status_code=401, detail="Unauthorized")
        
        result = ErrorHandler.handle_exception(exception, context="auth", user_id=1)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        data = result.body.decode()
        assert "AUTHENTICATION_ERROR" in data

    def test_handle_exception_file_error(self):
        """Test handling file-related exceptions."""
        exception = FileNotFoundError("File not found")
        
        result = ErrorHandler.handle_exception(exception, context="file", user_id=1)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        data = result.body.decode()
        assert "FILE_ERROR" in data

    def test_handle_exception_network_error(self):
        """Test handling network exceptions."""
        exception = ConnectionError("Network error")
        
        result = ErrorHandler.handle_exception(exception, context="network", user_id=1)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 503
        data = result.body.decode()
        assert "NETWORK_ERROR" in data

    def test_handle_exception_timeout_error(self):
        """Test handling timeout exceptions."""
        exception = TimeoutError("Request timeout")
        
        result = ErrorHandler.handle_exception(exception, context="timeout", user_id=1)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 408
        data = result.body.decode()
        assert "TIMEOUT_ERROR" in data

    def test_handle_exception_unknown_error(self):
        """Test handling unknown exceptions."""
        exception = Exception("Unknown error type")
        
        result = ErrorHandler.handle_exception(exception, context="unknown", user_id=1)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        data = result.body.decode()
        assert "INTERNAL_ERROR" in data

    def test_handle_exception_with_logging(self):
        """Test that exceptions are properly logged."""
        exception = Exception("Test error")
        
        with patch('utils.error_handler.logger') as mock_logger:
            ErrorHandler.handle_exception(exception, context="test", user_id=1)
            
            # Verify that the error was logged
            mock_logger.error.assert_called_once()

    def test_handle_exception_response_structure(self):
        """Test that error response has correct structure."""
        exception = Exception("Test error")
        
        result = ErrorHandler.handle_exception(exception, context="test", user_id=1)
        
        # Parse the JSON response
        import json
        data = json.loads(result.body.decode())
        
        # Check required fields
        assert "signal" in data
        assert "error" in data
        assert "message" in data
        assert data["signal"] == "INTERNAL_ERROR"

    def test_handle_exception_different_contexts(self):
        """Test handling exceptions in different contexts."""
        exception = Exception("Test error")
        
        contexts = ["auth", "database", "file", "network", "validation"]
        
        for context in contexts:
            result = ErrorHandler.handle_exception(exception, context=context, user_id=1)
            assert isinstance(result, JSONResponse)
            assert result.status_code in [400, 401, 404, 408, 422, 500, 503]

    def test_handle_exception_with_details(self):
        """Test handling exceptions with additional details."""
        exception = Exception("Test error")
        
        result = ErrorHandler.handle_exception(
            exception, 
            context="test", 
            user_id=1,
            details={"additional": "info"}
        )
        
        assert isinstance(result, JSONResponse)
        data = result.body.decode()
        assert "INTERNAL_ERROR" in data

    def test_handle_exception_none_exception(self):
        """Test handling None exception."""
        result = ErrorHandler.handle_exception(None, context="test", user_id=1)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        data = result.body.decode()
        assert "INTERNAL_ERROR" in data

    def test_handle_exception_with_custom_message(self):
        """Test handling exceptions with custom error message."""
        exception = Exception("Original error")
        
        result = ErrorHandler.handle_exception(
            exception, 
            context="test", 
            user_id=1,
            custom_message="Custom error message"
        )
        
        assert isinstance(result, JSONResponse)
        data = result.body.decode()
        assert "Custom error message" in data 