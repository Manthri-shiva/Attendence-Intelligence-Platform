import sys
import os
from datetime import date, datetime, time, timedelta

# Adjust Python path to load modules correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.session import Session
from app.models.attendance import Attendance
from app.services.auth import AuthService

def run_suite():
    print("============================================================")
    print("      MILESTONE 7 INTEGRATION & VERIFICATION SUITE")
    print("============================================================")

    db = SessionLocal()
    client = TestClient(app)

    passed_count = 0
    failed_count = 0

    try:
        # 1. Fetch lookup records
        coordinator_user = db.query(User).filter(User.role == UserRole.Coordinator).first()
        member_user = db.query(User).filter(User.email == "member@aip.com").first()
        
        if not coordinator_user or not member_user:
            print("[ERROR] Missing seed data (Coordinator or Member). Run seeding first.")
            sys.exit(1)

        # Login and fetch Bearer tokens
        print("\n[PREPARATION] Generating API access tokens...")
        
        # Coord token
        coord_auth = client.post("/api/v1/auth/login", json={"email": coordinator_user.email, "password": "password123"})
        coord_token = coord_auth.json()["access_token"]
        
        # Member token
        member_auth = client.post("/api/v1/auth/login", json={"email": member_user.email, "password": "password123"})
        member_token = member_auth.json()["access_token"]

        print(" -> Tokens secured successfully.")

        # Create session payload dynamically based on current time
        now_dt = datetime.now()
        start_time_str = (now_dt - timedelta(minutes=5)).strftime("%H:%M:%S")
        end_time_str = (now_dt + timedelta(hours=1)).strftime("%H:%M:%S")

        # ----------------------------------------------------
        # TEST 1: Create active session with Block policy
        # ----------------------------------------------------
        print("\n[TEST 1] Verifying GPS + AI Face Verification (Block policy, threshold 0.85)...")
        
        session_payload = {
            "name": "AI Verification Seminar",
            "description": "Biometrics and Anti-Spoofing lab.",
            "session_type": "Seminar",
            "date": str(date.today()),
            "start_time": start_time_str,
            "end_time": end_time_str,
            "grace_time": 10,
            "venue": "Lab Alpha",
            "gps_radius": 100.0,
            "evidence_type": "GPS",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "face_confidence_threshold": 0.85,
            "fallback_policy": "Block",
            "coordinator_id": coordinator_user.id,
            "organization_id": member_user.organization_id
        }

        # Create session
        res_create = client.post(
            "/api/v1/sessions/",
            json=session_payload,
            headers={"Authorization": f"Bearer {coord_token}"}
        )
        assert res_create.status_code in [200, 201]
        session_id = res_create.json()["data"]["id"]

        # Assign member
        client.post(
            f"/api/v1/sessions/{session_id}/assign-members",
            json={"user_ids": [member_user.id]},
            headers={"Authorization": f"Bearer {coord_token}"}
        )

        # Transition to Scheduled
        client.post(
            f"/api/v1/sessions/{session_id}/publish",
            headers={"Authorization": f"Bearer {coord_token}"}
        )

        # Transition to Active
        client.post(
            f"/api/v1/sessions/{session_id}/start",
            headers={"Authorization": f"Bearer {coord_token}"}
        )

        # A. Attempt check-in with high confidence and valid GPS (Present/Verified)
        checkin_payload_valid = {
            "latitude": 12.9716,
            "longitude": 77.5946,
            "image_b64": "test_biometric_frame_string",
            "simulate_confidence": 0.95
        }

        res_checkin = client.post(
            f"/api/v1/sessions/{session_id}/check-in",
            json=checkin_payload_valid,
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert res_checkin.status_code == 200
        att_data = res_checkin.json()["data"]
        assert att_data["status"] in ["Present", "Late"]
        assert att_data["verification_status"] == "Verified"
        assert att_data["confidence_score"] == 0.95
        assert att_data["verification_method"] == "Face+GPS"
        assert att_data["provider_name"] == "MockFaceRecognition"
        print(" -> Passed: Standard high-confidence check-in verified successfully.")
        passed_count += 1

        # ----------------------------------------------------
        # TEST 2: Verify Mismatch Rejection (Confidence < Threshold)
        # ----------------------------------------------------
        print("\n[TEST 2] Verifying AI Confidence Mismatch Rejection...")
        checkin_payload_low_conf = {
            "latitude": 12.9716,
            "longitude": 77.5946,
            "image_b64": "test_biometric_frame_string",
            "simulate_confidence": 0.70 # Under 0.85 threshold
        }

        res_low_conf = client.post(
            f"/api/v1/sessions/{session_id}/check-in",
            json=checkin_payload_low_conf,
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert res_low_conf.status_code == 403
        assert "Match confidence" in res_low_conf.json()["message"]
        print(" -> Passed: AI face confidence mismatch rejected successfully.")
        passed_count += 1

        # ----------------------------------------------------
        # TEST 3: Verify Liveness Spoof Detections
        # ----------------------------------------------------
        print("\n[TEST 3] Verifying Anti-Spoofing detections...")
        
        # A. Static Photo detection check
        res_spoof_photo = client.post(
            f"/api/v1/sessions/{session_id}/check-in",
            json={
                "latitude": 12.9716,
                "longitude": 77.5946,
                "image_b64": "test_biometric_frame_string",
                "simulate_liveness": "Static Photo"
            },
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert res_spoof_photo.status_code == 403
        assert "Static photo detected" in res_spoof_photo.json()["message"]

        # B. Screen Replay attack check
        res_spoof_replay = client.post(
            f"/api/v1/sessions/{session_id}/check-in",
            json={
                "latitude": 12.9716,
                "longitude": 77.5946,
                "image_b64": "test_biometric_frame_string",
                "simulate_liveness": "Replay Attempt"
            },
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert res_spoof_replay.status_code == 403
        assert "Screen replay attack detected" in res_spoof_replay.json()["message"]

        # C. Low Lighting warning check
        res_spoof_dark = client.post(
            f"/api/v1/sessions/{session_id}/check-in",
            json={
                "latitude": 12.9716,
                "longitude": 77.5946,
                "image_b64": "test_biometric_frame_string",
                "simulate_liveness": "Low Lighting"
            },
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert res_spoof_dark.status_code == 403
        assert "Insufficient lighting" in res_spoof_dark.json()["message"]

        print(" -> Passed: Spoof detections (Photo, Screen Replays, Lighting) successfully rejected.")
        passed_count += 1

        # ----------------------------------------------------
        # TEST 4: Fallback Policy check (Coordinator Approval)
        # ----------------------------------------------------
        print("\n[TEST 4] Verifying Fallback Policy (CoordinatorApproval)...")
        
        # Create a new session with CoordinatorApproval fallback policy
        res_create_fallback = client.post(
            "/api/v1/sessions/",
            json={
                "name": "AI Verification Fallback Lecture",
                "description": "Biometrics fallback workflows.",
                "session_type": "Lecture",
                "date": str(date.today()),
                "start_time": start_time_str,
                "end_time": end_time_str,
                "grace_time": 10,
                "venue": "Lecture Hall 4",
                "gps_radius": 100.0,
                "evidence_type": "GPS",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "face_confidence_threshold": 0.85,
                "fallback_policy": "CoordinatorApproval",
                "coordinator_id": coordinator_user.id,
                "organization_id": member_user.organization_id
            },
            headers={"Authorization": f"Bearer {coord_token}"}
        )
        assert res_create_fallback.status_code in [200, 201]
        fallback_session_id = res_create_fallback.json()["data"]["id"]

        # Assign member
        client.post(
            f"/api/v1/sessions/{fallback_session_id}/assign-members",
            json={"user_ids": [member_user.id]},
            headers={"Authorization": f"Bearer {coord_token}"}
        )

        # Transition to Scheduled
        client.post(
            f"/api/v1/sessions/{fallback_session_id}/publish",
            headers={"Authorization": f"Bearer {coord_token}"}
        )

        # Transition to Active
        client.post(
            f"/api/v1/sessions/{fallback_session_id}/start",
            headers={"Authorization": f"Bearer {coord_token}"}
        )

        # Perform check-in with low confidence (0.70 < 0.85)
        # Under CoordinatorApproval fallback, this must transition status to "Pending Approval"
        res_fb_checkin = client.post(
            f"/api/v1/sessions/{fallback_session_id}/check-in",
            json={
                "latitude": 12.9716,
                "longitude": 77.5946,
                "image_b64": "test_biometric_frame_string",
                "simulate_confidence": 0.70
            },
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert res_fb_checkin.status_code == 200
        att_fb_data = res_fb_checkin.json()["data"]
        assert att_fb_data["status"] == "Pending Approval"
        assert att_fb_data["verification_status"] == "Pending"
        assert att_fb_data["confidence_score"] == 0.70
        print(" -> Passed: Low-confidence check-in successfully routed to 'Pending Approval' fallback state.")
        passed_count += 1

        # ----------------------------------------------------
        # TEST 5: Manual Coordinator Approval Workflow
        # ----------------------------------------------------
        print("\n[TEST 5] Verifying Manual Coordinator Approval route...")
        res_approve = client.post(
            f"/api/v1/sessions/{fallback_session_id}/approve-attendance?member_id={member_user.id}",
            headers={"Authorization": f"Bearer {coord_token}"}
        )
        assert res_approve.status_code == 200
        approved_data = res_approve.json()["data"]
        assert approved_data["status"] in ["Present", "Late"]
        assert approved_data["verification_status"] == "Verified"
        print(" -> Passed: Coordinator manual approval successfully verified pending fallback attendance.")
        passed_count += 1

    except Exception as e:
        print(f"\n[FAIL] Test suite execution encountered an exception:")
        import traceback
        traceback.print_exc()
        failed_count += 1

    finally:
        db.close()

    print("\n============================================================")
    print("                 VERIFICATION RESULTS SUMMARY")
    print("============================================================")
    print(f"Total Passed: {passed_count}")
    print(f"Total Failed: {failed_count}")
    print("============================================================")

    if failed_count > 0:
        print("\nVerification SUITE FAILED!")
        sys.exit(1)
    else:
        print("\nVerification SUITE PASSED SUCCESS!")

if __name__ == "__main__":
    run_suite()
