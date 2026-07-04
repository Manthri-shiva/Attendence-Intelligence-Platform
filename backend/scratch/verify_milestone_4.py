import sys
import os
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.core.database import SessionLocal

def run_suite():
    client = TestClient(app)
    results = {
        "passed": [],
        "failed": [],
        "warnings": [],
        "performance": {}
    }
    
    print("=" * 60)
    print("   MILESTONE 4 COMPLETE INTEGRATION & VERIFICATION SUITE")
    print("=" * 60)
    
    # ----------------------------------------------------
    # TEST 1: Security - Hashed Passwords & Serialized Exclusions
    # ----------------------------------------------------
    print("\n[TEST 1] Verifying Security Requirements...")
    try:
        db = SessionLocal()
        user_db = db.query(User).filter(User.email == "member@aip.com").first()
        db.close()
        
        # Verify stored format is hashed, not plain
        assert user_db.hashed_password != "password123", "Password stored in plaintext!"
        assert user_db.hashed_password.startswith("$2b$") or len(user_db.hashed_password) > 20, "Password hash invalid format"
        results["passed"].append("Security: Password stored securely as a strong hash in the database.")
        
        # Authenticate to get token
        login_res = client.post("/api/v1/auth/login", json={"email": "member@aip.com", "password": "password123"})
        login_data = login_res.json()
        token = login_data["access_token"]
        
        # Verify login response does not expose hashed_password
        assert "hashed_password" not in login_data["user"], "Exposed hashed_password in login response!"
        assert "password" not in login_data["user"], "Exposed password in login response!"
        results["passed"].append("Security: Password fields excluded from login serialization.")
        
        # Verify /me response does not expose hashed_password
        me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        me_data = me_res.json()
        assert "hashed_password" not in me_data, "Exposed hashed_password in /me serialization!"
        results["passed"].append("Security: Password fields excluded from /me profile serialization.")
        print(" -> Passed security checks.")
    except Exception as e:
        print(f" -> Failed: {e}")
        results["failed"].append(f"Security Checks: {e}")
        
    # ----------------------------------------------------
    # TEST 2: Database Integrity & Constraints
    # ----------------------------------------------------
    print("\n[TEST 2] Verifying Unique Email Uniqueness Constraints...")
    try:
        db = SessionLocal()
        db.begin()
        # Attempt to insert a user with a duplicate email
        dup_user = User(
            email="member@aip.com",
            full_name="Duplicate User",
            hashed_password=get_password_hash("password123"),
            role=UserRole.Member,
            is_active=True
        )
        try:
            db.add(dup_user)
            db.commit()
            raise AssertionError("Duplicate email inserted without raising IntegrityError!")
        except IntegrityError:
            db.rollback()
            results["passed"].append("Database: Uniqueness constraint verified on users(email).")
            print(" -> Passed database integrity uniqueness checks.")
        finally:
            db.close()
    except Exception as e:
        print(f" -> Failed: {e}")
        results["failed"].append(f"Database Integrity: {e}")

    # ----------------------------------------------------
    # TEST 3: Validation, HTTP Handlers & Error Status Codes
    # ----------------------------------------------------
    print("\n[TEST 3] Verifying API Validation and Exception Handling...")
    try:
        # A. Missing fields validation (422)
        res_422 = client.post("/api/v1/auth/login", json={"email": "not-an-email"})
        assert res_422.status_code == 422, f"Expected 422 validation error, got {res_422.status_code}"
        assert res_422.json()["success"] is False, "Failure response should wrap success: False"
        results["passed"].append("API Validation: Incorrect payloads return HTTP 422 with wrapped envelopes.")

        # B. Unauthorized request (403)
        res_403 = client.get("/api/v1/auth/me")
        assert res_403.status_code == 403, f"Expected 403 status, got {res_403.status_code}"
        results["passed"].append("Authorization: Unauthenticated requests to protected endpoints return HTTP 403.")

        # C. Invalid credentials mapping (400)
        res_400 = client.post("/api/v1/auth/login", json={"email": "member@aip.com", "password": "wrong_password"})
        assert res_400.status_code == 400, f"Expected 400 status, got {res_400.status_code}"
        results["passed"].append("Exception Handling: Service layer domain exceptions map successfully to HTTP 400.")
        
        # D. Non-existent user forgot password (404)
        res_404 = client.post("/api/v1/auth/forgot-password", json={"email": "unknown@aip.com"})
        assert res_404.status_code == 404, f"Expected 404 status, got {res_404.status_code}"
        results["passed"].append("Exception Handling: Service layer UserNotFoundError maps successfully to HTTP 404.")
        print(" -> Passed validation and error mapping checks.")
    except Exception as e:
        print(f" -> Failed: {e}")
        results["failed"].append(f"API Exception Mapping: {e}")

    # ----------------------------------------------------
    # TEST 4: Swagger Documentation Availability
    # ----------------------------------------------------
    print("\n[TEST 4] Verifying Swagger OpenAPI Documentation Availability...")
    try:
        res_docs = client.get("/docs")
        assert res_docs.status_code == 200, "Swagger UI not accessible!"
        assert "swagger-ui" in res_docs.text.lower() or "swagger" in res_docs.text.lower(), "Docs page does not contain Swagger UI components"
        results["passed"].append("Documentation: Swagger/OpenAPI UI endpoint (/docs) resolves to 200 OK.")
        print(" -> Passed documentation checks.")
    except Exception as e:
        print(f" -> Failed: {e}")
        results["failed"].append(f"Documentation check: {e}")

    # ----------------------------------------------------
    # TEST 5: Performance & Response Latencies
    # ----------------------------------------------------
    print("\n[TEST 5] Testing API Performance and Response Latencies...")
    latencies = []
    try:
        for i in range(10):
            start = time.perf_counter()
            res_perf = client.get("/api/v1/system/info")
            elapsed = (time.perf_counter() - start) * 1000.0
            latencies.append(elapsed)
            
        avg_lat = sum(latencies) / len(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        
        results["performance"] = {
            "avg_latency_ms": round(avg_lat, 2),
            "min_latency_ms": round(min_lat, 2),
            "max_latency_ms": round(max_lat, 2)
        }
        
        # Recommend threshold of 200ms for system info
        if avg_lat > 200.0:
            results["warnings"].append(f"Performance Warning: Average endpoint latency is high ({round(avg_lat, 2)} ms)")
        else:
            results["passed"].append(f"Performance: Response speeds are efficient (Avg: {round(avg_lat, 2)} ms).")
        print(f" -> Done. Average: {round(avg_lat, 2)}ms (Min: {round(min_lat, 2)}ms, Max: {round(max_lat, 2)}ms)")
    except Exception as e:
        print(f" -> Failed to measure: {e}")
        results["failed"].append(f"Performance Testing: {e}")

    print("\n" + "=" * 60)
    print("                 VERIFICATION RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Passed: {len(results['passed'])}")
    print(f"Total Failed: {len(results['failed'])}")
    print(f"Total Warnings: {len(results['warnings'])}")
    print("=" * 60)
    
    # Save a verification summary file in scratch
    import json
    with open("scratch/verification_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    if len(results["failed"]) > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_suite()
