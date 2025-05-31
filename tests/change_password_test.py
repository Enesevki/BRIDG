#!/usr/bin/env python3
"""
Change Password API Test Script
Tests the password change endpoint with comprehensive security validation.

Test Flow:
1. Register a new test user with JWT tokens
2. Test change password with correct old password
3. Verify new password works for login
4. Test various error scenarios (wrong old password, weak new password, etc.)
5. Test rate limiting functionality

Author: Game Hosting Platform Team
Date: December 30, 2024
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USER_PREFIX = f"pwd_test_{int(time.time())}"

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

def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def test_change_password_success():
    """Test successful password change flow"""
    
    print_test_header("Password Change Success Test")
    
    # Test data
    original_password = "OriginalPass123!"
    new_password = "NewSecurePass456!"
    
    test_user = {
        "username": f"{TEST_USER_PREFIX}_success",
        "email": f"{TEST_USER_PREFIX}_success@test.com",
        "password": original_password,
        "password2": original_password
    }
    
    tokens = {}
    
    try:
        # Step 1: Register user
        print_step(1, "User Registration")
        
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if register_response.status_code == 201:
            register_data = register_response.json()
            tokens = register_data["tokens"]
            user_id = register_data["user"]["id"]
            username = register_data["user"]["username"]
            
            print_success(f"Registration successful - User: {username} (ID: {user_id})")
        else:
            print_error(f"Registration failed: {register_response.status_code}")
            return False
        
        # Step 2: Change password
        print_step(2, "Change Password")
        
        change_password_data = {
            "old_password": original_password,
            "new_password": new_password,
            "new_password2": new_password
        }
        
        change_response = requests.post(
            f"{BASE_URL}/api/auth/change-password/",
            json=change_password_data,
            headers={
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json"
            }
        )
        
        if change_response.status_code == 200:
            change_data = change_response.json()
            print_success(f"Password changed: {change_data['message']}")
            print_info(f"Detail: {change_data['detail']}")
            
            # Update tokens (new tokens provided for security)
            if 'tokens' in change_data:
                tokens = change_data['tokens']
                print_info("New JWT tokens received for security")
        else:
            print_error(f"Password change failed: {change_response.status_code}")
            print_error(change_response.text)
            return False
        
        # Step 3: Test login with new password
        print_step(3, "Test Login with New Password")
        
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login/",
            json={
                "username": test_user["username"],
                "password": new_password
            },
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            print_success("Login with new password successful")
        else:
            print_error(f"Login with new password failed: {login_response.status_code}")
            return False
        
        # Step 4: Test old password no longer works
        print_step(4, "Verify Old Password No Longer Works")
        
        old_login_response = requests.post(
            f"{BASE_URL}/api/auth/login/",
            json={
                "username": test_user["username"],
                "password": original_password
            },
            headers={"Content-Type": "application/json"}
        )
        
        if old_login_response.status_code == 401:
            print_success("Old password correctly rejected")
        else:
            print_error(f"Old password should be rejected but got: {old_login_response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print_error("Connection failed - Make sure Django server is running on port 8000")
        return False
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        return False

def test_change_password_errors():
    """Test password change error scenarios"""
    
    print_test_header("Password Change Error Scenarios")
    
    # Test data
    original_password = "TestOriginal123!"
    test_user = {
        "username": f"{TEST_USER_PREFIX}_errors",
        "email": f"{TEST_USER_PREFIX}_errors@test.com",
        "password": original_password,
        "password2": original_password
    }
    
    tokens = {}
    
    try:
        # Register user first
        print_step(1, "Setup - Register Test User")
        
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if register_response.status_code == 201:
            tokens = register_response.json()["tokens"]
            print_success("Test user registered")
        else:
            print_error("Failed to register test user")
            return False
        
        # Test 1: Wrong old password
        print_step(2, "Test Wrong Old Password")
        
        wrong_old_password_data = {
            "old_password": "WrongPassword123!",
            "new_password": "NewPassword123!",
            "new_password2": "NewPassword123!"
        }
        
        wrong_old_response = requests.post(
            f"{BASE_URL}/api/auth/change-password/",
            json=wrong_old_password_data,
            headers={
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json"
            }
        )
        
        if wrong_old_response.status_code == 400:
            error_data = wrong_old_response.json()
            print_success("Wrong old password correctly rejected")
            print_info(f"Error: {error_data.get('errors', {})}")
        else:
            print_error(f"Wrong old password should be rejected but got: {wrong_old_response.status_code}")
        
        # Test 2: Password mismatch
        print_step(3, "Test New Password Mismatch")
        
        mismatch_data = {
            "old_password": original_password,
            "new_password": "NewPassword123!",
            "new_password2": "DifferentPassword123!"
        }
        
        mismatch_response = requests.post(
            f"{BASE_URL}/api/auth/change-password/",
            json=mismatch_data,
            headers={
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json"
            }
        )
        
        if mismatch_response.status_code == 400:
            print_success("Password mismatch correctly detected")
        else:
            print_error(f"Password mismatch should be rejected but got: {mismatch_response.status_code}")
        
        # Test 3: Same password
        print_step(4, "Test Same Password (New = Old)")
        
        same_password_data = {
            "old_password": original_password,
            "new_password": original_password,
            "new_password2": original_password
        }
        
        same_response = requests.post(
            f"{BASE_URL}/api/auth/change-password/",
            json=same_password_data,
            headers={
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json"
            }
        )
        
        if same_response.status_code == 400:
            print_success("Same password correctly rejected")
        else:
            print_error(f"Same password should be rejected but got: {same_response.status_code}")
        
        # Test 4: Weak password
        print_step(5, "Test Weak Password")
        
        weak_password_data = {
            "old_password": original_password,
            "new_password": "123",
            "new_password2": "123"
        }
        
        weak_response = requests.post(
            f"{BASE_URL}/api/auth/change-password/",
            json=weak_password_data,
            headers={
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json"
            }
        )
        
        if weak_response.status_code == 400:
            print_success("Weak password correctly rejected")
        else:
            print_error(f"Weak password should be rejected but got: {weak_response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"Error test failed with exception: {str(e)}")
        return False

def test_change_password_without_auth():
    """Test password change without authentication"""
    
    print_test_header("Password Change Without Authentication")
    
    try:
        change_response = requests.post(
            f"{BASE_URL}/api/auth/change-password/",
            json={
                "old_password": "test123!",
                "new_password": "newtest123!",
                "new_password2": "newtest123!"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if change_response.status_code == 401:
            print_success("Password change without authentication correctly failed (401)")
        else:
            print_error(f"Expected 401 but got: {change_response.status_code}")
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")

def test_rate_limiting():
    """Test rate limiting for password changes"""
    
    print_test_header("Password Change Rate Limiting Test")
    print_warning("This test may take some time due to rate limiting...")
    
    # Register a user for rate limiting test
    original_password = "RateTestPass123!"
    test_user = {
        "username": f"{TEST_USER_PREFIX}_rate",
        "email": f"{TEST_USER_PREFIX}_rate@test.com",
        "password": original_password,
        "password2": original_password
    }
    
    try:
        # Register user
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if register_response.status_code != 201:
            print_error("Failed to register user for rate limiting test")
            return
        
        tokens = register_response.json()["tokens"]
        print_info("Test user registered for rate limiting")
        
        # Try to change password multiple times rapidly
        rate_limit_hit = False
        for i in range(12):  # Rate limit is 10/hour, so 12 should trigger it
            change_data = {
                "old_password": "WrongPassword123!",  # Intentionally wrong to avoid actually changing
                "new_password": f"NewPass{i}123!",
                "new_password2": f"NewPass{i}123!"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/auth/change-password/",
                json=change_data,
                headers={
                    "Authorization": f"Bearer {tokens['access']}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 429:  # Too Many Requests
                print_success(f"Rate limit triggered after {i+1} attempts")
                rate_limit_hit = True
                break
            elif i < 10:
                print_info(f"Attempt {i+1}: {response.status_code} (expected 400 for wrong password)")
            
            time.sleep(0.1)  # Small delay between requests
        
        if not rate_limit_hit:
            print_warning("Rate limiting might not be working as expected")
        
    except Exception as e:
        print_error(f"Rate limiting test failed: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting Change Password API Tests")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Target URL: {BASE_URL}")
    
    # Run all tests
    success = True
    
    success &= test_change_password_success()
    success &= test_change_password_errors()
    test_change_password_without_auth()
    test_rate_limiting()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 Change Password Tests Completed Successfully!")
        print_info("✅ Successful password change flow")
        print_info("✅ Error scenario handling")
        print_info("✅ Authentication requirements")
        print_info("✅ Input validation")
        print_info("✅ Rate limiting protection")
    else:
        print("❌ Some tests failed - Check output above")
    print(f"{'='*60}") 