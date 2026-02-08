"""Test login as the frontend would do it"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_login_flow():
    """Test the full login flow from frontend perspective"""
    
    # Step 1: Try to register a new user
    print("1. Attempting to register user...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": "frontendtest@example.com",
                "password": "Test123!",
                "name": "Frontend Test"
            },
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"   ✓ User registered: {response.json()}")
        elif response.status_code == 400:
            print(f"   → User already exists (this is OK for testing)")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return False
    
    # Step 2: Login
    print("\n2. Attempting to login...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "frontendtest@example.com",
                "password": "Test123!"
            },
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"   ✓ Login successful!")
            print(f"   Token: {token[:30]}...")
            
            # Step 3: Test /me endpoint with token
            print("\n3. Testing /me endpoint with token...")
            me_response = requests.get(
                f"{BASE_URL}/auth/me",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            print(f"   Status: {me_response.status_code}")
            if me_response.status_code == 200:
                print(f"   ✓ User data: {me_response.json()}")
                return True
            else:
                print(f"   ✗ Error: {me_response.text}")
                return False
        else:
            print(f"   ✗ Login failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Frontend Login Flow ===\n")
    success = test_login_flow()
    print(f"\n{'='*40}")
    if success:
        print("✓ ALL TESTS PASSED - Login flow working correctly!")
        print("\nIf login still fails in the browser:")
        print("1. Clear browser cache and localStorage")
        print("2. Check browser console for errors")
        print("3. Verify VITE_API_URL in frontend/.env")
    else:
        print("✗ TESTS FAILED - There is an issue with login")
    print("="*40)
