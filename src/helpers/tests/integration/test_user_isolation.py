#!/usr/bin/env python3
"""
Test script to verify user isolation in RAG
"""

import requests
import json
import time

def test_user_isolation():
    """Test that users can only access their own projects."""
    
    print("Testing User Isolation in RAG")
    
    base_url = "http://localhost:8000"
    
    # Test data for two users
    user1_data = {
        "email": "user1@test.com",
        "password": "testpass123"
    }
    
    user2_data = {
        "email": "user2@test.com", 
        "password": "testpass123"
    }
    
    # Register and login user 1
    print(f"Registering {user1_data['email']}...")
    response = requests.post(f"{base_url}/api/v1/auth/register", json=user1_data)
    if response.status_code == 200:
        print(f"Registered {user1_data['email']}")
    elif response.status_code == 409:
        print(f"User {user1_data['email']} already exists")
    else:
        print(f"Failed to register {user1_data['email']}: {response.text}")
    
    # Login user 1
    response = requests.post(f"{base_url}/api/v1/auth/login", json=user1_data)
    if response.status_code == 200:
        user1_token = response.json()["access_token"]
        print(f"Logged in {user1_data['email']}")
    else:
        print(f"Failed to login {user1_data['email']}: {response.text}")
        return False
    
    # Register and login user 2
    print(f"Registering {user2_data['email']}...")
    response = requests.post(f"{base_url}/api/v1/auth/register", json=user2_data)
    if response.status_code == 200:
        print(f"Registered {user2_data['email']}")
    elif response.status_code == 409:
        print(f"User {user2_data['email']} already exists")
    else:
        print(f"Failed to register {user2_data['email']}: {response.text}")
    
    # Login user 2
    response = requests.post(f"{base_url}/api/v1/auth/login", json=user2_data)
    if response.status_code == 200:
        user2_token = response.json()["access_token"]
        print(f"Logged in {user2_data['email']}")
    else:
        print(f"Failed to login {user2_data['email']}: {response.text}")
        return False
    
    # Create projects for user 1
    headers1 = {"Authorization": f"Bearer {user1_token}"}
    
    print(f"Creating project 1 for {user1_data['email']}...")
    response = requests.post(f"{base_url}/api/v1/data/projects", 
                           json={"project_code": "1", "project_name": "User 1 Project 1"},
                           headers=headers1)
    if response.status_code == 200:
        print(f"Created project 1 for {user1_data['email']}")
    else:
        print(f"Failed to create project 1 for {user1_data['email']}: {response.text}")
    
    print(f"Creating project 2 for {user1_data['email']}...")
    response = requests.post(f"{base_url}/api/v1/data/projects",
                           json={"project_code": "2", "project_name": "User 1 Project 2"},
                           headers=headers1)
    if response.status_code == 200:
        print(f"Created project 2 for {user1_data['email']}")
    else:
        print(f"Failed to create project 2 for {user1_data['email']}: {response.text}")
    
    # Create projects for user 2
    headers2 = {"Authorization": f"Bearer {user2_token}"}
    
    print(f"Creating project 3 for {user2_data['email']}...")
    response = requests.post(f"{base_url}/api/v1/data/projects",
                           json={"project_code": "3", "project_name": "User 2 Project 1"},
                           headers=headers2)
    if response.status_code == 200:
        print(f"Created project 3 for {user2_data['email']}")
    else:
        print(f"Failed to create project 3 for {user2_data['email']}: {response.text}")
    
    # Test user 1 can only see their own projects
    print(f"Testing {user1_data['email']} project access...")
    response = requests.get(f"{base_url}/api/v1/data/projects", headers=headers1)
    if response.status_code == 200:
        user1_projects = response.json()
        user_project_ids = [p["project_code"] for p in user1_projects]
        expected_projects = ["1", "2"]
        
        if set(user_project_ids) == set(expected_projects):
            print(f"{user1_data['email']} can only see their own projects: {user_project_ids}")
        else:
            print(f"{user1_data['email']} can see projects {user_project_ids}, expected {expected_projects}")
            return False
    else:
        print(f"Failed to get projects for {user1_data['email']}: {response.text}")
        return False
    
    # Test user 2 can only see their own projects
    print(f"Testing {user2_data['email']} project access...")
    response = requests.get(f"{base_url}/api/v1/data/projects", headers=headers2)
    if response.status_code == 200:
        user2_projects = response.json()
        user_project_ids = [p["project_code"] for p in user2_projects]
        expected_projects = ["3"]
        
        if set(user_project_ids) == set(expected_projects):
            print(f"{user2_data['email']} can only see their own projects: {user_project_ids}")
        else:
            print(f"{user2_data['email']} can see projects {user_project_ids}, expected {expected_projects}")
            return False
    else:
        print(f"Failed to get projects for {user2_data['email']}: {response.text}")
        return False
    
    # Test user 1 cannot access user 2's project
    print(f"Testing {user1_data['email']} cannot access {user2_data['email']}'s project...")
    response = requests.get(f"{base_url}/api/v1/data/projects/3", headers=headers1)
    if response.status_code == 403:
        print(f"{user1_data['email']} cannot access {user2_data['email']}'s project (403 Forbidden)")
    else:
        print(f"{user1_data['email']} can access {user2_data['email']}'s project (got {response.status_code})")
        return False
    
    # Test user 2 cannot access user 1's project
    print(f"Testing {user2_data['email']} cannot access {user1_data['email']}'s project...")
    response = requests.get(f"{base_url}/api/v1/data/projects/1", headers=headers2)
    if response.status_code == 403:
        print(f"{user2_data['email']} cannot access {user1_data['email']}'s project (403 Forbidden)")
    else:
        print(f"{user2_data['email']} can access {user1_data['email']}'s project (got {response.status_code})")
        return False
    
    print("\nAll user isolation tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_user_isolation()
        if success:
            print("\nUser isolation is working correctly!")
        else:
            print("\nUser isolation has issues!")
    except Exception as e:
        print(f"\nTest failed with exception: {e}") 