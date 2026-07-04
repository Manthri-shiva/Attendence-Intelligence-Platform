import sys
import os

# Inject backend path into PYTHONPATH to allow execution from within scratch folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_flow():
    print("--- 1. Testing Login with correct credentials ---")
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@aip.com",
        "password": "password123"
    })
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    print("\n--- 2. Testing Login with incorrect credentials ---")
    response_bad = client.post("/api/v1/auth/login", json={
        "email": "admin@aip.com",
        "password": "wrongpassword"
    })
    print(f"Status Code: {response_bad.status_code}")
    print(f"Response: {response_bad.json()}")
    assert response_bad.status_code == 400
    
    print("\n--- 3. Testing GET /me with valid token ---")
    response_me = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    print(f"Status Code: {response_me.status_code}")
    print(f"Response: {response_me.json()}")
    assert response_me.status_code == 200
    assert response_me.json()["email"] == "admin@aip.com"
    
    print("\n--- 4. Testing GET /me with invalid token ---")
    response_me_bad = client.get("/api/v1/auth/me", headers={
        "Authorization": "Bearer badtoken"
    })
    print(f"Status Code: {response_me_bad.status_code}")
    print(f"Response: {response_me_bad.json()}")
    assert response_me_bad.status_code == 401
    
    print("\n--- 5. Testing Forgot Password ---")
    response_forgot = client.post("/api/v1/auth/forgot-password", json={
        "email": "admin@aip.com"
    })
    print(f"Status Code: {response_forgot.status_code}")
    print(f"Response: {response_forgot.json()}")
    assert response_forgot.status_code == 200
    reset_token = response_forgot.json()["token"]
    
    print("\n--- 6. Testing Reset Password ---")
    response_reset = client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": "newpassword123",
        "confirm_password": "newpassword123"
    })
    print(f"Status Code: {response_reset.status_code}")
    print(f"Response: {response_reset.json()}")
    assert response_reset.status_code == 200
    
    print("\n--- 7. Testing Login with new password ---")
    response_login_new = client.post("/api/v1/auth/login", json={
        "email": "admin@aip.com",
        "password": "newpassword123"
    })
    print(f"Status Code: {response_login_new.status_code}")
    print(f"Response: {response_login_new.json()}")
    assert response_login_new.status_code == 200
    
    print("\n--- 8. Testing Login with old password (should fail) ---")
    response_login_old = client.post("/api/v1/auth/login", json={
        "email": "admin@aip.com",
        "password": "password123"
    })
    print(f"Status Code: {response_login_old.status_code}")
    print(f"Response: {response_login_old.json()}")
    assert response_login_old.status_code == 400
    
    print("\nALL AUTHENTICATION INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_auth_flow()
