import sys
import os
from datetime import datetime, date, time, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.department import Department
from app.models.team import Team
from app.models.session import Session as DatabaseSession
from app.models.attendance import Attendance
from app.models.activity import Activity
from app.models.notification import Notification
from app.models.report import Report
from app.models.audit_log import AuditLog

def seed_db():
    db: Session = SessionLocal()
    try:
        print("Starting database seeding...")

        # 1. Seed Organization
        org = db.query(Organization).filter(Organization.name == "AIP Enterprises").first()
        if not org:
            org = Organization(
                name="AIP Enterprises",
                logo="https://via.placeholder.com/150",
                description="AIP Global Headquarters Operations Node.",
                email="operations@aip-enterprises.com",
                phone="+1-555-0199",
                website="https://aip-enterprises.com",
                country="United States",
                state="California",
                city="San Francisco",
                timezone="America/Los_Angeles",
                address="100 Intelligence Way, Suite 400",
                status="Active"
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"Seeded Organization: {org.name} (ID: {org.id})")
        else:
            print(f"Organization '{org.name}' already exists.")

        # 2. Seed Departments
        dept_eng = db.query(Department).filter(Department.name == "Engineering", Department.organization_id == org.id).first()
        if not dept_eng:
            dept_eng = Department(
                name="Engineering",
                description="Core Technology and Software Engineering Division.",
                organization_id=org.id,
                status="Active"
            )
            db.add(dept_eng)
            db.commit()
            db.refresh(dept_eng)
            print(f"Seeded Department: {dept_eng.name}")
        else:
            print(f"Department '{dept_eng.name}' already exists.")

        dept_ops = db.query(Department).filter(Department.name == "Operations", Department.organization_id == org.id).first()
        if not dept_ops:
            dept_ops = Department(
                name="Operations",
                description="Global Infrastructure and Client Delivery Operations.",
                organization_id=org.id,
                status="Active"
            )
            db.add(dept_ops)
            db.commit()
            db.refresh(dept_ops)
            print(f"Seeded Department: {dept_ops.name}")
        else:
            print(f"Department '{dept_ops.name}' already exists.")

        # 3. Seed Teams
        team_alpha = db.query(Team).filter(Team.name == "Alpha Team", Team.department_id == dept_eng.id).first()
        if not team_alpha:
            team_alpha = Team(
                name="Alpha Team",
                department_id=dept_eng.id,
                status="Active"
            )
            db.add(team_alpha)
            db.commit()
            db.refresh(team_alpha)
            print(f"Seeded Team: {team_alpha.name}")
        else:
            print(f"Team '{team_alpha.name}' already exists.")

        # 4. Seed Users (with hashed passwords)
        default_users = [
            {
                "email": "admin@aip.com",
                "full_name": "System Administrator",
                "role": UserRole.SystemAdmin,
                "password": "password123",
                "is_active": True,
                "phone": "+1-555-0100",
                "gender": "Other",
                "organization_id": org.id,
                "department_id": None,
                "team_id": None
            },
            {
                "email": "coordinator@aip.com",
                "full_name": "Attendance Coordinator",
                "role": UserRole.Coordinator,
                "password": "password123",
                "is_active": True,
                "phone": "+1-555-0101",
                "gender": "Female",
                "organization_id": org.id,
                "department_id": dept_eng.id,
                "team_id": team_alpha.id
            },
            {
                "email": "member@aip.com",
                "full_name": "Team Member",
                "role": UserRole.Member,
                "password": "password123",
                "is_active": True,
                "phone": "+1-555-0102",
                "gender": "Male",
                "organization_id": org.id,
                "department_id": dept_eng.id,
                "team_id": team_alpha.id,
                "emergency_contact": "Jane Doe (+1-555-0190)",
                "joining_date": date(2025, 1, 15)
            },
            {
                "email": "auditor@aip.com",
                "full_name": "External Compliance Auditor",
                "role": UserRole.Auditor,
                "password": "password123",
                "is_active": True,
                "phone": "+1-555-0103",
                "gender": "Female",
                "organization_id": org.id,
                "department_id": None,
                "team_id": None
            },
            {
                "email": "orgadmin@aip.com",
                "full_name": "Enterprise Admin",
                "role": UserRole.OrgAdmin,
                "password": "password123",
                "is_active": True,
                "phone": "+1-555-0104",
                "gender": "Male",
                "organization_id": org.id,
                "department_id": dept_ops.id,
                "team_id": None
            }
        ]

        users_map = {}
        for u_data in default_users:
            user = db.query(User).filter(User.email == u_data["email"]).first()
            if not user:
                user = User(
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    hashed_password=get_password_hash(u_data["password"]),
                    is_active=u_data["is_active"],
                    phone=u_data["phone"],
                    gender=u_data["gender"],
                    organization_id=u_data["organization_id"],
                    department_id=u_data["department_id"],
                    team_id=u_data["team_id"],
                    emergency_contact=u_data.get("emergency_contact"),
                    joining_date=u_data.get("joining_date"),
                    status="Active"
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"Seeded User: {user.email} (Role: {user.role.value})")
            else:
                print(f"User '{user.email}' already exists.")
            users_map[u_data["email"]] = user

        # Update Head / Coordinator of Department and Leader of Team for complete reference integrity
        dept_eng.head_id = users_map["orgadmin@aip.com"].id
        dept_eng.coordinator_id = users_map["coordinator@aip.com"].id
        team_alpha.leader_id = users_map["coordinator@aip.com"].id
        db.commit()
        print("Updated Department heads and Team leaders.")

        # 5. Seed Sessions
        today = date.today()
        default_sessions = [
            {
                "name": "Daily Engineering Sync",
                "description": "Daily standup for Software Engineering Division to track progress.",
                "session_type": "Meeting",
                "date": today,
                "start_time": time(9, 30),
                "end_time": time(10, 0),
                "grace_time": 10,
                "venue": "Conference Room A / Hybrid",
                "gps_radius": 50.0,
                "evidence_type": "GPS",
                "coordinator_id": users_map["coordinator@aip.com"].id,
                "department_id": dept_eng.id,
                "organization_id": org.id,
                "status": "Published"
            },
            {
                "name": "Weekly Sprint Planning",
                "description": "Planning session for Sprint 24 deliverables.",
                "session_type": "Meeting",
                "date": today + timedelta(days=2),
                "start_time": time(14, 0),
                "end_time": time(15, 30),
                "grace_time": 15,
                "venue": "Main Auditorium / MS Teams",
                "gps_radius": 100.0,
                "evidence_type": "GPS+Face",
                "coordinator_id": users_map["coordinator@aip.com"].id,
                "department_id": dept_eng.id,
                "organization_id": org.id,
                "status": "Draft"
            },
            {
                "name": "Quarterly Operations Review",
                "description": "System architecture compliance and operations audit.",
                "session_type": "Lecture",
                "date": today - timedelta(days=5),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "grace_time": 15,
                "venue": "Executive Suite 1",
                "gps_radius": 30.0,
                "evidence_type": "GPS",
                "coordinator_id": users_map["orgadmin@aip.com"].id,
                "department_id": dept_ops.id,
                "organization_id": org.id,
                "status": "Closed",
                "checkout_time": time(12, 0)
            }
        ]

        sessions_map = {}
        for s_data in default_sessions:
            session = db.query(DatabaseSession).filter(
                DatabaseSession.name == s_data["name"], 
                DatabaseSession.date == s_data["date"]
            ).first()
            if not session:
                session = DatabaseSession(
                    name=s_data["name"],
                    description=s_data["description"],
                    session_type=s_data["session_type"],
                    date=s_data["date"],
                    start_time=s_data["start_time"],
                    end_time=s_data["end_time"],
                    grace_time=s_data["grace_time"],
                    checkout_time=s_data.get("checkout_time"),
                    venue=s_data["venue"],
                    gps_radius=s_data["gps_radius"],
                    evidence_type=s_data["evidence_type"],
                    coordinator_id=s_data["coordinator_id"],
                    department_id=s_data["department_id"],
                    organization_id=s_data["organization_id"],
                    status=s_data["status"]
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                print(f"Seeded Session: {session.name} (Status: {session.status})")
            else:
                print(f"Session '{session.name}' already exists.")
            sessions_map[s_data["name"]] = session

        # 6. Seed Session Members (Many-to-Many mapping)
        # Assign members to sessions
        eng_members = [users_map["member@aip.com"], users_map["coordinator@aip.com"]]
        for member in eng_members:
            # Sync engineering sync session
            session = sessions_map["Daily Engineering Sync"]
            if member not in session.assigned_members:
                session.assigned_members.append(member)
                print(f"Assigned user {member.email} to session '{session.name}'")
            
            # Sync sprint planning session
            session_sprint = sessions_map["Weekly Sprint Planning"]
            if member not in session_sprint.assigned_members:
                session_sprint.assigned_members.append(member)
                print(f"Assigned user {member.email} to session '{session_sprint.name}'")
        
        # Assign ops to operations review
        ops_members = [users_map["orgadmin@aip.com"], users_map["member@aip.com"]]
        for member in ops_members:
            session = sessions_map["Quarterly Operations Review"]
            if member not in session.assigned_members:
                session.assigned_members.append(member)
                print(f"Assigned user {member.email} to session '{session.name}'")
        db.commit()

        # 7. Seed Attendance Records
        # Create presence verification logs for the closed Operations Review session
        ops_session = sessions_map["Quarterly Operations Review"]
        attendance_logs = [
            {
                "member_id": users_map["member@aip.com"].id,
                "session_id": ops_session.id,
                "check_in_time": datetime.combine(ops_session.date, time(9, 58)),
                "check_out_time": datetime.combine(ops_session.date, time(12, 1)),
                "duration": 123,
                "gps_status": "Verified",
                "verification_status": "Verified",
                "activity_status": "Completed",
                "status": "Present"
            },
            {
                "member_id": users_map["orgadmin@aip.com"].id,
                "session_id": ops_session.id,
                "check_in_time": datetime.combine(ops_session.date, time(10, 5)),
                "check_out_time": datetime.combine(ops_session.date, time(12, 0)),
                "duration": 115,
                "gps_status": "Verified",
                "verification_status": "Verified",
                "activity_status": "None",
                "status": "Present"
            }
        ]

        for att_data in attendance_logs:
            att = db.query(Attendance).filter(
                Attendance.member_id == att_data["member_id"],
                Attendance.session_id == att_data["session_id"]
            ).first()
            if not att:
                att = Attendance(**att_data)
                db.add(att)
                print(f"Seeded Attendance for member ID {att.member_id} in session ID {att.session_id}")
            else:
                print(f"Attendance for member ID {att.member_id} already exists.")
        db.commit()

        # 8. Seed Activities
        activities_data = [
            {
                "title": "Complete Database Architecture Migration",
                "description": "Establish schemas, autogenerate migrations, and verify table constraints.",
                "category": "Development",
                "priority": "High",
                "assigned_by_id": users_map["coordinator@aip.com"].id,
                "assigned_to_id": users_map["member@aip.com"].id,
                "session_id": sessions_map["Daily Engineering Sync"].id,
                "department_id": dept_eng.id,
                "start_time": datetime.now() - timedelta(hours=4),
                "end_time": datetime.now(),
                "status": "Completed",
                "remarks": "Database tables and indexes created and validated successfully.",
                "evidence": "verify_tables.py successful output"
            },
            {
                "title": "Review Operations Audit Compliance",
                "description": "Audit user records and compliance checklist.",
                "category": "Technical Support",
                "priority": "Medium",
                "assigned_by_id": users_map["orgadmin@aip.com"].id,
                "assigned_to_id": users_map["member@aip.com"].id,
                "session_id": sessions_map["Quarterly Operations Review"].id,
                "department_id": dept_ops.id,
                "status": "Pending"
            }
        ]

        for act_data in activities_data:
            act = db.query(Activity).filter(
                Activity.title == act_data["title"],
                Activity.assigned_to_id == act_data["assigned_to_id"]
            ).first()
            if not act:
                act = Activity(**act_data)
                db.add(act)
                print(f"Seeded Activity: {act.title}")
            else:
                print(f"Activity '{act.title}' already exists.")
        db.commit()

        # 9. Seed Notifications
        notifications_data = [
            {
                "user_id": users_map["member@aip.com"].id,
                "title": "Welcome to AIP Dashboard",
                "message": "Your profile has been created and bound to Department 'Engineering' and Team 'Alpha Team'.",
                "type": "System",
                "is_read": False
            },
            {
                "user_id": users_map["member@aip.com"].id,
                "title": "New Session Published",
                "message": "Attendance Coordinator published a new session: 'Daily Engineering Sync'. Please stand by to verify presence.",
                "type": "Session",
                "is_read": True
            }
        ]

        for not_data in notifications_data:
            notif = db.query(Notification).filter(
                Notification.user_id == not_data["user_id"],
                Notification.title == not_data["title"]
            ).first()
            if not notif:
                notif = Notification(**not_data)
                db.add(notif)
                print(f"Seeded Notification: {notif.title}")
            else:
                print(f"Notification '{notif.title}' already exists.")
        db.commit()

        # 10. Seed Reports
        report = db.query(Report).filter(Report.title == "Q2 Attendance Compliance Audit Report").first()
        if not report:
            report = Report(
                title="Q2 Attendance Compliance Audit Report",
                description="Aggregated attendance presence and geofence verification compliance metrics.",
                report_type="Attendance",
                format="Excel",
                generated_by_id=users_map["admin@aip.com"].id,
                file_path="/exports/reports/q2_attendance_compliance.xlsx"
            )
            db.add(report)
            db.commit()
            print(f"Seeded Report: {report.title}")
        else:
            print(f"Report '{report.title}' already exists.")

        # 11. Seed Audit Logs
        log = db.query(AuditLog).filter(AuditLog.action == "SEED_DATABASE").first()
        if not log:
            log = AuditLog(
                actor_id=users_map["admin@aip.com"].id,
                action="SEED_DATABASE",
                module="System",
                device="AIP Local Dev Server",
                ip_address="127.0.0.1",
                new_value="Database schema initialized and baseline development dataset applied.",
                reason="Initialize fresh database state for Milestone 4 integration verification."
            )
            db.add(log)
            db.commit()
            print(f"Seeded Audit Log for Action: {log.action}")
        else:
            print("Database seeding audit log already exists.")

        print("\nDATABASE SEEDING COMPLETED SUCCESSFULLY!")
    except Exception as e:
        db.rollback()
        print("Database seeding failed:")
        print(e)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
