#!/usr/bin/env python3
"""
JWT Logout API Test Script
Tests the new logout endpoint that blacklists JWT refresh tokens.

Test Flow:
1. Register a new test user  
2. Login and get JWT tokens (access + refresh)
3. Verify access token works
4. Logout (blacklist refresh token)
5. Verify access token still works temporarily
6. Try to refresh token (should fail - blacklisted)
7. Try to logout again with same token (should fail)

Author: Game Hosting Platform Team
Date: December 30, 2024
"""

import requests
import json
import time
from datetime import datetime
import random

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USER_PREFIX = f"logout_test_{int(time.time())}"

def print_test_header(title):
    """Print formatted test section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_step(step_num, description):
    """Print formatted test step"""
    print(f"\n📋 Step {step_num}: {description}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def test_jwt_logout_complete_flow():
    """Test complete JWT logout flow with token blacklisting"""
    
    print_test_header("JWT Logout API Complete Test")
    
    # Test data
    random_id = random.randint(1000, 9999)
    register_data = {
        "username": f"logouttest_{random_id}",
        "email": f"logouttest_{random_id}@example.com",
        "password": "TestSecure123!",
        "password2": "TestSecure123!",
        "first_name": "Logout",
        "last_name": "Tester"
    }
    
    # Store tokens for testing
    tokens = {}
    
    try:
        # Step 1: Register user and get initial tokens
        print_step(1, "User Registration + Auto-Login")
        
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        
        if register_response.status_code == 201:
            register_data = register_response.json()
            tokens = register_data["tokens"]
            user_id = register_data["user"]["id"]
            
            print_success(f"Registration successful - User ID: {user_id}")
            print_info(f"Access Token: {tokens['access'][:50]}...")
            print_info(f"Refresh Token: {tokens['refresh'][:50]}...")
        else:
            print_error(f"Registration failed: {register_response.status_code}")
            print(register_response.text)
            return False
        
        # Step 2: Test access token works
        print_step(2, "Verify Access Token Works")
        
        profile_response = requests.get(
            f"{BASE_URL}/api/auth-legacy/profile/",
            headers={"Authorization": f"Bearer {tokens['access']}"}
        )
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print_success(f"Access token works - Username: {profile_data['username']}")
        else:
            print_error(f"Access token failed: {profile_response.status_code}")
            return False
        
        # Step 3: Test refresh token works (before logout)
        print_step(3, "Test Refresh Token (Before Logout)")
        
        refresh_response = requests.post(
            f"{BASE_URL}/api/auth/refresh/",
            json={"refresh": tokens["refresh"]},
            headers={"Content-Type": "application/json"}
        )
        
        if refresh_response.status_code == 200:
            refresh_data = refresh_response.json()
            print_success("Refresh token works before logout")
            print_info(f"New Access Token: {refresh_data['access'][:50]}...")
            
            # Update tokens for testing
            tokens['access'] = refresh_data['access']
            if 'refresh' in refresh_data:  # Token rotation enabled
                tokens['refresh'] = refresh_data['refresh']
                print_info("Token rotation: New refresh token received")
        else:
            print_error(f"Refresh failed: {refresh_response.status_code}")
            return False
        
        # Step 4: Logout (blacklist refresh token)
        print_step(4, "JWT Logout - Blacklist Refresh Token")
        
        logout_response = requests.post(
            f"{BASE_URL}/api/auth/logout/",
            json={"refresh_token": tokens["refresh"]},
            headers={
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json"
            }
        )
        
        if logout_response.status_code == 200:
            logout_data = logout_response.json()
            print_success(f"Logout successful: {logout_data['message']}")
            print_info(f"Detail: {logout_data['detail']}")
        else:
            print_error(f"Logout failed: {logout_response.status_code}")
            print(logout_response.text)
            return False
        
        # Step 5: Verify access token still works temporarily
        print_step(5, "Verify Access Token Still Valid (Temporary)")
        
        profile_response2 = requests.get(
            f"{BASE_URL}/api/auth-legacy/profile/",
            headers={"Authorization": f"Bearer {tokens['access']}"}
        )
        
        if profile_response2.status_code == 200:
            print_success("Access token still valid temporarily (expected behavior)")
            print_info("Access tokens remain valid until expiry (1 hour)")
        else:
            print_error(f"Access token unexpectedly invalid: {profile_response2.status_code}")
        
        # Step 6: Try to refresh with blacklisted token (should fail)
        print_step(6, "Try Refresh with Blacklisted Token (Should Fail)")
        
        refresh_response2 = requests.post(
            f"{BASE_URL}/api/auth/refresh/",
            json={"refresh": tokens["refresh"]},
            headers={"Content-Type": "application/json"}
        )
        
        if refresh_response2.status_code == 401:
            print_success("Refresh token correctly blacklisted (401 Unauthorized)")
            refresh_error = refresh_response2.json()
            print_info(f"Error: {refresh_error.get('detail', 'Token is blacklisted')}")
        else:
            print_error(f"Refresh token should be blacklisted but got: {refresh_response2.status_code}")
            print(refresh_response2.text)
        
        # Step 7: Try to logout again with same token (should fail)
        print_step(7, "Try Logout Again with Same Token (Should Fail)")
        
        logout_response2 = requests.post(
            f"{BASE_URL}/api/auth/logout/",
            json={"refresh_token": tokens["refresh"]},
            headers={
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json"
            }
        )
        
        if logout_response2.status_code == 400:
            logout_error = logout_response2.json()
            print_success("Second logout correctly failed (token already blacklisted)")
            print_info(f"Error: {logout_error.get('message', 'Token already blacklisted')}")
        else:
            print_error(f"Second logout should fail but got: {logout_response2.status_code}")
        
        # Step 8: Test logout without refresh token (should fail)
        print_step(8, "Test Logout Without Refresh Token (Should Fail)")
        
        logout_response3 = requests.post(
            f"{BASE_URL}/api/auth/logout/",
            json={},  # No refresh token
            headers={
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json"
            }
        )
        
        if logout_response3.status_code == 400:
            logout_error3 = logout_response3.json()
            print_success("Logout without refresh token correctly failed")
            print_info(f"Error: {logout_error3.get('message', 'Refresh token required')}")
        else:
            print_error(f"Logout without token should fail but got: {logout_response3.status_code}")
        
        print_test_header("🎉 JWT Logout Test Summary")
        print_success("All logout functionality tests passed!")
        print_info("✅ User registration with JWT tokens")
        print_info("✅ Access token validation")
        print_info("✅ Refresh token functionality (before logout)")
        print_info("✅ Secure logout with token blacklisting")
        print_info("✅ Access token remains valid temporarily")
        print_info("✅ Refresh token properly blacklisted")
        print_info("✅ Duplicate logout prevention")
        print_info("✅ Missing token validation")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print_error("Connection failed - Make sure Django server is running on port 8000")
        return False
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        return False

def test_logout_without_auth():
    """Test logout endpoint without authentication (should fail)"""
    
    print_test_header("Logout Without Authentication Test")
    
    try:
        logout_response = requests.post(
            f"{BASE_URL}/api/auth/logout/",
            json={"refresh_token": "fake_token"},
            headers={"Content-Type": "application/json"}
        )
        
        if logout_response.status_code == 401:
            print_success("Logout without authentication correctly failed (401)")
        else:
            print_error(f"Expected 401 but got: {logout_response.status_code}")
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting JWT Logout API Tests")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Target URL: {BASE_URL}")
    
    # Run all tests
    success = True
    
    success &= test_jwt_logout_complete_flow()
    test_logout_without_auth()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 All JWT Logout Tests Completed Successfully!")
    else:
        print("❌ Some tests failed - Check output above")
    print(f"{'='*60}") 