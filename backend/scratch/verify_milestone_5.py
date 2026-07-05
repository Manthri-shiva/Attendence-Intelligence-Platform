import sys
import os
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.department import Department
from app.models.team import Team
from app.models.audit_log import AuditLog

def run_suite():
    client = TestClient(app)
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    print("=" * 60)
    print("      MILESTONE 5 INTEGRATION & VERIFICATION SUITE")
    print("=" * 60)
    
    # Authenticate default seeded users to get tokens
    print("\n[PREPARATION] Fetching authentication tokens for test roles...")
    tokens = {}
    roles = ["admin", "orgadmin", "coordinator", "member"]
    for role in roles:
        res = client.post("/api/v1/auth/login", json={"email": f"{role}@aip.com", "password": "password123"})
        if res.status_code == 200:
            tokens[role] = res.json()["access_token"]
            print(f" -> Secured token for {role}")
        else:
            print(f" -> FAILED to secure token for {role}. Seed data missing?")
            results["failed"].append(f"Preparation: Seed user login failed for {role}")
            
    if results["failed"]:
        sys.exit(1)

    # ----------------------------------------------------
    # TEST 1: Organizations CRUD & Unique Constraint
    # ----------------------------------------------------
    print("\n[TEST 1] Verifying Organizations CRUD & Validation...")
    try:
        # A. Create organization as SystemAdmin (Super Admin)
        org_name = "Milestone 5 Test Org"
        org_payload = {
            "name": org_name,
            "description": "Verification test tenant node.",
            "email": "m5@test-org.com",
            "timezone": "America/New_York",
            "status": "Active"
        }
        res_create = client.post(
            "/api/v1/organizations/",
            json=org_payload,
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        assert res_create.status_code == 201, f"Expected 201, got {res_create.status_code}. Response: {res_create.text}"
        org_data = res_create.json()["data"]
        org_id = org_data["id"]
        results["passed"].append("Organizations: Create Organization as Super Admin success.")
        
        # B. Validate duplicate name constraint (400)
        res_dup = client.post(
            "/api/v1/organizations/",
            json=org_payload,
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        assert res_dup.status_code == 400, f"Expected 400 for duplicate org name, got {res_dup.status_code}"
        results["passed"].append("Organizations: Duplication check on name returns HTTP 400.")
        
        # C. Read Organization List
        res_list = client.get(
            "/api/v1/organizations/?limit=10",
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        assert res_list.status_code == 200, f"Expected 200, got {res_list.status_code}"
        orgs_list = res_list.json()["data"]
        assert len(orgs_list) >= 2, "Should find seed org and test org."
        results["passed"].append("Organizations: Paginated List query returns correctly.")
        
        # D. Scope checks: OrgAdmin can only view their own organization
        res_scope = client.get(
            "/api/v1/organizations/",
            headers={"Authorization": f"Bearer {tokens['orgadmin']}"}
        )
        assert res_scope.status_code == 200
        orgs_scope = res_scope.json()["data"]
        assert len(orgs_scope) == 1, f"OrgAdmin should only see 1 org, got {len(orgs_scope)}"
        results["passed"].append("Organizations: Scoped visibility constraints enforced on OrgAdmin.")
        
    except Exception as e:
        print(f" -> Failed: {e}")
        results["failed"].append(f"Organizations CRUD: {e}")
        
    # ----------------------------------------------------
    # TEST 2: Departments CRUD & Scope Restrictions
    # ----------------------------------------------------
    print("\n[TEST 2] Verifying Departments CRUD & Scope Checks...")
    try:
        # A. Create department as OrgAdmin inside their own organization
        # We need to know what organization_id the orgadmin user has
        db = SessionLocal()
        orgadmin_user = db.query(User).filter(User.email == "orgadmin@aip.com").first()
        org_id_scope = orgadmin_user.organization_id
        db.close()
        
        dept_name = "Milestone 5 Dept"
        dept_payload = {
            "name": dept_name,
            "description": "Validation test department.",
            "organization_id": org_id_scope,
            "status": "Active"
        }
        res_dept = client.post(
            "/api/v1/departments/",
            json=dept_payload,
            headers={"Authorization": f"Bearer {tokens['orgadmin']}"}
        )
        assert res_dept.status_code == 201, f"Expected 201, got {res_dept.status_code}. Response: {res_dept.text}"
        dept_id = res_dept.json()["data"]["id"]
        results["passed"].append("Departments: Create Department as OrgAdmin inside their own tenant.")
        
        # B. Duplicate department inside same organization should fail (400)
        res_dept_dup = client.post(
            "/api/v1/departments/",
            json=dept_payload,
            headers={"Authorization": f"Bearer {tokens['orgadmin']}"}
        )
        assert res_dept_dup.status_code == 400, f"Expected 400, got {res_dept_dup.status_code}"
        results["passed"].append("Departments: Duplicate department names within the same organization rejected with 400.")
        
        # C. Create department in another organization should return 403 Forbidden for OrgAdmin
        other_dept_payload = {
            "name": "Unauthorized Dept",
            "organization_id": org_id, # The org we created as admin above
            "status": "Active"
        }
        res_dept_forb = client.post(
            "/api/v1/departments/",
            json=other_dept_payload,
            headers={"Authorization": f"Bearer {tokens['orgadmin']}"}
        )
        assert res_dept_forb.status_code == 403, f"Expected 403, got {res_dept_forb.status_code}"
        results["passed"].append("Departments: Multi-tenant boundary checks reject department creation in other orgs with HTTP 403.")
        
    except Exception as e:
        print(f" -> Failed: {e}")
        results["failed"].append(f"Departments CRUD: {e}")

    # ----------------------------------------------------
    # TEST 3: Teams CRUD & Duplicate Validation
    # ----------------------------------------------------
    print("\n[TEST 3] Verifying Teams CRUD & Duplicate Prevention...")
    try:
        # A. Create Team inside Department
        team_name = "Milestone 5 Team"
        team_payload = {
            "name": team_name,
            "department_id": dept_id,
            "status": "Active"
        }
        res_team = client.post(
            "/api/v1/teams/",
            json=team_payload,
            headers={"Authorization": f"Bearer {tokens['orgadmin']}"}
        )
        assert res_team.status_code == 201, f"Expected 201, got {res_team.status_code}. Response: {res_team.text}"
        team_id = res_team.json()["data"]["id"]
        results["passed"].append("Teams: Create Team under department success.")
        
        # B. Duplicate team inside same department should fail
        res_team_dup = client.post(
            "/api/v1/teams/",
            json=team_payload,
            headers={"Authorization": f"Bearer {tokens['orgadmin']}"}
        )
        assert res_team_dup.status_code == 400, f"Expected 400, got {res_team_dup.status_code}"
        results["passed"].append("Teams: Duplicate team name inside the same department rejected with HTTP 400.")
        
    except Exception as e:
        print(f" -> Failed: {e}")
        results["failed"].append(f"Teams CRUD: {e}")

    # ----------------------------------------------------
    # TEST 4: Users/Members CRUD & Phone Format Checks
    # ----------------------------------------------------
    print("\n[TEST 4] Verifying Users/Members CRUD & Custom Validations...")
    try:
        # A. Create user with invalid phone format (should return 400)
        invalid_user_payload = {
            "email": "invalid_phone@test.com",
            "full_name": "Invalid Phone User",
            "role": "Student",
            "password": "securepassword123",
            "phone": "not-a-phone-number",
            "organization_id": org_id_scope,
            "department_id": dept_id,
            "team_id": team_id
        }
        res_invalid_phone = client.post(
            "/api/v1/users/",
            json=invalid_user_payload,
            headers={"Authorization": f"Bearer {tokens['orgadmin']}"}
        )
        assert res_invalid_phone.status_code == 400, f"Expected 400, got {res_invalid_phone.status_code}"
        results["passed"].append("Users: Phone number format constraint verified (raises HTTP 400 on alphanumeric strings).")

        # B. Create user with valid phone format (should return 201)
        valid_user_payload = {
            "email": "valid_user_m5@test.com",
            "full_name": "Valid Member User",
            "role": "Student",
            "password": "securepassword123",
            "phone": "+1 555-901-2003",
            "organization_id": org_id_scope,
            "department_id": dept_id,
            "team_id": team_id
        }
        res_valid_user = client.post(
            "/api/v1/users/",
            json=valid_user_payload,
            headers={"Authorization": f"Bearer {tokens['orgadmin']}"}
        )
        assert res_valid_user.status_code == 201, f"Expected 201, got {res_valid_user.status_code}. Response: {res_valid_user.text}"
        new_user_id = res_valid_user.json()["data"]["id"]
        results["passed"].append("Users: Create user with correct validations completes successfully.")

        # C. Verify password is NOT exposed in UserResponse payload
        user_res_data = res_valid_user.json()["data"]
        assert "hashed_password" not in user_res_data, "Hashed password was exposed in user payload!"
        assert "password" not in user_res_data, "Plaintext password was exposed in user payload!"
        results["passed"].append("Users: Hashed password is excluded from User response payload serialization.")

        # D. Deactivate user account
        res_deact = client.delete(
            f"/api/v1/users/{new_user_id}",
            headers={"Authorization": f"Bearer {tokens['orgadmin']}"}
        )
        assert res_deact.status_code == 200, f"Expected 200, got {res_deact.status_code}"
        assert res_deact.json()["data"]["is_active"] is False, "User should be marked inactive"
        assert res_deact.json()["data"]["status"] == "Inactive", "User status should be Inactive"
        results["passed"].append("Users: Deactivate user sets account status to Inactive successfully.")

        # E. Activate user account
        res_act = client.post(
            f"/api/v1/users/{new_user_id}/activate",
            headers={"Authorization": f"Bearer {tokens['orgadmin']}"}
        )
        assert res_act.status_code == 200, f"Expected 200, got {res_act.status_code}"
        assert res_act.json()["data"]["is_active"] is True, "User should be marked active"
        assert res_act.json()["data"]["status"] == "Active", "User status should be Active"
        results["passed"].append("Users: Activate user restores active status successfully.")
        
    except Exception as e:
        print(f" -> Failed: {e}")
        results["failed"].append(f"Users CRUD: {e}")

    # ----------------------------------------------------
    # TEST 5: Audit Log Generation
    # ----------------------------------------------------
    print("\n[TEST 5] Checking Audit Log Persistence...")
    try:
        db = SessionLocal()
        logs = db.query(AuditLog).filter(AuditLog.module.in_(["Organization", "Department", "Team", "User"])).all()
        db.close()
        
        # Verify that we generated logs for various CRUD events
        actions_logged = [log.action for log in logs]
        print(f" -> Actions logged during suite: {actions_logged}")
        assert len(logs) >= 5, f"Expected at least 5 audit log entries, found {len(logs)}"
        assert "Create" in actions_logged, "Should have logged Create actions"
        assert "Deactivate" in actions_logged or "Deactivate" in [l.action for l in logs], "Should have logged Deactivate actions"
        
        results["passed"].append("Audit Logs: Automated audit log writes verified successfully.")
        
    except Exception as e:
        print(f" -> Failed: {e}")
        results["failed"].append(f"Audit Logging: {e}")

    # ----------------------------------------------------
    # SUMMARY
    # ----------------------------------------------------
    print("\n" + "=" * 60)
    print("                 VERIFICATION RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Passed: {len(results['passed'])}")
    print(f"Total Failed: {len(results['failed'])}")
    print(f"Total Warnings: {len(results['warnings'])}")
    print("=" * 60)
    
    # Save a verification summary file in scratch
    with open("scratch/verification_m5_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    if len(results["failed"]) > 0:
        print("\nVerification SUITE FAILED!")
        sys.exit(1)
    else:
        print("\nVerification SUITE PASSED SUCCESS!")
        sys.exit(0)

if __name__ == "__main__":
    run_suite()
