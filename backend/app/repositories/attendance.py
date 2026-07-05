from sqlalchemy.orm import Session as SqlSession, joinedload
from typing import List, Optional
from app.repositories.base import BaseRepository
from app.models.attendance import Attendance

class AttendanceRepository(BaseRepository[Attendance]):
    def __init__(self, db: SqlSession):
        super().__init__(db, Attendance)

    def get_by_member_and_session(self, member_id: int, session_id: int) -> Optional[Attendance]:
        return self.db.query(Attendance).filter(
            Attendance.member_id == member_id,
            Attendance.session_id == session_id
        ).first()

    def get_session_attendances(self, session_id: int) -> List[Attendance]:
        return self.db.query(Attendance).filter(
            Attendance.session_id == session_id
        ).options(
            joinedload(Attendance.member)
        ).all()
