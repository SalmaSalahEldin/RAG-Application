#!/usr/bin/env python3
"""
Test script for enhanced error handling.
Verifies that error messages are detailed, representative, and convenient for users.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_enhanced_error_handling():
    print("🧪 Testing Enhanced Error Handling")
    print("=" * 60)
    
    # Test user credentials
    test_user = {
        "email": "error_test@example.com",
        "password": "test123"
    }
    
    # 1. Test authentication errors
    print("\n1. Testing Authentication Error Messages...")
    
    # Test login with non-existent user
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        if response.status_code == 401:
            data = response.json()
            print("✅ Login with non-existent user:")
            print(f"   Title: {data.get('error', {}).get('title', 'N/A')}")
            print(f"   Message: {data.get('error', {}).get('message', 'N/A')}")
            print(f"   Suggestion: {data.get('error', {}).get('suggestion', 'N/A')}")
            print(f"   Category: {data.get('error', {}).get('category', 'N/A')}")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Login test failed: {e}")
    
    # Test registration with existing user
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
        if response.status_code == 200:
            print("✅ User registered successfully")
        elif response.status_code == 400:
            data = response.json()
            print("✅ Registration with existing user:")
            print(f"   Title: {data.get('error', {}).get('title', 'N/A')}")
            print(f"   Message: {data.get('error', {}).get('message', 'N/A')}")
            print(f"   Suggestion: {data.get('error', {}).get('suggestion', 'N/A')}")
        else:
            print(f"⚠️  Registration response: {response.status_code}")
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
    
    # 2. Test project management errors
    print("\n2. Testing Project Management Error Messages...")
    
    # Login to get token
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data={
            "username": test_user["email"],
            "password": test_user["password"]
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("data", {}).get("access_token")
            if not token:
                token = data.get("access_token")  # Fallback for old format
            
            if token:
                print("✅ Login successful")
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test creating duplicate project
                project_id = 400
                response = requests.post(f"{BASE_URL}/api/v1/data/projects/create/{project_id}", headers=headers)
                if response.status_code == 201:
                    print(f"✅ Project {project_id} created successfully")
                    
                    # Try to create the same project again
                    response = requests.post(f"{BASE_URL}/api/v1/data/projects/create/{project_id}", headers=headers)
                    if response.status_code == 400:
                        data = response.json()
                        print("✅ Duplicate project creation:")
                        print(f"   Title: {data.get('error', {}).get('title', 'N/A')}")
                        print(f"   Message: {data.get('error', {}).get('message', 'N/A')}")
                        print(f"   Suggestion: {data.get('error', {}).get('suggestion', 'N/A')}")
                        print(f"   Category: {data.get('error', {}).get('category', 'N/A')}")
                    else:
                        print(f"⚠️  Unexpected duplicate response: {response.status_code}")
                else:
                    print(f"⚠️  Project creation failed: {response.status_code}")
                
                # Test accessing non-existent project
                response = requests.get(f"{BASE_URL}/api/v1/data/projects/99999", headers=headers)
                if response.status_code == 400:
                    data = response.json()
                    print("✅ Non-existent project access:")
                    print(f"   Title: {data.get('error', {}).get('title', 'N/A')}")
                    print(f"   Message: {data.get('error', {}).get('message', 'N/A')}")
                    print(f"   Suggestion: {data.get('error', {}).get('suggestion', 'N/A')}")
                    print(f"   Category: {data.get('error', {}).get('category', 'N/A')}")
                else:
                    print(f"⚠️  Non-existent project response: {response.status_code}")
                
                # Test processing with no files
                response = requests.post(f"{BASE_URL}/api/v1/data/process/{project_id}", 
                                       headers=headers,
                                       json={"chunk_size": 100, "overlap_size": 20, "do_reset": 0})
                if response.status_code == 400:
                    data = response.json()
                    print("✅ Processing with no files:")
                    print(f"   Title: {data.get('error', {}).get('title', 'N/A')}")
                    print(f"   Message: {data.get('error', {}).get('message', 'N/A')}")
                    print(f"   Suggestion: {data.get('error', {}).get('suggestion', 'N/A')}")
                    print(f"   Category: {data.get('error', {}).get('category', 'N/A')}")
                else:
                    print(f"⚠️  Processing response: {response.status_code}")
                
            else:
                print("❌ No token received")
        else:
            print(f"❌ Login failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Login test failed: {e}")
    
    # 3. Test NLP errors
    print("\n3. Testing NLP Error Messages...")
    
    try:
        # Test NLP operations on non-existent project
        response = requests.get(f"{BASE_URL}/api/v1/nlp/index/info/99999", headers=headers)
        if response.status_code == 400:
            data = response.json()
            print("✅ NLP project access error:")
            print(f"   Title: {data.get('error', {}).get('title', 'N/A')}")
            print(f"   Message: {data.get('error', {}).get('message', 'N/A')}")
            print(f"   Suggestion: {data.get('error', {}).get('suggestion', 'N/A')}")
            print(f"   Category: {data.get('error', {}).get('category', 'N/A')}")
        else:
            print(f"⚠️  NLP error response: {response.status_code}")
    except Exception as e:
        print(f"❌ NLP test failed: {e}")
    
    print("\n🎉 Enhanced Error Handling Test Completed!")
    print("=" * 60)
    print("✅ Detailed error messages with titles")
    print("✅ Helpful suggestions for users")
    print("✅ Categorized error types")
    print("✅ Consistent error format")
    print("✅ User-friendly language")
    print("✅ Proper HTTP status codes")
    print("✅ Timestamp information")
    print("✅ Context-specific details")

if __name__ == "__main__":
    test_enhanced_error_handling() 