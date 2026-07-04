import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.database import SessionLocal
from app.repositories.user import UserRepository
from app.services.user import UserService
from app.api.deps import get_user_repository, get_user_service, get_auth_service

def test_direct_repository_and_service():
    print("--- 1. Testing Repository & Service Layers Directly ---")
    db: Session = SessionLocal()
    try:
        # Create Repository
        user_repo = UserRepository(db)
        # Query User
        user = user_repo.get_by_email("member@aip.com")
        assert user is not None, "UserRepository failed to find member@aip.com"
        print(f"Repository Query Successful: Found user '{user.full_name}' with email '{user.email}'")

        # Create Service
        user_service = UserService(user_repo)
        service_user = user_service.get_user_by_email("member@aip.com")
        assert service_user.id == user.id, "UserService failed to return same user ID as repository"
        print(f"Service Execution Successful: Retreived user ID {service_user.id} through UserService")
        
        # Test generic CRUD BaseRepository.get_by_id
        db_user_by_id = user_repo.get_by_id(user.id)
        assert db_user_by_id.email == user.email, "BaseRepository.get_by_id failed"
        print(f"BaseRepository get_by_id Successful: Found user ID {db_user_by_id.id} by primary key")
        
    finally:
        db.close()

def test_dependency_injection_resolution():
    print("\n--- 2. Verifying Dependency Injection Resolution ---")
    db: Session = SessionLocal()
    try:
        # Verify repo provider
        repo = get_user_repository(db)
        assert isinstance(repo, UserRepository), "get_user_repository did not resolve to UserRepository"
        print("Dependency 'get_user_repository' resolved successfully.")

        # Verify service provider
        service = get_user_service(repo)
        assert isinstance(service, UserService), "get_user_service did not resolve to UserService"
        print("Dependency 'get_user_service' resolved successfully.")

        # Verify auth service provider
        auth_service = get_auth_service(repo)
        print("Dependency 'get_auth_service' resolved successfully.")
    finally:
        db.close()

def test_end_to_end_request_flow():
    print("\n--- 3. Testing End-to-End Request Flow: Router -> Service -> Repository -> Database ---")
    client = TestClient(app)

    # A. Test Successful Login Request Flow
    print("Flow A: Sending login request to POST /api/v1/auth/login...")
    payload = {
        "email": "member@aip.com",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200, f"Login failed: {response.text}"
    token_data = response.json()
    assert "access_token" in token_data, "No access token in response"
    assert token_data["user"]["email"] == "member@aip.com", "Returned user email does not match"
    print(f"Flow A Success: Authenticated successfully. Token: {token_data['access_token'][:30]}...")

    # B. Test Authenticated User Fetch Flow
    print("\nFlow B: Sending request to GET /api/v1/auth/me with Bearer Token...")
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}"
    }
    response_me = client.get("/api/v1/auth/me", headers=headers)
    assert response_me.status_code == 200, f"Fetch /me failed: {response_me.text}"
    user_me = response_me.json()
    assert user_me["email"] == "member@aip.com", "Me endpoint returned incorrect user profile"
    print(f"Flow B Success: Retrieved profile of '{user_me['full_name']}' successfully.")

    # C. Test Invalid Credentials Domain Exception Response Mapping Flow
    print("\nFlow C: Testing Domain Exception translation on invalid credentials...")
    bad_payload = {
        "email": "member@aip.com",
        "password": "wrong_password"
    }
    response_bad = client.post("/api/v1/auth/login", json=bad_payload)
    assert response_bad.status_code == 400, f"Expected status 400, got {response_bad.status_code}"
    error_data = response_bad.json()
    assert error_data["success"] is False, "Response should have success=False"
    assert error_data["errors"][0]["type"] == "InvalidCredentialsError", "Expected InvalidCredentialsError type"
    print(f"Flow C Success: Domain exception mapped correctly to: HTTP 400 - {error_data['message']}")

if __name__ == "__main__":
    test_direct_repository_and_service()
    test_dependency_injection_resolution()
    test_end_to_end_request_flow()
    print("\nALL REPOSITORY & DEPENDENCY LIFECYCLE FLOW TESTS COMPLETED SUCCESSFULLY!")
