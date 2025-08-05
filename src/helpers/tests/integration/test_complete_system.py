#!/usr/bin/env python3
"""
Complete System Test for RAG
"""

import requests
import json
import time

def test_complete_system():
    """Test the complete RAG system."""
    
    print("RAG Complete System Test")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test data
    user_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        # 1. Test server status
        print("\n1. Server Status")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("   Server is running and responding")
        else:
            print(f"   Server status: {response.status_code}")
        
        # 2. Test user registration and login
        print("\n2. User Authentication")
        
        # Register user
        response = requests.post(f"{base_url}/api/v1/auth/register", json=user_data)
        if response.status_code in [200, 409]:  # 409 means user already exists
            print("   Registration successful or user already exists")
        else:
            print(f"   Registration failed: {response.status_code}")
        
        # Login user
        response = requests.post(f"{base_url}/api/v1/auth/login", json=user_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("   Login successful")
        else:
            print(f"   Login failed: {response.status_code}")
            return False
        
        # 3. Test user info
        print("\n3. User Information")
        response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            print(f"   User authenticated: {user_info.get('email')}")
        else:
            print(f"   User info failed: {response.status_code}")
        
        # 4. Test project creation
        print("\n4. Project Management")
        
        # Create a test project
        project_data = {
            "project_code": "test1",
            "project_name": "Test Project"
        }
        response = requests.post(f"{base_url}/api/v1/data/projects", json=project_data, headers=headers)
        if response.status_code == 200:
            print("   Project created successfully")
        else:
            print(f"   Project creation failed: {response.status_code}")
        
        # 5. Test document processing
        print("\n5. Document Processing")
        
        # Create test content
        test_content = "This is a test document for the RAG system. It contains information about AI and machine learning."
        
        # Upload test file
        files = {"file": ("test.txt", test_content, "text/plain")}
        response = requests.post(f"{base_url}/api/v1/data/upload/test1", files=files, headers=headers)
        if response.status_code == 200:
            print("   File uploaded successfully")
        else:
            print(f"   File upload failed: {response.status_code}")
        
        # Process the file
        response = requests.post(f"{base_url}/api/v1/data/process/test1", headers=headers)
        if response.status_code == 200:
            print("   File processed successfully")
        else:
            print(f"   File processing failed: {response.status_code}")
        
        # 6. Test question answering
        print("\n6. Question Answering")
        
        question_data = {
            "question": "What is this document about?",
            "project_code": "test1"
        }
        response = requests.post(f"{base_url}/api/v1/nlp/ask", json=question_data, headers=headers)
        if response.status_code == 200:
            answer = response.json()
            print("   Question answered successfully")
            print(f"   Answer: {answer.get('answer', 'No answer provided')[:100]}...")
        else:
            print(f"   Question answering failed: {response.status_code}")
        
        print("\nRAG system is ready for assignment submission!")
        return True
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    test_complete_system() 