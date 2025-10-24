#!/usr/bin/env python3
"""
Simple test script for IBM-FE-Login Authentication System
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_registration():
    """Test user registration"""
    print("Testing registration...")
    data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/register", json=data)
    print(f"Registration: {response.status_code} - {response.json()}")
    return response.status_code == 201

def test_login():
    """Test login with demo credentials"""
    print("Testing login...")
    data = {
        "email": "admin@ibm.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/api/login", json=data)
    result = response.json()
    print(f"Login: {response.status_code} - {result}")
    return response.status_code == 200, result.get("otp_preview")

def test_otp_verification(email, otp):
    """Test OTP verification"""
    print("Testing OTP verification...")
    data = {
        "email": email,
        "otp": otp
    }
    response = requests.post(f"{BASE_URL}/api/verify-otp", json=data)
    result = response.json()
    print(f"OTP Verification: {response.status_code} - {result}")
    return response.status_code == 200, result.get("token")

def test_dashboard(token):
    """Test dashboard access"""
    print("Testing dashboard access...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/dashboard", headers=headers)
    result = response.json()
    print(f"Dashboard: {response.status_code} - {result}")
    return response.status_code == 200

def main():
    print("IBM-FE-Login System Test")
    print("=" * 30)
    
    # Test registration
    test_registration()
    print()
    
    # Test login flow
    login_success, otp = test_login()
    if not login_success:
        print("Login failed, stopping tests")
        return
    print()
    
    # Test OTP verification
    otp_success, token = test_otp_verification("admin@ibm.com", otp)
    if not otp_success:
        print("OTP verification failed, stopping tests")
        return
    print()
    
    # Test dashboard
    dashboard_success = test_dashboard(token)
    print()
    
    if dashboard_success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")

if __name__ == "__main__":
    main()