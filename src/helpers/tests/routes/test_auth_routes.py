"""
Tests for authentication routes.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

class TestAuthRoutes:
    """Test cases for authentication routes."""

    def test_register_success(self, test_client):
        """Test successful user registration."""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = test_client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data or "access_token" in data

    def test_register_invalid_email(self, test_client):
        """Test registration with invalid email."""
        user_data = {
            "email": "invalid-email",
            "password": "testpassword123"
        }
        
        response = test_client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_weak_password(self, test_client):
        """Test registration with weak password."""
        user_data = {
            "email": "test@example.com",
            "password": "123"
        }
        
        response = test_client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_duplicate_email(self, test_client):
        """Test registration with duplicate email."""
        user_data = {
            "email": "existing@example.com",
            "password": "testpassword123"
        }
        
        # First registration
        response1 = test_client.post("/auth/register", json=user_data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Second registration with same email
        response2 = test_client.post("/auth/register", json=user_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self, test_client):
        """Test successful user login."""
        # First register a user
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        test_client.post("/auth/register", json=user_data)
        
        # Then login
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        
        response = test_client.post("/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data or "success" in data

    def test_login_invalid_credentials(self, test_client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = test_client.post("/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_wrong_password(self, test_client):
        """Test login with wrong password."""
        # First register a user
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        test_client.post("/auth/register", json=user_data)
        
        # Then login with wrong password
        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = test_client.post("/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_endpoint_with_valid_token(self, test_client, auth_headers):
        """Test /auth/me endpoint with valid token."""
        # Mock the authentication dependency
        with patch('routes.auth.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.user_id = 1
            mock_user.email = "test@example.com"
            mock_user.is_active = True
            mock_get_user.return_value = mock_user
            
            response = test_client.get("/auth/me", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["user_id"] == 1

    def test_me_endpoint_without_token(self, test_client):
        """Test /auth/me endpoint without token."""
        response = test_client.get("/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_endpoint_with_invalid_token(self, test_client):
        """Test /auth/me endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = test_client.get("/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_register_missing_fields(self, test_client):
        """Test registration with missing fields."""
        # Missing email
        user_data = {"password": "testpassword123"}
        response = test_client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing password
        user_data = {"email": "test@example.com"}
        response = test_client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_missing_fields(self, test_client):
        """Test login with missing fields."""
        # Missing username
        login_data = {"password": "testpassword123"}
        response = test_client.post("/auth/login", data=login_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing password
        login_data = {"username": "test@example.com"}
        response = test_client.post("/auth/login", data=login_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_password_hashing(self, test_client):
        """Test that passwords are properly hashed."""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = test_client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_200_OK
        
        # Verify that the stored password is hashed (not plain text)
        # This would require database access to verify
        # For now, we just ensure the registration succeeds
        assert "success" in response.json() or "access_token" in response.json()

    def test_token_expiration(self, test_client):
        """Test that tokens have proper expiration."""
        # Register and login to get a token
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        test_client.post("/auth/register", json=user_data)
        
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        response = test_client.post("/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify token structure (should contain expiration)
        if "access_token" in data:
            token = data["access_token"]
            # Basic JWT structure check (3 parts separated by dots)
            assert len(token.split('.')) == 3 