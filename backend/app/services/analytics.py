import time
import os
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session as SqlSession

from app.models.organization import Organization
from app.models.department import Department
from app.models.team import Team
from app.models.user import User
from app.models.session import Session
from app.models.attendance import Attendance
from app.services.audit_log import AuditLogService

# Lightweight thread-safe global caching containers
_dashboard_cache: Dict[str, Any] = {}
_charts_cache: Dict[str, Any] = {}

CACHE_EXPIRATION_SECONDS = int(os.getenv("ANALYTICS_CACHE_EXPIRY", "60"))

class AnalyticsService:
    def __init__(self, db: SqlSession):
        self.db = db

    def get_dashboard_metrics(self, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieves live system counts and rates. Caches evaluations to limit DB aggregates.
        """
        now = time.time()
        cache_key = f"dash_{organization_id or 'global'}"
        
        # Check cache validity
        if cache_key in _dashboard_cache:
            timestamp, data = _dashboard_cache[cache_key]
            if now - timestamp < CACHE_EXPIRATION_SECONDS:
                return data

        # Compute metrics
        # 1. Scope queries by organization if specified
        org_query = self.db.query(Organization)
        dept_query = self.db.query(Department)
        team_query = self.db.query(Team)
        user_query = self.db.query(User)
        session_query = self.db.query(Session)
        att_query = self.db.query(Attendance).join(Session)

        if organization_id:
            org_query = org_query.filter(Organization.id == organization_id)
            dept_query = dept_query.filter(Department.organization_id == organization_id)
            team_query = team_query.join(Department).filter(Department.organization_id == organization_id)
            user_query = user_query.filter(User.organization_id == organization_id)
            session_query = session_query.filter(Session.organization_id == organization_id)
            att_query = att_query.filter(Session.organization_id == organization_id)

        total_orgs = org_query.count()
        total_depts = dept_query.count()
        total_teams = team_query.count()
        total_members = user_query.count()
        total_sessions = session_query.count()
        
        active_sessions = session_query.filter(Session.status == "Active").count()
        completed_sessions = session_query.filter(Session.status == "Completed").count()

        # Attendances
        total_att = att_query.count()
        present = att_query.filter(Attendance.status == "Present").count()
        late = att_query.filter(Attendance.status == "Late").count()
        absent = att_query.filter(Attendance.status == "Absent").count()
        excused = att_query.filter(Attendance.status == "Excused").count()
        pending_ai = att_query.filter(Attendance.status == "Pending Approval").count()
        
        today_date = date.today()
        today_att = att_query.filter(Session.date == today_date).count()
        verified_att = att_query.filter(Attendance.verification_status == "Verified").count()
        pending_att = att_query.filter(Attendance.verification_status == "Pending").count()
        rejected_att = att_query.filter(Attendance.verification_status == "Failed").count()

        # Calculate average duration
        avg_dur = att_query.with_entities(func.avg(Attendance.duration)).filter(Attendance.duration != None).scalar()
        avg_dur_val = round(float(avg_dur), 1) if avg_dur is not None else 0.0

        # Calculate rates
        attendance_percentage = 100.0
        if total_att > 0:
            # Present and Late count as attended
            attended = present + late
            attendance_percentage = (attended / total_att) * 100.0

        # AI metrics
        total_ai = att_query.filter(Attendance.verification_method == "Face+GPS").count()
        ai_success = att_query.filter(Attendance.verification_method == "Face+GPS", Attendance.verification_status == "Verified").count()
        
        ai_success_rate = 100.0
        ai_failure_rate = 0.0
        if total_ai > 0:
            ai_success_rate = (ai_success / total_ai) * 100.0
            ai_failure_rate = 100.0 - ai_success_rate

        metrics = {
            "total_organizations": total_orgs,
            "total_departments": total_depts,
            "total_teams": total_teams,
            "total_members": total_members,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "attendance_percentage": round(attendance_percentage, 1),
            "present_count": present,
            "late_count": late,
            "absent_count": absent,
            "excused_count": excused,
            "pending_ai_approvals": pending_ai,
            "average_session_duration": avg_dur_val,
            "average_attendance_rate": round(attendance_percentage, 1),
            "ai_verification_success_rate": round(ai_success_rate, 1),
            "ai_verification_failure_rate": round(ai_failure_rate, 1),
            "today_attendance": today_att,
            "verified_attendance": verified_att,
            "pending_verification": pending_att,
            "rejected_attendance": rejected_att
        }

        # Cache metrics
        _dashboard_cache[cache_key] = (now, metrics)
        
        AuditLogService.log_event(
            db=self.db,
            actor_id=None, # System actor ID
            action="DashboardRefresh",
            module="Analytics",
            new_value=f"Dashboard statistics refreshed for scope: {organization_id or 'global'}."
        )

        return metrics

    def get_charts_data(self, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieves series datasets for interactive dashboard charts.
        """
        now = time.time()
        cache_key = f"charts_{organization_id or 'global'}"

        if cache_key in _charts_cache:
            timestamp, data = _charts_cache[cache_key]
            if now - timestamp < CACHE_EXPIRATION_SECONDS:
                return data

        # Compile trends for past 7 days
        daily_trend = []
        weekly_trend = []
        monthly_trend = []
        today = date.today()

        # Daily Trend (Last 7 Days)
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            # Query scoped by date
            q = self.db.query(Attendance).join(Session).filter(Session.date == d)
            if organization_id:
                q = q.filter(Session.organization_id == organization_id)
            
            pres = q.filter(Attendance.status.in_(["Present", "Late"])).count()
            abs_cnt = q.filter(Attendance.status == "Absent").count()
            daily_trend.append({
                "date": d.strftime("%b %d"),
                "present": pres,
                "absent": abs_cnt
            })

        # Weekly Trend (Past 4 Weeks)
        for i in range(3, -1, -1):
            end_d = today - timedelta(weeks=i)
            start_d = end_d - timedelta(days=6)
            q = self.db.query(Attendance).join(Session).filter(Session.date.between(start_d, end_d))
            if organization_id:
                q = q.filter(Session.organization_id == organization_id)

            pres = q.filter(Attendance.status.in_(["Present", "Late"])).count()
            abs_cnt = q.filter(Attendance.status == "Absent").count()
            weekly_trend.append({
                "week": f"Wk -{i}" if i > 0 else "This Wk",
                "present": pres,
                "absent": abs_cnt
            })

        # Monthly Trend (Past 3 Months)
        for i in range(2, -1, -1):
            # Compute start/end dates for months dynamically
            # For simplicity, divide into 30 day blocks
            end_d = today - timedelta(days=30 * i)
            start_d = end_d - timedelta(days=29)
            q = self.db.query(Attendance).join(Session).filter(Session.date.between(start_d, end_d))
            if organization_id:
                q = q.filter(Session.organization_id == organization_id)

            pres = q.filter(Attendance.status.in_(["Present", "Late"])).count()
            abs_cnt = q.filter(Attendance.status == "Absent").count()
            total = pres + abs_cnt
            rate = (pres / total * 100.0) if total > 0 else 100.0
            monthly_trend.append({
                "month": start_d.strftime("%B"),
                "rate": round(rate, 1)
            })

        # Attendance by Department
        dept_data = []
        depts = self.db.query(Department)
        if organization_id:
            depts = depts.filter(Department.organization_id == organization_id)
        
        for dept in depts.limit(10).all():
            q = self.db.query(Attendance).join(Session).filter(Session.department_id == dept.id)
            total = q.count()
            attended = q.filter(Attendance.status.in_(["Present", "Late"])).count()
            rate = (attended / total * 100.0) if total > 0 else 0.0
            dept_data.append({
                "name": dept.name,
                "rate": round(rate, 1)
            })

        # Attendance by Team
        team_data = []
        teams = self.db.query(Team)
        if organization_id:
            teams = teams.join(Department).filter(Department.organization_id == organization_id)
        
        for team in teams.limit(10).all():
            q = self.db.query(Attendance).join(User, Attendance.member_id == User.id).filter(User.team_id == team.id)
            total = q.count()
            attended = q.filter(Attendance.status.in_(["Present", "Late"])).count()
            rate = (attended / total * 100.0) if total > 0 else 0.0
            team_data.append({
                "name": team.name,
                "rate": round(rate, 1)
            })

        # Attendance by Organization (Global Admin Only)
        org_data = []
        if not organization_id:
            for org in self.db.query(Organization).limit(10).all():
                q = self.db.query(Attendance).join(Session).filter(Session.organization_id == org.id)
                total = q.count()
                attended = q.filter(Attendance.status.in_(["Present", "Late"])).count()
                rate = (attended / total * 100.0) if total > 0 else 0.0
                org_data.append({
                    "name": org.name,
                    "rate": round(rate, 1)
                })

        # AI Success vs Failure
        ai_success = self.db.query(Attendance).join(Session).filter(
            Attendance.verification_method == "Face+GPS",
            Attendance.verification_status == "Verified"
        )
        ai_fail = self.db.query(Attendance).join(Session).filter(
            Attendance.verification_method == "Face+GPS",
            Attendance.status == "Pending Approval"
        )
        if organization_id:
            ai_success = ai_success.filter(Session.organization_id == organization_id)
            ai_fail = ai_fail.filter(Session.organization_id == organization_id)

        ai_success_count = ai_success.count()
        ai_fail_count = ai_fail.count()

        # Session Completion Trend (Scheduled vs Completed)
        session_completion = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            q = self.db.query(Session).filter(Session.date == d)
            if organization_id:
                q = q.filter(Session.organization_id == organization_id)
            
            sched = q.filter(Session.status == "Scheduled").count()
            compl = q.filter(Session.status == "Completed").count()
            session_completion.append({
                "date": d.strftime("%b %d"),
                "scheduled": sched,
                "completed": compl
            })

        charts = {
            "daily_attendance_trend": daily_trend,
            "weekly_attendance_trend": weekly_trend,
            "monthly_attendance_trend": monthly_trend,
            "attendance_by_department": dept_data,
            "attendance_by_team": team_data,
            "attendance_by_organization": org_data,
            "ai_verification_success_vs_failure": [
                {"name": "Verified", "value": ai_success_count},
                {"name": "Mismatches/Pending", "value": ai_fail_count}
            ],
            "session_completion_trend": session_completion
        }

        _charts_cache[cache_key] = (now, charts)
        return charts
