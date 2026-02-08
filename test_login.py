"""Test login functionality"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """Test user registration"""
    print("Testing registration...")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test User"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 201

def test_login():
    """Test user login"""
    print("\nTesting login...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"\nToken received: {token[:20]}...")
        return True
    return False

def test_me(token):
    """Test /me endpoint with token"""
    print("\nTesting /me endpoint...")
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    try:
        # Test registration
        test_register()
        
        # Test login
        if test_login():
            print("\n✓ Login successful!")
        else:
            print("\n✗ Login failed!")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
