import math
from datetime import datetime, timedelta, date, time
from typing import Optional, List
from sqlalchemy.orm import Session as SqlSession
from app.models.attendance import Attendance
from app.models.session import Session
from app.models.user import User
from app.repositories.attendance import AttendanceRepository
from app.core.domain_exceptions import (
    DomainException, ObjectNotFoundError, PermissionDeniedError
)
from app.services.audit_log import AuditLogService

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface
    using the Haversine formula. Returns distance in meters.
    """
    R = 6371000.0 # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return R * c

class AttendanceService:
    def __init__(self, db: SqlSession):
        self.db = db
        self.repo = AttendanceRepository(db)

    def check_in(
        self,
        session_id: int,
        member_id: int,
        latitude: float,
        longitude: float,
        verification_status: Optional[str] = "Verified",
        actor_id: Optional[int] = None
    ) -> Attendance:
        # 1. Retrieve session and member
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise ObjectNotFoundError(f"Session with ID {session_id} not found.")

        member = self.db.query(User).filter(User.id == member_id).first()
        if not member:
            raise ObjectNotFoundError(f"Member with ID {member_id} not found.")

        # 2. Idempotency Check
        existing_record = self.repo.get_by_member_and_session(member_id, session_id)
        if existing_record and existing_record.check_in_time is not None:
            # Already checked in, return the existing record idempotently
            return existing_record

        # 3. Session State & Window Validation
        if session.status != "Active":
            raise DomainException(f"Attendance cannot be submitted because session is in '{session.status}' status.")

        now = datetime.now()
        # Combine date and time to construct exact datetime bounds
        start_dt = datetime.combine(session.date, session.start_time)
        end_dt = datetime.combine(session.date, session.end_time)

        if now < start_dt or now > end_dt:
            raise DomainException("Attendance check-in is not allowed outside the session time boundaries.")

        # 4. GPS Geofence Check
        if session.latitude is not None and session.longitude is not None and session.gps_radius is not None:
            dist = calculate_haversine_distance(latitude, longitude, session.latitude, session.longitude)
            if dist > session.gps_radius:
                raise PermissionDeniedError(
                    f"Check-in rejected: Outside allowed GPS geofence area. Distance: {dist:.1f}m, Max: {session.gps_radius}m"
                )

        # 5. Tardiness Check (Grace Period check)
        grace_limit_dt = start_dt + timedelta(minutes=session.grace_time)
        attendance_status = "Present"
        if now > grace_limit_dt:
            attendance_status = "Late"

        # 6. Store or Create Attendance Record
        if existing_record:
            att = existing_record
            att.status = attendance_status
            att.check_in_time = now
            att.gps_status = "Verified"
            att.verification_status = verification_status
            att.activity_status = "Active"
        else:
            att = Attendance(
                member_id=member_id,
                session_id=session_id,
                status=attendance_status,
                check_in_time=now,
                gps_status="Verified",
                verification_status=verification_status,
                activity_status="Active"
            )
            self.db.add(att)

        self.db.commit()
        self.db.refresh(att)

        AuditLogService.log_event(
            db=self.db,
            actor_id=actor_id or member_id,
            action="SubmitAttendance",
            module="Attendance",
            new_value=f"Check-in: User {member_id} to Session {session_id} as {attendance_status}"
        )
        return att

    def check_out(
        self,
        session_id: int,
        member_id: int,
        latitude: float,
        longitude: float,
        verification_status: Optional[str] = "Verified",
        actor_id: Optional[int] = None
    ) -> Attendance:
        # 1. Get attendance record
        att = self.repo.get_by_member_and_session(member_id, session_id)
        if not att or not att.check_in_time:
            raise DomainException("No check-in records found for this member and session.")

        # 2. Get session
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise ObjectNotFoundError(f"Session with ID {session_id} not found.")

        # 3. GPS Geofence Check
        if session.latitude is not None and session.longitude is not None and session.gps_radius is not None:
            dist = calculate_haversine_distance(latitude, longitude, session.latitude, session.longitude)
            if dist > session.gps_radius:
                raise PermissionDeniedError(
                    f"Check-out rejected: Outside allowed GPS geofence area. Distance: {dist:.1f}m"
                )

        # 4. Perform check-out updates
        now = datetime.now()
        att.check_out_time = now
        delta = now - att.check_in_time
        att.duration = int(delta.total_seconds() / 60) # duration in minutes
        att.activity_status = "Completed"

        self.db.commit()
        self.db.refresh(att)

        AuditLogService.log_event(
            db=self.db,
            actor_id=actor_id or member_id,
            action="CheckOut",
            module="Attendance",
            new_value=f"Check-out: User {member_id} from Session {session_id}, Duration: {att.duration} min"
        )
        return att

    def submit_manual_attendance(
        self,
        session_id: int,
        member_id: int,
        status: str,
        actor_id: Optional[int] = None
    ) -> Attendance:
        """
        Allows administrators to manually mark/update attendance status (e.g. Excused, Present, Absent).
        """
        valid_statuses = ["Present", "Late", "Absent", "Excused"]
        if status not in valid_statuses:
            raise DomainException(f"Invalid attendance status: {status}. Must be one of {valid_statuses}")

        att = self.repo.get_by_member_and_session(member_id, session_id)
        
        if att:
            old_val = att.status
            att.status = status
            if status == "Absent" or status == "Excused":
                att.check_in_time = None
                att.check_out_time = None
                att.duration = None
        else:
            att = Attendance(
                member_id=member_id,
                session_id=session_id,
                status=status,
                gps_status="Manual",
                verification_status="Manual"
            )
            self.db.add(att)
            old_val = "None"

        self.db.commit()
        self.db.refresh(att)

        AuditLogService.log_event(
            db=self.db,
            actor_id=actor_id,
            action="ModifyAttendance",
            module="Attendance",
            new_value=f"Manual attendance status for user {member_id} in session {session_id} set to {status} from {old_val}"
        )
        return att
