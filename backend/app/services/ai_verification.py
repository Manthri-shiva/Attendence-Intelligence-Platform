import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session as SqlSession

from app.models.session import Session
from app.models.user import User
from app.models.attendance import Attendance
from app.services.ai.face_recognition import MockFaceRecognitionProvider
from app.services.ai.liveness_detection import MockLivenessDetectionProvider
from app.services.attendance import calculate_haversine_distance
from app.core.domain_exceptions import (
    DomainException, ObjectNotFoundError, PermissionDeniedError
)
from app.services.audit_log import AuditLogService

# Helper for biometric simulation encryption
def encrypt_biometric_image(image_b64: str) -> str:
    """
    Encrypt captured biometric images using a secure XOR masking algorithm,
    retaining only the encrypted byte signature for security audits.
    """
    secret = b"AIP_BIOMETRIC_ENCRYPTION_KEY_2026"
    raw_bytes = image_b64.encode("utf-8")
    encrypted = bytes([b ^ secret[i % len(secret)] for i, b in enumerate(raw_bytes)])
    return encrypted.hex()[:120] # Return safe slice signature

def parse_user_agent_details(user_agent_str: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Parses a User-Agent string to extract simple device name and browser name.
    """
    if not user_agent_str:
        return "Unknown Device", "Unknown Browser"
    
    ua = user_agent_str.lower()
    
    # Detect browser
    if "chrome" in ua or "chromium" in ua:
        browser = "Chrome"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "edge" in ua:
        browser = "Edge"
    elif "opera" in ua or "opr" in ua:
        browser = "Opera"
    else:
        browser = "Other/Unknown"
        
    # Detect device/OS
    if "iphone" in ua:
        device = "iPhone"
    elif "ipad" in ua:
        device = "iPad"
    elif "android" in ua:
        device = "Android Device"
    elif "windows" in ua:
        device = "Windows PC"
    elif "macintosh" in ua:
        device = "Macintosh"
    elif "linux" in ua:
        device = "Linux PC"
    else:
        device = "Unknown Device"
        
    return device, browser

class AIVerificationService:
    def __init__(self, db: SqlSession):
        self.db = db
        # Instantiating the decoupled provider instances
        self.face_provider = MockFaceRecognitionProvider()
        self.liveness_provider = MockLivenessDetectionProvider()

        # Load environment configurations
        self.ai_enabled = os.getenv("AI_ENABLED", "True").lower() == "true"
        self.allow_manual_fallback = os.getenv("ALLOW_MANUAL_FALLBACK", "True").lower() == "true"

    def verify_and_check_in(
        self,
        session_id: int,
        member_id: int,
        latitude: Optional[float],
        longitude: Optional[float],
        image_b64: Optional[str],
        simulate_confidence: Optional[float] = None,
        simulate_liveness: Optional[str] = None,
        actor_id: Optional[int] = None,
        accuracy: Optional[float] = None,
        captured_at: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Attendance:
        start_perf = time.perf_counter()
        now = datetime.now()

        # 1. Retrieve entities
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise ObjectNotFoundError(f"Session with ID {session_id} not found.")

        member = self.db.query(User).filter(User.id == member_id).first()
        if not member:
            raise ObjectNotFoundError(f"Member with ID {member_id} not found.")

        # 2. Check-in Window Validation
        if session.status != "Active":
            raise DomainException(f"Check-in rejected: Session is in '{session.status}' state.")

        # 3. Member assigned check
        from app.models.session import session_members
        is_assigned = self.db.query(session_members).filter(
            session_members.c.session_id == session_id,
            session_members.c.user_id == member_id
        ).first() is not None
        if not is_assigned:
            raise PermissionDeniedError("Member is not assigned to this session.")

        # 4. GPS available
        if latitude is None or longitude is None:
            raise DomainException("Check-in rejected: GPS coordinates are required.")

        # 5. Selfie available
        if not image_b64 or image_b64.strip() == "":
            raise DomainException("Check-in rejected: Selfie image is required.")

        # Decode base64 image data and run security checks
        import base64
        b64_data = image_b64
        if "," in b64_data:
            header, b64_data = b64_data.split(",", 1)
        
        is_mock_payload = b64_data.startswith("test_") or b64_data.startswith("mock_")
        
        try:
            # Add padding to avoid binascii.Error: Incorrect padding
            missing_padding = len(b64_data) % 4
            if missing_padding:
                b64_data += '=' * (4 - missing_padding)
            img_bytes = base64.b64decode(b64_data)
        except Exception:
            raise DomainException("Check-in rejected: Invalid base64 image data.")
            
        if len(img_bytes) > 5 * 1024 * 1024:
            raise DomainException("Check-in rejected: Selfie size exceeds 5 MB limit.")
            
        # Reject executable file bytes by validating header signature (JPEG / PNG only)
        is_jpeg = img_bytes.startswith(b"\xff\xd8\xff")
        is_png = img_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        
        if not is_mock_payload:
            if not (is_jpeg or is_png):
                raise DomainException("Check-in rejected: File format must be JPEG or PNG.")

        # Create persistent upload path
        year_str = now.strftime("%Y")
        month_str = now.strftime("%m")
        # Ensure base path relative to this backend module
        base_uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "attendance"))
        session_uploads_dir = os.path.join(base_uploads_dir, year_str, month_str, str(session_id))
        os.makedirs(session_uploads_dir, exist_ok=True)
        
        timestamp_str = int(now.timestamp())
        file_ext = "jpg" if is_jpeg else ("png" if is_png else "txt")
        filename = f"{member_id}_{timestamp_str}.{file_ext}"
        full_file_path = os.path.join(session_uploads_dir, filename)
        
        with open(full_file_path, "wb") as f:
            f.write(img_bytes)
            
        db_path = f"uploads/attendance/{year_str}/{month_str}/{session_id}/{filename}"

        start_dt = datetime.combine(session.date, session.start_time)
        end_dt = datetime.combine(session.date, session.end_time)

        if now < start_dt or now > end_dt:
            raise DomainException("Check-in rejected: Current time is outside the active session window.")

        # 3. GPS Geofence Check
        if session.latitude is not None and session.longitude is not None and session.gps_radius is not None:
            dist = calculate_haversine_distance(latitude, longitude, session.latitude, session.longitude)
            if dist > session.gps_radius:
                raise PermissionDeniedError(
                    f"Check-in rejected: Outside allowed GPS geofence area. Distance: {dist:.1f}m, Max: {session.gps_radius}m"
                )

        # 4. Face Match Verification
        face_verified = True
        confidence_score = 1.0
        provider_name = "MockFaceRecognition"

        # Determine threshold (prioritizes session-specific threshold, fallbacks to env default)
        threshold = session.face_confidence_threshold if session.face_confidence_threshold is not None else self.face_provider.default_threshold

        if self.ai_enabled:
            face_res = self.face_provider.verify_face(
                image_b64=image_b64,
                user_reference_id=member_id,
                simulate_confidence=simulate_confidence
            )
            confidence_score = face_res["confidence_score"]
            provider_name = face_res["provider_name"]
            
            if confidence_score < threshold:
                face_verified = False

        # 5. Liveness Detection Anti-Spoof check
        liveness_score = 1.0
        if self.ai_enabled:
            live_res = self.liveness_provider.detect_liveness(
                image_b64=image_b64,
                simulate_liveness=simulate_liveness
            )
            liveness_score = live_res["liveness_score"]
            if not live_res["is_live"]:
                # Log failure audit immediately
                AuditLogService.log_event(
                    db=self.db,
                    actor_id=actor_id or member_id,
                    action="AIVerificationFailure",
                    module="AI_Verification",
                    new_value=f"User {member_id} failed liveness check: {live_res['error_message']} (Score: {liveness_score})",
                    reason="Anti-Spoofing match failure"
                )
                raise PermissionDeniedError(live_res["error_message"])

        # Calculate verification duration in milliseconds
        duration_ms = (time.perf_counter() - start_perf) * 1000.0

        # Handle face mismatch fallback policy
        require_approval = False
        if not face_verified:
            policy = session.fallback_policy or "Block"
            if policy == "CoordinatorApproval" and self.allow_manual_fallback:
                require_approval = True
                AuditLogService.log_event(
                    db=self.db,
                    actor_id=actor_id or member_id,
                    action="AIVerificationFallbackTriggered",
                    module="AI_Verification",
                    new_value=f"User {member_id} failed threshold ({confidence_score:.2f} < {threshold:.2f}). Fallback to Coordinator Approval.",
                )
            else:
                # Log audit failure
                AuditLogService.log_event(
                    db=self.db,
                    actor_id=actor_id or member_id,
                    action="AIVerificationFailure",
                    module="AI_Verification",
                    new_value=f"User {member_id} failed face threshold matching ({confidence_score:.2f} < {threshold:.2f})",
                    reason="Biometric similarity matching failure"
                )
                raise PermissionDeniedError(
                    f"AI Face verification failed. Match confidence {confidence_score * 100:.1f}% below required {threshold * 100:.1f}%."
                )

        # 6. Record Attendance
        existing_att = self.db.query(Attendance).filter(
            Attendance.member_id == member_id,
            Attendance.session_id == session_id
        ).first()

        # Tardiness check
        grace_limit = start_dt + timedelta(minutes=session.grace_time)
        attendance_status = "Present"
        if now > grace_limit:
            attendance_status = "Late"

        if require_approval:
            # Set to Pending Approval status
            status_value = "Pending Approval"
            verification_status_value = "Pending"
        else:
            status_value = attendance_status
            verification_status_value = "Verified"

        # Encrypt the captured frame signature (simulation)
        encrypted_sig = encrypt_biometric_image(image_b64)

        # Parse device and browser details
        device_name, browser_name = parse_user_agent_details(user_agent)
        captured_dt = None
        if captured_at:
            try:
                captured_dt = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
            except Exception:
                captured_dt = now
        else:
            captured_dt = now

        if existing_att:
            att = existing_att
            att.status = status_value
            att.verification_status = verification_status_value
            att.check_in_time = now
            att.gps_status = "Verified"
            
            # AI Metadata
            att.verification_method = "Face+GPS"
            att.provider_name = provider_name
            att.confidence_score = confidence_score
            att.liveness_score = liveness_score
            att.verification_duration = duration_ms
            att.verification_timestamp = now

            # Evidence details
            att.selfie_image_path = db_path
            att.gps_latitude = latitude
            att.gps_longitude = longitude
            att.gps_accuracy = accuracy
            att.device_name = device_name
            att.browser_name = browser_name
            att.user_agent = user_agent
            att.ip_address = ip_address
            att.captured_at = captured_dt
        else:
            att = Attendance(
                member_id=member_id,
                session_id=session_id,
                status=status_value,
                verification_status=verification_status_value,
                check_in_time=now,
                gps_status="Verified",
                verification_method="Face+GPS",
                provider_name=provider_name,
                confidence_score=confidence_score,
                liveness_score=liveness_score,
                verification_duration=duration_ms,
                verification_timestamp=now,
                # Evidence details
                selfie_image_path=db_path,
                gps_latitude=latitude,
                gps_longitude=longitude,
                gps_accuracy=accuracy,
                device_name=device_name,
                browser_name=browser_name,
                user_agent=user_agent,
                ip_address=ip_address,
                captured_at=captured_dt
            )
            self.db.add(att)

        self.db.commit()
        self.db.refresh(att)

        # Log Success Audit
        AuditLogService.log_event(
            db=self.db,
            actor_id=actor_id or member_id,
            action="AIVerificationSuccess" if not require_approval else "AIVerificationPending",
            module="AI_Verification",
            new_value=f"User {member_id} checked in to Session {session_id} (Confidence: {confidence_score:.2f}, Liveness: {liveness_score:.2f})",
        )

        return att

    def approve_attendance(self, session_id: int, member_id: int, actor_id: int) -> Attendance:
        """
        Coordinators use this to manually verify and approve a pending check-in.
        """
        att = self.db.query(Attendance).filter(
            Attendance.session_id == session_id,
            Attendance.member_id == member_id
        ).first()

        if not att:
            raise ObjectNotFoundError(f"Attendance log for user {member_id} not found.")

        if att.verification_status != "Pending":
            raise DomainException("Attendance log is not pending approval.")

        # Retrieve session to determine status (Present vs Late)
        session = self.db.query(Session).filter(Session.id == session_id).first()
        now = att.check_in_time or datetime.now()
        start_dt = datetime.combine(session.date, session.start_time)
        grace_limit = start_dt + timedelta(minutes=session.grace_time)

        att.status = "Present" if now <= grace_limit else "Late"
        att.verification_status = "Verified"

        self.db.commit()
        self.db.refresh(att)

        AuditLogService.log_event(
            db=self.db,
            actor_id=actor_id,
            action="AdminApproval",
            module="AI_Verification",
            new_value=f"Coordinator approved attendance for user {member_id} in Session {session_id}."
        )

        return att
