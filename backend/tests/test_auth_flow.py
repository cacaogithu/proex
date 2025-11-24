import requests
import sys
import time
import os

BASE_URL = "http://localhost:8000"
EMAIL = "test_user@example.com"
PASSWORD = "password123"

def test_auth_flow():
    print("🚀 Starting Auth Flow Test...")
    
    # 1. Register
    print("\n1. Testing Registration...")
    try:
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={"email": EMAIL, "password": PASSWORD})
        if resp.status_code == 200:
            print("✅ Registration successful")
        elif resp.status_code == 400 and "already registered" in resp.text:
            print("⚠️ User already registered (expected if re-running)")
        else:
            print(f"❌ Registration failed: {resp.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

    # 2. Login
    print("\n2. Testing Login...")
    resp = requests.post(f"{BASE_URL}/api/auth/token", data={"username": EMAIL, "password": PASSWORD})
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        print("✅ Login successful, token received")
    else:
        print(f"❌ Login failed: {resp.text}")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Me
    print("\n3. Testing /me endpoint...")
    resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if resp.status_code == 200 and resp.json()["email"] == EMAIL:
        print("✅ /me endpoint verified")
    else:
        print(f"❌ /me failed: {resp.text}")
        sys.exit(1)

    # 4. List Submissions (Protected)
    print("\n4. Testing List Submissions (Protected)...")
    resp = requests.get(f"{BASE_URL}/api/submissions", headers=headers)
    if resp.status_code == 200:
        print(f"✅ List submissions successful (Count: {len(resp.json())})")
    else:
        print(f"❌ List submissions failed: {resp.text}")
        sys.exit(1)

    # 5. Test Unauthorized Access
    print("\n5. Testing Unauthorized Access...")
    resp = requests.get(f"{BASE_URL}/api/submissions")
    if resp.status_code == 401:
        print("✅ Unauthorized access blocked (401)")
    else:
        print(f"❌ Failed to block unauthorized access. Status: {resp.status_code}")
        sys.exit(1)

    print("\n✨ All Auth Tests Passed!")

if __name__ == "__main__":
    # Wait for server to start if needed
    time.sleep(2) 
    test_auth_flow()
