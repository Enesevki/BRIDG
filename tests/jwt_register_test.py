#!/usr/bin/env python3
"""
JWT Registration Test Script
GameHost Platform - JWT Registration Testing

Bu script JWT registration endpoint'ini test eder.
"""

import requests
import json
from datetime import datetime
import random

# API Base URL
BASE_URL = "http://127.0.0.1:8000"

def test_jwt_registration():
    """Test JWT registration endpoint"""
    
    print("🔐 JWT REGISTRATION TEST")
    print("=" * 50)
    
    # Test registration data with unique email
    random_id = random.randint(1000, 9999)
    register_data = {
        "username": f"testuserJWT_{random_id}",
        "email": f"test_{random_id}@example.com",
        "password": "testpass123",
        "password2": "testpass123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    print(f"📋 Testing registration for user: {register_data['username']}")
    print(f"👤 Name: {register_data['first_name']} {register_data['last_name']}")
    print()
    
    # ==========================================================================
    # 1. REGISTER - Get JWT Tokens directly
    # ==========================================================================
    print("1️⃣ REGISTER - Getting JWT tokens directly...")
    
    register_url = f"{BASE_URL}/api/auth/register/"
    
    try:
        response = requests.post(
            register_url, 
            json=register_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            result = response.json()
            user_data = result['user']
            tokens = result['tokens']
            message = result['message']
            
            print("✅ REGISTRATION SUCCESSFUL!")
            print(f"👤 User: {user_data}")
            print(f"💬 Message: {message}")
            print(f"🔑 Access Token (first 50 chars): {tokens['access'][:50]}...")
            print(f"🔄 Refresh Token (first 50 chars): {tokens['refresh'][:50]}...")
            print()
            
            # Test authenticated request with new token
            test_authenticated_request(tokens['access'])
            
        else:
            print(f"❌ REGISTRATION FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            return
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Make sure Django server is running on port 8000")
        return
    except json.JSONDecodeError:
        print(f"❌ JSON DECODE ERROR: {response.text}")
        return

def test_authenticated_request(access_token):
    """Test using the JWT token for authenticated requests"""
    
    print("2️⃣ AUTHENTICATED REQUEST TEST...")
    
    # Test with authenticated endpoint
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Try accessing user profile
    profile_url = f"{BASE_URL}/api/auth-legacy/profile/"
    
    try:
        response = requests.get(profile_url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ AUTHENTICATED REQUEST SUCCESSFUL!")
            print(f"👤 User Profile: {user_data}")
            print()
        else:
            print(f"⚠️ AUTHENTICATED REQUEST FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            print()
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")

def test_duplicate_registration():
    """Test duplicate username registration"""
    
    print("3️⃣ DUPLICATE REGISTRATION TEST...")
    
    register_data = {
        "username": "testuserJWT_duplicate",  # Fixed username for duplicate test
        "email": "duplicate@example.com",
        "password": "testpass123",
        "password2": "testpass123",
        "first_name": "Duplicate",
        "last_name": "Test"
    }
    
    register_url = f"{BASE_URL}/api/auth/register/"
    
    # First registration attempt
    try:
        response1 = requests.post(
            register_url, 
            json=register_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"First registration: {response1.status_code}")
        
        # Second registration attempt with same username but different email
        register_data["email"] = "different@example.com"
        response2 = requests.post(
            register_url, 
            json=register_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response2.status_code == 400:
            print("✅ DUPLICATE USERNAME CORRECTLY REJECTED!")
            print(f"Error: {response2.text}")
        else:
            print(f"⚠️ UNEXPECTED RESPONSE: {response2.status_code}")
            print(f"Response: {response2.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
    
    print()

if __name__ == "__main__":
    test_jwt_registration()
    test_duplicate_registration()
    
    print("🎉 JWT REGISTRATION TEST COMPLETED!")
    print("=" * 50) 