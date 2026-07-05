import sys
import os
import time
from datetime import date, datetime, timedelta

# Adjust Python path to load modules correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.services.analytics import _dashboard_cache

def run_suite():
    print("============================================================")
    print("      MILESTONE 8 INTEGRATION & VERIFICATION SUITE")
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
            print("[ERROR] Missing seed data. Run seeding first.")
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

        # ----------------------------------------------------
        # TEST 1: Dashboard Stats & Memory Caching
        # ----------------------------------------------------
        print("\n[TEST 1] Verifying Dashboard aggregates & Cache mechanics...")
        
        # Empty cache first
        _dashboard_cache.clear()

        # First request (DB read)
        t_start = time.perf_counter()
        res_db = client.get("/api/v1/analytics/dashboard", headers={"Authorization": f"Bearer {coord_token}"})
        t_db = time.perf_counter() - t_start
        
        assert res_db.status_code == 200
        stats = res_db.json()["data"]
        assert "total_members" in stats
        assert "attendance_percentage" in stats
        assert "present_count" in stats
        assert "pending_ai_approvals" in stats

        # Second request (Served from local memory cache)
        t_start = time.perf_counter()
        res_cache = client.get("/api/v1/analytics/dashboard", headers={"Authorization": f"Bearer {coord_token}"})
        t_cache = time.perf_counter() - t_start
        
        assert res_cache.status_code == 200
        # Cache retrieval should be near-instantaneous
        print(f" -> DB query latency: {t_db*1000.1:.2f}ms | Cache hit latency: {t_cache*1000.1:.2f}ms")
        assert t_cache < t_db or t_cache < 0.05 # Assert cache performance speedup
        print(" -> Passed: Live dashboard aggregates computed and cached successfully.")
        passed_count += 1

        # ----------------------------------------------------
        # TEST 2: Charts Dataset series
        # ----------------------------------------------------
        print("\n[TEST 2] Verifying Interactive Charts series payloads...")
        res_charts = client.get("/api/v1/analytics/charts", headers={"Authorization": f"Bearer {coord_token}"})
        assert res_charts.status_code == 200
        charts = res_charts.json()["data"]
        
        assert "daily_attendance_trend" in charts
        assert "weekly_attendance_trend" in charts
        assert "attendance_by_department" in charts
        assert "attendance_by_team" in charts
        assert "ai_verification_success_vs_failure" in charts
        assert len(charts["daily_attendance_trend"]) == 7
        print(" -> Passed: SVG charts datasets returned correct structures.")
        passed_count += 1

        # ----------------------------------------------------
        # TEST 3: Report Exports (CSV, Excel, PDF)
        # ----------------------------------------------------
        print("\n[TEST 3] Verifying Multi-Format Reports Export...")
        
        # A. CSV Export
        res_csv = client.get("/api/v1/reports/export?format=csv", headers={"Authorization": f"Bearer {coord_token}"})
        assert res_csv.status_code == 200
        assert "text/csv" in res_csv.headers["content-type"]
        assert "Attendance ID,Member ID" in res_csv.text
        
        # B. Excel Export
        res_xls = client.get("/api/v1/reports/export?format=excel", headers={"Authorization": f"Bearer {coord_token}"})
        assert res_xls.status_code == 200
        assert "application/vnd.ms-excel" in res_xls.headers["content-type"]
        assert "<table" in res_xls.text
        
        # C. PDF Export (print-ready HTML layout)
        res_pdf = client.get("/api/v1/reports/export?format=pdf", headers={"Authorization": f"Bearer {coord_token}"})
        assert res_pdf.status_code == 200
        assert "text/html" in res_pdf.headers["content-type"]
        assert "<h1>Attendance platform" in res_pdf.text

        print(" -> Passed: CSV, Excel, and PDF reports exported successfully.")
        passed_count += 1

        # ----------------------------------------------------
        # TEST 4: Notifications Dispatch and Reading
        # ----------------------------------------------------
        print("\n[TEST 4] Verifying Notification services...")
        
        # Post a notification using notification service directly
        from app.services.notification import NotificationService
        ns = NotificationService(db)
        
        # Trigger mock alert dispatch
        notif = ns.send_notification(
            user_id=member_user.id,
            title="Biometric check-in verification",
            message="Your AI face liveness match succeeded.",
            notif_type="Attendance",
            email_recipient=member_user.email
        )
        assert notif.is_read is False

        # Read notifications list via API
        res_list = client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {member_token}"})
        assert res_list.status_code == 200
        notifs = res_list.json()["data"]
        assert len(notifs) > 0
        
        # Target latest notification ID
        notif_id = notifs[0]["id"]
        
        # Mark as read
        res_read = client.post(f"/api/v1/notifications/{notif_id}/read", headers={"Authorization": f"Bearer {member_token}"})
        assert res_read.status_code == 200
        assert res_read.json()["data"]["is_read"] is True

        # Clear notifications
        res_clear = client.post("/api/v1/notifications/clear", headers={"Authorization": f"Bearer {member_token}"})
        assert res_clear.status_code == 200
        
        # Verify cleared
        res_list_empty = client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {member_token}"})
        assert len(res_list_empty.json()["data"]) == 0

        print(" -> Passed: Notifications dispatched, read, and dismissed successfully.")
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
