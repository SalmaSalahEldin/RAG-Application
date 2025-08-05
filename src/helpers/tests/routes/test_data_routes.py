"""
Tests for data routes.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from fastapi import status
import io

class TestDataRoutes:
    """Test cases for data routes."""

    def test_get_user_projects_success(self, test_client, auth_headers):
        """Test getting user projects successfully."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_user_projects') as mock_get_projects:
                mock_get_projects.return_value = ([], 0)
                
                response = test_client.get("/api/v1/data/projects", headers=auth_headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "signal" in data
                assert data["signal"] == "PROJECTS_RETRIEVED"

    def test_get_user_projects_unauthorized(self, test_client):
        """Test getting user projects without authentication."""
        response = test_client.get("/api/v1/data/projects")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_project_success(self, test_client, auth_headers):
        """Test creating a project successfully."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_project_or_create_one') as mock_create:
                mock_project = Mock()
                mock_project.project_id = 1
                mock_project.project_code = 1
                mock_create.return_value = mock_project
                
                response = test_client.post("/api/v1/data/projects/create/1", headers=auth_headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "signal" in data
                assert data["signal"] == "PROJECT_CREATED"

    def test_create_project_duplicate(self, test_client, auth_headers):
        """Test creating a project with duplicate project code."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_project_or_create_one') as mock_create:
                # Simulate duplicate key error
                from sqlalchemy.exc import IntegrityError
                mock_create.side_effect = IntegrityError("duplicate key", None, None)
                
                response = test_client.post("/api/v1/data/projects/create/1", headers=auth_headers)
                
                assert response.status_code == status.HTTP_409_CONFLICT
                data = response.json()
                assert "signal" in data
                assert data["signal"] == "PROJECT_ALREADY_EXISTS"

    def test_upload_file_success(self, test_client, auth_headers):
        """Test uploading a file successfully."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_user_project') as mock_get_project:
                mock_project = Mock()
                mock_project.project_id = 1
                mock_get_project.return_value = mock_project
                
                with patch('models.AssetModel.create_asset') as mock_create_asset:
                    mock_asset = Mock()
                    mock_asset.asset_id = 1
                    mock_create_asset.return_value = mock_asset
                    
                    # Create a test file
                    test_file = io.BytesIO(b"test file content")
                    files = {"file": ("test.txt", test_file, "text/plain")}
                    
                    response = test_client.post("/api/v1/data/upload/1", files=files, headers=auth_headers)
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert "signal" in data
                    assert data["signal"] == "FILE_UPLOADED"

    def test_upload_file_invalid_project(self, test_client, auth_headers):
        """Test uploading file to invalid project."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_user_project') as mock_get_project:
                mock_get_project.return_value = None
                
                test_file = io.BytesIO(b"test file content")
                files = {"file": ("test.txt", test_file, "text/plain")}
                
                response = test_client.post("/api/v1/data/upload/999", files=files, headers=auth_headers)
                
                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_upload_file_no_file(self, test_client, auth_headers):
        """Test uploading without file."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            response = test_client.post("/api/v1/data/upload/1", headers=auth_headers)
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_process_project_success(self, test_client, auth_headers):
        """Test processing a project successfully."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_user_project') as mock_get_project:
                mock_project = Mock()
                mock_project.project_id = 1
                mock_get_project.return_value = mock_project
                
                with patch('controllers.ProcessController.process_project') as mock_process:
                    mock_process.return_value = True
                    
                    process_data = {"process_type": "text"}
                    response = test_client.post("/api/v1/data/process/1", json=process_data, headers=auth_headers)
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert "signal" in data
                    assert data["signal"] == "PROJECT_PROCESSED"

    def test_get_project_details_success(self, test_client, auth_headers):
        """Test getting project details successfully."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_user_project') as mock_get_project:
                mock_project = Mock()
                mock_project.project_id = 1
                mock_project.project_code = 1
                mock_get_project.return_value = mock_project
                
                with patch('models.AssetModel.get_project_assets') as mock_get_assets:
                    mock_get_assets.return_value = []
                    
                    with patch('models.ChunkModel.get_total_chunks_count') as mock_get_chunks:
                        mock_get_chunks.return_value = 0
                        
                        response = test_client.get("/api/v1/data/projects/1", headers=auth_headers)
                        
                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert "signal" in data
                        assert data["signal"] == "PROJECT_DETAILS_RETRIEVED"

    def test_get_project_details_not_found(self, test_client, auth_headers):
        """Test getting project details for non-existent project."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_user_project') as mock_get_project:
                mock_get_project.return_value = None
                
                response = test_client.get("/api/v1/data/projects/999", headers=auth_headers)
                
                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_project_success(self, test_client, auth_headers):
        """Test deleting a project successfully."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.delete_project') as mock_delete:
                mock_delete.return_value = True
                
                response = test_client.delete("/api/v1/data/projects/1", headers=auth_headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "signal" in data
                assert data["signal"] == "PROJECT_DELETED"

    def test_delete_project_not_found(self, test_client, auth_headers):
        """Test deleting a non-existent project."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.delete_project') as mock_delete:
                mock_delete.return_value = False
                
                response = test_client.delete("/api/v1/data/projects/999", headers=auth_headers)
                
                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_file_content_success(self, test_client, auth_headers):
        """Test getting file content successfully."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_user_project') as mock_get_project:
                mock_project = Mock()
                mock_project.project_id = 1
                mock_get_project.return_value = mock_project
                
                with patch('models.AssetModel.get_asset_by_id') as mock_get_asset:
                    mock_asset = Mock()
                    mock_asset.asset_id = 1
                    mock_asset.asset_name = "test.txt"
                    mock_asset.asset_size = 1024
                    mock_asset.asset_project_id = 1
                    mock_get_asset.return_value = mock_asset
                    
                    with patch('controllers.ProcessController.get_file_content') as mock_get_content:
                        mock_content = [Mock(page_content="test content")]
                        mock_get_content.return_value = mock_content
                        
                        response = test_client.get("/api/v1/data/file/content/1/1", headers=auth_headers)
                        
                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert "signal" in data
                        assert data["signal"] == "FILE_CONTENT_RETRIEVED"

    def test_get_file_content_not_found(self, test_client, auth_headers):
        """Test getting file content for non-existent file."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_user_project') as mock_get_project:
                mock_project = Mock()
                mock_project.project_id = 1
                mock_get_project.return_value = mock_project
                
                with patch('models.AssetModel.get_asset_by_id') as mock_get_asset:
                    mock_get_asset.return_value = None
                    
                    response = test_client.get("/api/v1/data/file/content/1/999", headers=auth_headers)
                    
                    assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pagination_parameters(self, test_client, auth_headers):
        """Test pagination parameters in get_user_projects."""
        with patch('routes.data.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_get_user.return_value = mock_user
            
            with patch('models.ProjectModel.get_user_projects') as mock_get_projects:
                mock_get_projects.return_value = ([], 0)
                
                # Test with custom pagination
                response = test_client.get("/api/v1/data/projects?page=2&page_size=5", headers=auth_headers)
                
                assert response.status_code == status.HTTP_200_OK
                # Verify that the pagination parameters were passed correctly
                mock_get_projects.assert_called_with(user_id=1, page=2, page_size=5) 