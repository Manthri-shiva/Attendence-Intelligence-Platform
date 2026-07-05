from sqlalchemy.orm import Session as SqlSession, joinedload, selectinload
from sqlalchemy import or_
from typing import List, Tuple, Optional
from datetime import date
from app.repositories.base import BaseRepository
from app.models.session import Session

class SessionRepository(BaseRepository[Session]):
    def __init__(self, db: SqlSession):
        super().__init__(db, Session)

    def get_sessions_filtered(
        self,
        *,
        skip: int = 0,
        limit: int = 10,
        q: Optional[str] = None,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        coordinator_id: Optional[int] = None,
        filter_date: Optional[date] = None,
        status: Optional[str] = None,
    ) -> List[Session]:
        query = self.db.query(Session)

        # Apply Scoped Filters
        if organization_id is not None:
            query = query.filter(Session.organization_id == organization_id)
        if department_id is not None:
            query = query.filter(Session.department_id == department_id)
        if team_id is not None:
            # Note: since team assignments are at the user level, sessions are assigned to departments.
            # However, if we filter sessions by team, we can filter for sessions whose department matches the team's department.
            # Let's support department_id as the primary structural link, but if team_id is provided, we can filter by that.
            pass
        if coordinator_id is not None:
            query = query.filter(Session.coordinator_id == coordinator_id)
        if filter_date is not None:
            query = query.filter(Session.date == filter_date)
        if status is not None:
            query = query.filter(Session.status == status)

        # Text search matching session name or description
        if q:
            search_pattern = f"%{q}%"
            query = query.filter(
                or_(
                    Session.name.ilike(search_pattern),
                    Session.description.ilike(search_pattern)
                )
            )

        # Eager Load relationships to avoid N+1 queries
        query = query.options(
            joinedload(Session.coordinator),
            joinedload(Session.department),
            joinedload(Session.organization),
            selectinload(Session.assigned_members)
        )

        return query.order_by(Session.date.desc(), Session.start_time.desc()).offset(skip).limit(limit).all()

    def count_sessions_filtered(
        self,
        *,
        q: Optional[str] = None,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        coordinator_id: Optional[int] = None,
        filter_date: Optional[date] = None,
        status: Optional[str] = None,
    ) -> int:
        query = self.db.query(Session)

        if organization_id is not None:
            query = query.filter(Session.organization_id == organization_id)
        if department_id is not None:
            query = query.filter(Session.department_id == department_id)
        if coordinator_id is not None:
            query = query.filter(Session.coordinator_id == coordinator_id)
        if filter_date is not None:
            query = query.filter(Session.date == filter_date)
        if status is not None:
            query = query.filter(Session.status == status)

        if q:
            search_pattern = f"%{q}%"
            query = query.filter(
                or_(
                    Session.name.ilike(search_pattern),
                    Session.description.ilike(search_pattern)
                )
            )

        return query.count()
