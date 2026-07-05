import sys
import os
import json
from datetime import date, time, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SqlSession

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.department import Department
from app.models.session import Session as DbSession
from app.models.attendance import Attendance as DbAttendance
from app.models.audit_log import AuditLog

def run_suite():
    client = TestClient(app)
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    print("=" * 60)
    print("      MILESTONE 6 INTEGRATION & VERIFICATION SUITE")
    print("=" * 60)
    
    # 1. Fetch authentication tokens
    print("\n[PREPARATION] Fetching authentication tokens for test roles...")
    tokens = {}
    roles = ["admin", "orgadmin", "coordinator", "member"]
    for role in roles:
        res = client.post("/api/v1/auth/login", json={"email": f"{role}@aip.com", "password": "password123"})
        if res.status_code == 200:
            tokens[role] = res.json()["access_token"]
            print(f" -> Secured token for {role}")
        else:
            print(f" -> FAILED to secure token for {role}.")
            results["failed"].append(f"Preparation: Token acquisition failed for {role}")
            
    if results["failed"]:
        sys.exit(1)

    db = SessionLocal()
    try:
        # Retrieve lookup IDs from database
        coordinator_user = db.query(User).filter(User.role == UserRole.Coordinator).first()
        org_admin_user = db.query(User).filter(User.role == UserRole.OrgAdmin).first()
        student_user = db.query(User).filter(User.email == "member@aip.com").first()
        test_dept = db.query(Department).first()

        if not coordinator_user or not org_admin_user or not student_user or not test_dept:
            print("[ERROR] Missing seed data (Coordinator, OrgAdmin, Student, or Department). Run seeding first.")
            sys.exit(1)

        coordinator_token = tokens["coordinator"]
        admin_token = tokens["admin"]
        member_token = tokens["member"]

        # ----------------------------------------------------
        # TEST 1: Create Session (Defaults & Validations)
        # ----------------------------------------------------
        print("\n[TEST 1] Verifying Session Scheduling CRUD (Draft)...")
        now_dt = datetime.now()
        start_time_str = (now_dt - timedelta(minutes=5)).strftime("%H:%M:%S")
        end_time_str = (now_dt + timedelta(hours=1)).strftime("%H:%M:%S")
        
        session_payload = {
            "name": "Intelligent Systems Seminar",
            "description": "Lab instructions on neural architectures.",
            "session_type": "Seminar",
            "date": str(date.today()),
            "start_time": start_time_str,
            "end_time": end_time_str,
            "grace_time": 10,
            "venue": "Research Lab B",
            "gps_radius": 50.0,
            "evidence_type": "GPS",
            "latitude": 12.9716, # Bangalore Center Coordinate
            "longitude": 77.5946,
            "capacity": 2,
            "recurrence_pattern": "Weekly",
            "recurrence_end_date": str(date.today() + timedelta(days=30)),
            "coordinator_id": coordinator_user.id,
            "department_id": test_dept.id,
            "organization_id": test_dept.organization_id
        }

        # A. Create Session
        res = client.post(
            "/api/v1/sessions/",
            json=session_payload,
            headers={"Authorization": f"Bearer {coordinator_token}"}
        )
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
        session_data = res.json()["data"]
        session_id = session_data["id"]
        assert session_data["status"] == "Draft"
        assert session_data["latitude"] == 12.9716
        assert session_data["capacity"] == 2
        print(" -> Passed: Create Session as Coordinator success.")

        # B. List Sessions with filters
        res = client.get(
            f"/api/v1/sessions/?q=Intelligent&status=Draft&organization_id={test_dept.organization_id}",
            headers={"Authorization": f"Bearer {coordinator_token}"}
        )
        assert res.status_code == 200
        assert len(res.json()["data"]) >= 1
        print(" -> Passed: Session filtering & text search success.")

        # ----------------------------------------------------
        # TEST 2: State Transitions & Timestamps
        # ----------------------------------------------------
        print("\n[TEST 2] Verifying Session Lifecycle State Transitions...")
        
        # Invalid state transition (Draft -> Active should fail)
        res = client.post(
            f"/api/v1/sessions/{session_id}/start",
            headers={"Authorization": f"Bearer {coordinator_token}"}
        )
        assert res.status_code == 400
        print(" -> Passed: Invalid state transition Draft -> Active correctly rejected.")

        # Publish/Schedule Session (Draft -> Scheduled)
        res = client.post(
            f"/api/v1/sessions/{session_id}/publish",
            headers={"Authorization": f"Bearer {coordinator_token}"}
        )
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "Scheduled"
        assert res.json()["data"]["scheduled_at"] is not None
        print(" -> Passed: Transition to Scheduled sets scheduled_at.")

        # ----------------------------------------------------
        # TEST 3: Participant Scope & Capacity Checks
        # ----------------------------------------------------
        print("\n[TEST 3] Verifying Roster Management & Capacity Validations...")
        
        # Bulk assignment: Add coordinator and student to roster
        assign_payload = {
            "user_ids": [coordinator_user.id, student_user.id]
        }
        res = client.post(
            f"/api/v1/sessions/{session_id}/assign-members",
            json=assign_payload,
            headers={"Authorization": f"Bearer {coordinator_token}"}
        )
        assert res.status_code == 200
        assert len(res.json()["data"]["assigned_members"]) == 2
        print(" -> Passed: Assigned 2 members successfully.")

        # Exceed Capacity (limit is 2, trying to assign another user)
        # Find another user
        extra_user = db.query(User).filter(User.id != coordinator_user.id, User.id != student_user.id).first()
        if extra_user:
            exceed_payload = {"user_ids": [extra_user.id]}
            res = client.post(
                f"/api/v1/sessions/{session_id}/assign-members",
                json=exceed_payload,
                headers={"Authorization": f"Bearer {coordinator_token}"}
            )
            assert res.status_code == 400
            assert "exceed session capacity" in res.json()["message"]
            print(" -> Passed: Capacity check correctly blocks overflow assignment.")

        # ----------------------------------------------------
        # TEST 4: Concurrency & Lock on Active Updates
        # ----------------------------------------------------
        print("\n[TEST 4] Verifying Concurrency Controls & Active Modifications Lock...")

        # Fetch session to get current updated_at timestamp
        res = client.get(f"/api/v1/sessions/{session_id}", headers={"Authorization": f"Bearer {coordinator_token}"})
        sess_read = res.json()["data"]
        updated_at_str = sess_read["updated_at"]

        # A. Trigger transition to Active (Scheduled -> Active)
        res_active = client.post(
            f"/api/v1/sessions/{session_id}/start",
            headers={"Authorization": f"Bearer {coordinator_token}"}
        )
        assert res_active.status_code == 200
        assert res_active.json()["data"]["status"] == "Active"
        assert res_active.json()["data"]["started_at"] is not None
        print(" -> Passed: Transition to Active sets started_at.")

        # B. Concurrency check: Edit session using stale updated_at header
        res_edit = client.put(
            f"/api/v1/sessions/{session_id}",
            json={"name": "Outdated Seminar Name"},
            headers={
                "Authorization": f"Bearer {coordinator_token}",
                "X-Updated-At": updated_at_str # stale timestamp
            }
        )
        assert res_edit.status_code == 400
        assert "modified by another request" in res_edit.json()["message"]
        print(" -> Passed: Stale concurrency timestamp rejected.")

        # C. Lock on Active: Attempt to modify session time when Active
        res_lock = client.put(
            f"/api/v1/sessions/{session_id}",
            json={"start_time": "08:00:00"},
            headers={"Authorization": f"Bearer {coordinator_token}"}
        )
        assert res_lock.status_code == 403
        assert "Cannot modify" in res_lock.json()["message"]
        print(" -> Passed: Modifications to locked attributes (start_time) during Active state rejected.")

        # ----------------------------------------------------
        # TEST 5: GPS Geofence Check-in Validations
        # ----------------------------------------------------
        print("\n[TEST 5] Verifying GPS Geofence & Check-In Window...")

        # A. Check-in outside geofence (Far away: Latitude 13.5, Longitude 78.0)
        far_checkin = {
            "latitude": 13.5,
            "longitude": 78.0,
            "verification_status": "Verified"
        }
        student_token = member_token

        res_far = client.post(
            f"/api/v1/sessions/{session_id}/check-in",
            json=far_checkin,
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert res_far.status_code == 403
        assert "Outside allowed GPS geofence area" in res_far.json()["message"]
        print(" -> Passed: Geofence validation rejects check-in from outside boundary.")

        # B. Check-in inside geofence (Near center: 12.9716, 77.5946)
        near_checkin = {
            "latitude": 12.97165,
            "longitude": 77.59465,
            "verification_status": "Verified"
        }
        res_near = client.post(
            f"/api/v1/sessions/{session_id}/check-in",
            json=near_checkin,
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert res_near.status_code == 200
        checkin_data = res_near.json()["data"]
        # Since it is checked in, check if status is Present or Late
        # Because the session time is 14:00 and we check in now, it will compute late depending on grace time.
        # It should return a valid AttendanceResponse
        assert checkin_data["check_in_time"] is not None
        assert checkin_data["gps_status"] == "Verified"
        print(" -> Passed: Check-in succeeds inside geofence.")

        # ----------------------------------------------------
        # TEST 6: Check-in Idempotency & Late status
        # ----------------------------------------------------
        print("\n[TEST 6] Verifying Check-in Idempotency...")
        
        res_idempotent = client.post(
            f"/api/v1/sessions/{session_id}/check-in",
            json=near_checkin,
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert res_idempotent.status_code == 200
        assert res_idempotent.json()["data"]["id"] == checkin_data["id"]
        print(" -> Passed: Duplicate check-in returned same record idempotently.")

        # ----------------------------------------------------
        # TEST 7: Check-out & Duration calculation
        # ----------------------------------------------------
        print("\n[TEST 7] Verifying Check-out & Duration calculation...")
        
        checkout_payload = {
            "latitude": 12.97162,
            "longitude": 77.59462,
            "verification_status": "Verified"
        }
        res_out = client.post(
            f"/api/v1/sessions/{session_id}/check-out",
            json=checkout_payload,
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert res_out.status_code == 200
        checkout_data = res_out.json()["data"]
        assert checkout_data["check_out_time"] is not None
        assert checkout_data["duration"] is not None
        print(f" -> Passed: Check-out completed. Duration: {checkout_data['duration']} minutes.")

        # ----------------------------------------------------
        # TEST 8: Manual Attendance Overwrites & Dashboard Stats
        # ----------------------------------------------------
        print("\n[TEST 8] Verifying Manual Overwrites & Dashboard Statistics...")
        
        # A. Manual Overwrite as Coordinator: mark user as Excused
        res_manual = client.post(
            f"/api/v1/sessions/{session_id}/manual-attendance?member_id={student_user.id}&status=Excused",
            headers={"Authorization": f"Bearer {coordinator_token}"}
        )
        assert res_manual.status_code == 200
        assert res_manual.json()["data"]["status"] == "Excused"
        print(" -> Passed: Manual status override to 'Excused' success.")

        # B. Get Extended Dashboard Stats
        res_stats = client.get("/api/v1/system/dashboard-stats", headers={"Authorization": f"Bearer {coordinator_token}"})
        assert res_stats.status_code == 200
        stats = res_stats.json()["data"]
        assert "todays_sessions" in stats
        assert "active_sessions" in stats
        assert "completed_sessions" in stats
        assert "total_attendance" in stats
        print(f" -> Passed: Extended Dashboard Stats. Active: {stats['active_sessions']}, Today's: {stats['todays_sessions']}.")

        results["passed"].append("Milestone 6 core workflows verified.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        results["failed"].append(f"Suite exception: {str(e)}")
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("                 VERIFICATION RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Passed: {len(results['passed'])}")
    print(f"Total Failed: {len(results['failed'])}")
    print("=" * 60)
    
    if results["failed"]:
        sys.exit(1)
    else:
        print("\nVerification SUITE PASSED SUCCESS!")

if __name__ == "__main__":
    run_suite()
