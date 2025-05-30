#!/usr/bin/env python3
"""
JWT Authentication Test Script
GameHost Platform - Modern JWT Authentication Testing

Bu script JWT authentication sisteminin çalışmasını test eder.
"""

import requests
import json
from datetime import datetime

# API Base URL
BASE_URL = "http://127.0.0.1:8000"

def test_jwt_authentication():
    """Test JWT authentication flow"""
    
    print("🔐 JWT AUTHENTICATION TEST")
    print("=" * 50)
    
    # Test credentials (you should have a user in database)
    credentials = {
        "username": "testuser",  # Replace with your username
        "password": "testpass123"  # Replace with your password
    }
    
    print(f"📋 Testing with user: {credentials['username']}")
    print()
    
    # ==========================================================================
    # 1. LOGIN - Get JWT Tokens
    # ==========================================================================
    print("1️⃣ LOGIN - Getting JWT tokens...")
    
    login_url = f"{BASE_URL}/api/auth/login/"
    
    try:
        response = requests.post(login_url, data=credentials)
        
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens['access']
            refresh_token = tokens['refresh']
            
            print("✅ LOGIN SUCCESSFUL!")
            print(f"🔑 Access Token (first 50 chars): {access_token[:50]}...")
            print(f"🔄 Refresh Token (first 50 chars): {refresh_token[:50]}...")
            print()
            
        else:
            print(f"❌ LOGIN FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            return
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Make sure Django server is running on port 8000")
        return
    
    # ==========================================================================
    # 2. AUTHENTICATED REQUEST - Using Access Token
    # ==========================================================================
    print("2️⃣ AUTHENTICATED REQUEST - Testing protected endpoint...")
    
    # Test with game creation endpoint
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Try accessing user profile (protected endpoint)
    profile_url = f"{BASE_URL}/api/auth-legacy/profile/"  # Legacy endpoint for testing
    
    try:
        response = requests.get(profile_url, headers=headers)
        
        if response.status_code == 200:
            print("✅ AUTHENTICATED REQUEST SUCCESSFUL!")
            print(f"👤 User data: {response.json()}")
            print()
        else:
            print(f"⚠️ AUTHENTICATED REQUEST RESPONSE: {response.status_code}")
            print(f"Response: {response.text}")
            print()
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
    
    # ==========================================================================
    # 3. TOKEN VERIFICATION
    # ==========================================================================
    print("3️⃣ TOKEN VERIFICATION - Verifying access token...")
    
    verify_url = f"{BASE_URL}/api/auth/verify/"
    verify_data = {"token": access_token}
    
    try:
        response = requests.post(verify_url, data=verify_data)
        
        if response.status_code == 200:
            print("✅ TOKEN VERIFICATION SUCCESSFUL!")
            print("🔐 Access token is valid")
            print()
        else:
            print(f"❌ TOKEN VERIFICATION FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            print()
            
    except requests.exceptions.RequestException as e:
        print(f"❌ VERIFICATION ERROR: {e}")
    
    # ==========================================================================
    # 4. TOKEN REFRESH
    # ==========================================================================
    print("4️⃣ TOKEN REFRESH - Getting new access token...")
    
    refresh_url = f"{BASE_URL}/api/auth/refresh/"
    refresh_data = {"refresh": refresh_token}
    
    try:
        response = requests.post(refresh_url, data=refresh_data)
        
        if response.status_code == 200:
            new_tokens = response.json()
            new_access_token = new_tokens['access']
            
            print("✅ TOKEN REFRESH SUCCESSFUL!")
            print(f"🔑 New Access Token (first 50 chars): {new_access_token[:50]}...")
            
            # Check if refresh token was rotated
            if 'refresh' in new_tokens:
                new_refresh_token = new_tokens['refresh']
                print(f"🔄 New Refresh Token (rotated): {new_refresh_token[:50]}...")
            
            print()
            
        else:
            print(f"❌ TOKEN REFRESH FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            print()
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REFRESH ERROR: {e}")
    
    # ==========================================================================
    # 5. RATE LIMITING TEST
    # ==========================================================================
    print("5️⃣ RATE LIMITING TEST - Testing protected endpoints...")
    
    games_url = f"{BASE_URL}/api/games/games/"
    
    for i in range(3):
        try:
            response = requests.get(games_url, headers=headers)
            print(f"Request {i+1}: {response.status_code} - Rate limit headers:")
            
            # Check rate limit headers
            for header_name in response.headers:
                if 'ratelimit' in header_name.lower() or 'x-rate' in header_name.lower():
                    print(f"  {header_name}: {response.headers[header_name]}")
                    
        except requests.exceptions.RequestException as e:
            print(f"Request {i+1} ERROR: {e}")
    
    print()
    print("🎉 JWT AUTHENTICATION TEST COMPLETED!")
    print("=" * 50)

if __name__ == "__main__":
    test_jwt_authentication() 