import sys
import os

# Inject backend path into PYTHONPATH to allow execution from scratch folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_system_and_middleware():
    print("--- 1. Testing GET /api/v1/system/info (System Info) ---")
    response = client.get("/api/v1/system/info")
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "operational"
    assert data["data"]["environment"]["database_connected"] is False
    
    print("\n--- 2. Testing Logging Middleware Latency Header ---")
    print(f"Response Headers: {dict(response.headers)}")
    assert "x-process-time-ms" in response.headers
    print(f"Latency Header: {response.headers['x-process-time-ms']}ms")
    
    print("\n--- 3. Testing Validation Exception Handler Envelope ---")
    # Trigger validation error by sending invalid email on login endpoint
    response_val = client.post("/api/v1/auth/login", json={
        "email": "not-an-email-address",
        "password": ""
    })
    print(f"Status Code: {response_val.status_code}")
    print(f"Response Body: {response_val.json()}")
    assert response_val.status_code == 422
    val_data = response_val.json()
    assert val_data["success"] is False
    assert val_data["message"] == "Validation failed"
    assert len(val_data["errors"]) > 0
    print("Validation errors caught and wrapped correctly!")
    
    print("\n--- 4. Testing HTTP Exception Handler Envelope ---")
    # Trigger 403 on /me without headers (HTTPBearer auto-raises 403)
    response_http = client.get("/api/v1/auth/me")
    print(f"Status Code: {response_http.status_code}")
    print(f"Response Body: {response_http.json()}")
    assert response_http.status_code in [401, 403]
    http_data = response_http.json()
    assert http_data["success"] is False
    print("HTTP error caught and wrapped correctly!")
    
    print("\nALL SYSTEM, MIDDLEWARE, AND EXCEPTION TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_system_and_middleware()
