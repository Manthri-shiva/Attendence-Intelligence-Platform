from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

class AuditLogService:
    """
    Service layer for writing audit logs.
    """
    @staticmethod
    def log_event(
        db: Session,
        actor_id: Optional[int],
        action: str,
        module: str,
        device: Optional[str] = None,
        ip_address: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        reason: Optional[str] = None
    ) -> AuditLog:
        """Create and commit an audit log entry."""
        log_entry = AuditLog(
            actor_id=actor_id,
            action=action,
            module=module,
            device=device,
            ip_address=ip_address,
            old_value=old_value,
            new_value=new_value,
            reason=reason
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
