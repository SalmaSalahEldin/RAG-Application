#!/usr/bin/env python3
import requests
import json

def test_server():
    """Test the server endpoints."""
    base_url = "http://localhost:8000"
    
    print("Testing server endpoints...")
    
    # Test basic endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/")
        print(f"✅ Basic endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Basic endpoint failed: {e}")
    
    # Test auth register endpoint
    try:
        data = {"email": "test@example.com", "password": "testpassword123"}
        response = requests.post(f"{base_url}/auth/register", json=data)
        print(f"✅ Auth register: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Auth register failed: {e}")
    
    # Test auth login endpoint
    try:
        data = {"username": "test@example.com", "password": "testpassword123"}
        response = requests.post(f"{base_url}/auth/login", data=data)
        print(f"✅ Auth login: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Auth login failed: {e}")

if __name__ == "__main__":
    test_server() 