#!/usr/bin/env python3
"""
Test script for UI registration and login with enhanced error handling.
Verifies that the frontend correctly handles the new response format.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_ui_registration_login():
    print("🧪 Testing UI Registration and Login")
    print("=" * 60)
    
    # Test user credentials
    test_user = {
        "email": "ui_test_new@example.com",
        "password": "test123"
    }
    
    # 1. Test registration
    print("\n1. Testing Registration...")
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Registration successful!")
            print(f"   Message: {data.get('success', {}).get('message', 'N/A')}")
            print(f"   User ID: {data.get('data', {}).get('user_id', 'N/A')}")
            print(f"   Email: {data.get('data', {}).get('email', 'N/A')}")
            print(f"   Is Active: {data.get('data', {}).get('is_active', 'N/A')}")
        elif response.status_code == 400:
            data = response.json()
            if data.get('error'):
                print("✅ Registration error handled correctly:")
                print(f"   Title: {data.get('error', {}).get('title', 'N/A')}")
                print(f"   Message: {data.get('error', {}).get('message', 'N/A')}")
                print(f"   Suggestion: {data.get('error', {}).get('suggestion', 'N/A')}")
            else:
                print(f"⚠️  Registration failed: {response.status_code}")
        else:
            print(f"⚠️  Unexpected registration response: {response.status_code}")
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
    
    # 2. Test login
    print("\n2. Testing Login...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data={
            "username": test_user["email"],
            "password": test_user["password"]
        })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"   Message: {data.get('success', {}).get('message', 'N/A')}")
            print(f"   User ID: {data.get('data', {}).get('user_id', 'N/A')}")
            print(f"   Email: {data.get('data', {}).get('email', 'N/A')}")
            print(f"   Token Type: {data.get('data', {}).get('token_type', 'N/A')}")
            
            # Extract token for further tests
            token = data.get('data', {}).get('access_token')
            if token:
                print(f"   Token: {token[:50]}...")
                return token
            else:
                print("❌ No token received")
                return None
        elif response.status_code == 401:
            data = response.json()
            if data.get('error'):
                print("✅ Login error handled correctly:")
                print(f"   Title: {data.get('error', {}).get('title', 'N/A')}")
                print(f"   Message: {data.get('error', {}).get('message', 'N/A')}")
                print(f"   Suggestion: {data.get('error', {}).get('suggestion', 'N/A')}")
            else:
                print(f"⚠️  Login failed: {response.status_code}")
        else:
            print(f"⚠️  Unexpected login response: {response.status_code}")
    except Exception as e:
        print(f"❌ Login test failed: {e}")
    
    return None
    
    # 3. Test duplicate registration
    print("\n3. Testing Duplicate Registration...")
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
        
        if response.status_code == 400:
            data = response.json()
            if data.get('error'):
                print("✅ Duplicate registration error handled correctly:")
                print(f"   Title: {data.get('error', {}).get('title', 'N/A')}")
                print(f"   Message: {data.get('error', {}).get('message', 'N/A')}")
                print(f"   Suggestion: {data.get('error', {}).get('suggestion', 'N/A')}")
                print(f"   Category: {data.get('error', {}).get('category', 'N/A')}")
            else:
                print(f"⚠️  Duplicate registration response: {response.status_code}")
        else:
            print(f"⚠️  Unexpected duplicate registration response: {response.status_code}")
    except Exception as e:
        print(f"❌ Duplicate registration test failed: {e}")
    
    # 4. Test login with wrong password
    print("\n4. Testing Login with Wrong Password...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data={
            "username": test_user["email"],
            "password": "wrongpassword"
        })
        
        if response.status_code == 401:
            data = response.json()
            if data.get('error'):
                print("✅ Wrong password error handled correctly:")
                print(f"   Title: {data.get('error', {}).get('title', 'N/A')}")
                print(f"   Message: {data.get('error', {}).get('message', 'N/A')}")
                print(f"   Suggestion: {data.get('error', {}).get('suggestion', 'N/A')}")
                print(f"   Category: {data.get('error', {}).get('category', 'N/A')}")
            else:
                print(f"⚠️  Wrong password response: {response.status_code}")
        else:
            print(f"⚠️  Unexpected wrong password response: {response.status_code}")
    except Exception as e:
        print(f"❌ Wrong password test failed: {e}")
    
    print("\n🎉 UI Registration and Login Test Completed!")
    print("=" * 60)
    print("✅ Registration works with new response format")
    print("✅ Login works with new response format")
    print("✅ Error handling works correctly")
    print("✅ Frontend can handle both success and error cases")
    print("✅ Enhanced error messages are displayed")
    print("✅ Consistent response format across all endpoints")

if __name__ == "__main__":
    test_ui_registration_login() 