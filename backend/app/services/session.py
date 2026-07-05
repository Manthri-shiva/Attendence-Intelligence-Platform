from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session as SqlSession
from app.models.session import Session
from app.models.user import User
from app.repositories.session import SessionRepository
from app.core.domain_exceptions import (
    DomainException, ObjectNotFoundError, DuplicateRecordError, PermissionDeniedError
)
from app.services.audit_log import AuditLogService
from app.schemas.session import SessionCreate, SessionUpdate

class SessionService:
    def __init__(self, db: SqlSession):
        self.db = db
        self.repo = SessionRepository(db)

    def create_session(self, schema: SessionCreate, actor_id: Optional[int] = None) -> Session:
        # Validate parent coordinator existence
        if schema.coordinator_id:
            coordinator = self.db.query(User).filter(User.id == schema.coordinator_id).first()
            if not coordinator:
                raise ObjectNotFoundError(f"Coordinator with ID {schema.coordinator_id} not found.")

        # Create session database record
        session_data = schema.model_dump()
        session = Session(**session_data)
        session.status = "Draft"
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        AuditLogService.log_event(
            db=self.db,
            actor_id=actor_id,
            action="Create",
            module="Session",
            new_value=f"Session: {session.name} ({session.id})"
        )
        return session

    def get_session(self, session_id: int) -> Session:
        session = self.repo.get_by_id(session_id)
        if not session:
            raise ObjectNotFoundError(f"Session with ID {session_id} not found.")
        return session

    def get_sessions(
        self,
        *,
        skip: int = 0,
        limit: int = 10,
        q: Optional[str] = None,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        coordinator_id: Optional[int] = None,
        filter_date: Optional[date] = None,
        status: Optional[str] = None,
    ) -> List[Session]:
        return self.repo.get_sessions_filtered(
            skip=skip,
            limit=limit,
            q=q,
            organization_id=organization_id,
            department_id=department_id,
            coordinator_id=coordinator_id,
            filter_date=filter_date,
            status=status
        )

    def count_sessions(
        self,
        *,
        q: Optional[str] = None,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        coordinator_id: Optional[int] = None,
        filter_date: Optional[date] = None,
        status: Optional[str] = None,
    ) -> int:
        return self.repo.count_sessions_filtered(
            q=q,
            organization_id=organization_id,
            department_id=department_id,
            coordinator_id=coordinator_id,
            filter_date=filter_date,
            status=status
        )

    def update_session(
        self,
        session_id: int,
        schema: SessionUpdate,
        actor_id: Optional[int] = None,
        check_updated_at: Optional[datetime] = None
    ) -> Session:
        session = self.get_session(session_id)

        # Optimistic Concurrency Control
        if check_updated_at and session.updated_at != check_updated_at:
            raise DomainException("Session has been modified by another request. Please refresh and try again.")

        # Once a session is Active or beyond, prevent certain structural changes
        locked_states = ["Active", "Paused", "Completed", "Archived"]
        if session.status in locked_states:
            # Check if attempting to modify locked fields
            update_data = schema.model_dump(exclude_unset=True)
            locked_fields = ["organization_id", "department_id", "date", "start_time", "end_time"]
            for field in locked_fields:
                if field in update_data and update_data[field] != getattr(session, field):
                    raise PermissionDeniedError(f"Cannot modify field '{field}' once session is {session.status}.")

        # Apply updates
        update_data = schema.model_dump(exclude_unset=True)
        
        # Check coordinator validation if updating
        if "coordinator_id" in update_data and update_data["coordinator_id"]:
            coordinator = self.db.query(User).filter(User.id == update_data["coordinator_id"]).first()
            if not coordinator:
                raise ObjectNotFoundError(f"Coordinator with ID {update_data['coordinator_id']} not found.")

        # Apply update payload fields
        for key, val in update_data.items():
            setattr(session, key, val)

        self.db.commit()
        self.db.refresh(session)

        AuditLogService.log_event(
            db=self.db,
            actor_id=actor_id,
            action="Update",
            module="Session",
            new_value=f"Session updated: {session.id}"
        )
        return session

    def delete_session(self, session_id: int, actor_id: Optional[int] = None) -> None:
        session = self.get_session(session_id)
        if session.status in ["Active", "Paused", "Completed"]:
            raise PermissionDeniedError(f"Cannot delete session in state '{session.status}'.")

        self.db.delete(session)
        self.db.commit()

        AuditLogService.log_event(
            db=self.db,
            actor_id=actor_id,
            action="Delete",
            module="Session",
            old_value=f"Deleted session ID: {session_id}"
        )

    def transition_state(self, session_id: int, target_status: str, actor_id: Optional[int] = None) -> Session:
        session = self.get_session(session_id)
        current = session.status

        # Define valid transitions
        valid_transitions = {
            "Draft": ["Scheduled", "Cancelled"],
            "Scheduled": ["Active", "Cancelled"],
            "Active": ["Paused", "Completed"],
            "Paused": ["Active", "Completed"],
            "Completed": ["Archived"],
            "Cancelled": ["Archived"],
            "Archived": [] # Terminal state
        }

        if target_status not in valid_transitions.get(current, []):
            raise DomainException(f"Invalid state transition from '{current}' to '{target_status}'.")

        # Once session is Active or beyond, we locked participant changes as well
        # Note: transitions are allowed, but we record appropriate timestamp
        now = datetime.now()
        session.status = target_status

        if target_status == "Scheduled":
            session.scheduled_at = now
        elif target_status == "Active":
            # If transitioned from Paused to Active, it counts as Resumed timestamp
            if current == "Paused":
                session.resumed_at = now
            else:
                session.started_at = now
        elif target_status == "Paused":
            session.paused_at = now
        elif target_status == "Completed":
            session.completed_at = now
        elif target_status == "Archived" or target_status == "Cancelled":
            session.archived_at = now

        self.db.commit()
        self.db.refresh(session)

        AuditLogService.log_event(
            db=self.db,
            actor_id=actor_id,
            action=f"State:{target_status}",
            module="Session",
            new_value=f"Session transitioned to {target_status}"
        )
        return session

    def assign_members(self, session_id: int, user_ids: List[int], actor_id: Optional[int] = None) -> Session:
        session = self.get_session(session_id)

        # Prevent participant scope updates on Active/Completed/Archived
        if session.status in ["Active", "Paused", "Completed", "Archived"]:
            raise PermissionDeniedError(f"Cannot update participant scope once session is {session.status}.")

        # Capacity Check
        current_count = len(session.assigned_members)
        if session.capacity is not None:
            # Check how many unique new members we are attempting to add
            existing_ids = {m.id for m in session.assigned_members}
            new_ids = [uid for uid in user_ids if uid not in existing_ids]
            if current_count + len(new_ids) > session.capacity:
                raise DomainException(
                    f"Assigning members would exceed session capacity limit of {session.capacity}."
                )

        # Retrieve and assign new members
        for uid in user_ids:
            # Check if user already assigned
            if any(m.id == uid for m in session.assigned_members):
                continue # Prevent duplicate assignments gracefully

            user_obj = self.db.query(User).filter(User.id == uid).first()
            if not user_obj:
                raise ObjectNotFoundError(f"User with ID {uid} not found.")

            session.assigned_members.append(user_obj)
            
            AuditLogService.log_event(
                db=self.db,
                actor_id=actor_id,
                action="Assign",
                module="Session",
                new_value=f"Assigned User ID {uid} to Session ID {session_id}"
            )

        self.db.commit()
        self.db.refresh(session)
        return session

    def remove_members(self, session_id: int, user_ids: List[int], actor_id: Optional[int] = None) -> Session:
        session = self.get_session(session_id)

        if session.status in ["Active", "Paused", "Completed", "Archived"]:
            raise PermissionDeniedError(f"Cannot update participant scope once session is {session.status}.")

        for uid in user_ids:
            user_obj = next((m for m in session.assigned_members if m.id == uid), None)
            if user_obj:
                session.assigned_members.remove(user_obj)
                AuditLogService.log_event(
                    db=self.db,
                    actor_id=actor_id,
                    action="Unassign",
                    module="Session",
                    old_value=f"Removed User ID {uid} from Session ID {session_id}"
                )

        self.db.commit()
        self.db.refresh(session)
        return session
