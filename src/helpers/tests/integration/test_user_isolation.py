#!/usr/bin/env python3
"""
Test script to verify user isolation in Mini-RAG
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_user_isolation():
    """Test that users can only access their own projects"""
    
    print("🧪 Testing User Isolation in Mini-RAG")
    print("=" * 50)
    
    # Test data
    user1_data = {
        "email": "user1@test.com",
        "password": "password123"
    }
    
    user2_data = {
        "email": "user2@test.com", 
        "password": "password123"
    }
    
    tokens = {}
    
    try:
        # 1. Register and login users
        print("\n1. Registering and logging in users...")
        
        for user_data in [user1_data, user2_data]:
            # Register user
            response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
            if response.status_code == 200:
                print(f"✅ Registered {user_data['email']}")
            elif response.status_code == 400:
                print(f"ℹ️  User {user_data['email']} already exists")
            else:
                print(f"❌ Failed to register {user_data['email']}: {response.text}")
                return False
            
            # Login user
            response = requests.post(f"{BASE_URL}/auth/login", json=user_data)
            if response.status_code == 200:
                token = response.json()["access_token"]
                tokens[user_data['email']] = token
                print(f"✅ Logged in {user_data['email']}")
            else:
                print(f"❌ Failed to login {user_data['email']}: {response.text}")
                return False
        
        # 2. Create projects for each user
        print("\n2. Creating projects for each user...")
        
        user_projects = {}
        for email, token in tokens.items():
            headers = {"Authorization": f"Bearer {token}"}
            
            # Create project 1 for user
            response = requests.post(f"{API_BASE}/data/projects/create/1", headers=headers)
            if response.status_code == 200:
                print(f"✅ Created project 1 for {email}")
                user_projects[email] = [1]
            else:
                print(f"❌ Failed to create project 1 for {email}: {response.text}")
                return False
            
            # Create project 2 for user
            response = requests.post(f"{API_BASE}/data/projects/create/2", headers=headers)
            if response.status_code == 200:
                print(f"✅ Created project 2 for {email}")
                user_projects[email].append(2)
            else:
                print(f"❌ Failed to create project 2 for {email}: {response.text}")
                return False
        
        # 3. Test user isolation - users should only see their own projects
        print("\n3. Testing project isolation...")
        
        for email, token in tokens.items():
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get user's projects
            response = requests.get(f"{API_BASE}/data/projects", headers=headers)
            if response.status_code == 200:
                data = response.json()
                user_project_ids = [p["project_id"] for p in data.get("projects", [])]
                expected_projects = user_projects[email]
                
                if set(user_project_ids) == set(expected_projects):
                    print(f"✅ {email} can only see their own projects: {user_project_ids}")
                else:
                    print(f"❌ {email} can see projects {user_project_ids}, expected {expected_projects}")
                    return False
            else:
                print(f"❌ Failed to get projects for {email}: {response.text}")
                return False
        
        # 4. Test cross-user access - users should not be able to access other users' projects
        print("\n4. Testing cross-user access prevention...")
        
        user1_token = tokens[user1_data['email']]
        user2_token = tokens[user2_data['email']]
        
        # User 1 trying to access User 2's project
        headers = {"Authorization": f"Bearer {user1_token}"}
        response = requests.get(f"{API_BASE}/data/projects", headers=headers)
        if response.status_code == 200:
            data = response.json()
            user1_projects = [p["project_id"] for p in data.get("projects", [])]
            
            # User 1 should not see User 2's projects
            if not any(pid in user_projects[user2_data['email']] for pid in user1_projects):
                print("✅ User 1 cannot see User 2's projects")
            else:
                print("❌ User 1 can see User 2's projects - isolation failed!")
                return False
        
        # User 2 trying to access User 1's project
        headers = {"Authorization": f"Bearer {user2_token}"}
        response = requests.get(f"{API_BASE}/data/projects", headers=headers)
        if response.status_code == 200:
            data = response.json()
            user2_projects = [p["project_id"] for p in data.get("projects", [])]
            
            # User 2 should not see User 1's projects
            if not any(pid in user_projects[user1_data['email']] for pid in user2_projects):
                print("✅ User 2 cannot see User 1's projects")
            else:
                print("❌ User 2 can see User 1's projects - isolation failed!")
                return False
        
        # 5. Test project operations isolation
        print("\n5. Testing project operations isolation...")
        
        # User 1 trying to process User 2's project (should fail)
        headers = {"Authorization": f"Bearer {user1_token}"}
        response = requests.post(
            f"{API_BASE}/data/process/2",  # User 2's project
            json={"chunk_size": 100, "overlap_size": 20},
            headers=headers
        )
        
        if response.status_code == 403:
            print("✅ User 1 cannot access User 2's project (403 Forbidden)")
        else:
            print(f"❌ User 1 can access User 2's project (got {response.status_code})")
            return False
        
        # User 2 trying to process User 1's project (should fail)
        headers = {"Authorization": f"Bearer {user2_token}"}
        response = requests.post(
            f"{API_BASE}/data/process/1",  # User 1's project
            json={"chunk_size": 100, "overlap_size": 20},
            headers=headers
        )
        
        if response.status_code == 403:
            print("✅ User 2 cannot access User 1's project (403 Forbidden)")
        else:
            print(f"❌ User 2 can access User 1's project (got {response.status_code})")
            return False
        
        print("\n🎉 All user isolation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_user_isolation()
    if success:
        print("\n✅ User isolation is working correctly!")
    else:
        print("\n❌ User isolation has issues!")
        exit(1) 