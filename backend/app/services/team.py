from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.team import TeamRepository
from app.repositories.user import UserRepository
from app.repositories.department import DepartmentRepository
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate
from app.core.domain_exceptions import DuplicateRecordError, ObjectNotFoundError
from app.services.audit_log import AuditLogService

class TeamService:
    """
    Business logic layer for managing Teams.
    """
    def __init__(self, team_repo: TeamRepository, user_repo: UserRepository, dept_repo: DepartmentRepository):
        self.team_repo = team_repo
        self.user_repo = user_repo
        self.dept_repo = dept_repo

    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Fetch team by id."""
        return self.team_repo.get_by_id(team_id)

    def get_all_teams(self, skip: int = 0, limit: int = 100) -> List[Team]:
        """Fetch all teams with pagination and eager relationships."""
        return self.team_repo.get_all_with_relations(skip=skip, limit=limit)

    def get_teams_by_dept(self, department_id: int, skip: int = 0, limit: int = 100) -> List[Team]:
        """Fetch teams filtered by department."""
        return self.team_repo.get_by_dept(department_id, skip=skip, limit=limit)

    def search_teams(self, query: str, department_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Team]:
        """Fetch teams matching search text, optionally scoped to a department."""
        q = self.team_repo.db.query(Team)
        if department_id is not None:
            q = q.filter(Team.department_id == department_id)
        q = q.filter(Team.name.ilike(f"%{query}%"))
        return q.offset(skip).limit(limit).all()

    def count_teams(self, query: Optional[str] = None, department_id: Optional[int] = None) -> int:
        """Count matching teams for pagination."""
        q = self.team_repo.db.query(Team)
        if department_id is not None:
            q = q.filter(Team.department_id == department_id)
        if query:
            q = q.filter(Team.name.ilike(f"%{query}%"))
        return q.count()

    def create_team(self, db: Session, team_in: TeamCreate, actor_id: Optional[int]) -> Team:
        """Create team, validating department and leader existence, duplicate names, and logging audit."""
        # Validate department exists
        dept = self.dept_repo.get_by_id(team_in.department_id)
        if not dept:
            raise ObjectNotFoundError(f"Department with ID {team_in.department_id} does not exist.")

        # Prevent duplicate team name in the same department
        existing = self.team_repo.get_by_name_and_dept(team_in.name, team_in.department_id)
        if existing:
            raise DuplicateRecordError(f"A team named '{team_in.name}' already exists in this department.")

        # Validate leader exists if supplied
        if team_in.leader_id:
            leader = self.user_repo.get_by_id(team_in.leader_id)
            if not leader:
                raise ObjectNotFoundError(f"Team Leader User with ID {team_in.leader_id} not found.")

        team_dict = team_in.model_dump()
        new_team = self.team_repo.create(team_dict)

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Create",
            module="Team",
            new_value=f"ID: {new_team.id}, Name: {new_team.name}, DeptID: {new_team.department_id}",
            reason="Team created"
        )
        return new_team

    def update_team(self, db: Session, team_id: int, team_in: TeamUpdate, actor_id: Optional[int]) -> Team:
        """Update team, enforcing constraints and logging audit."""
        team = self.team_repo.get_by_id(team_id)
        if not team:
            raise ObjectNotFoundError(f"Team with ID {team_id} not found.")

        team_in_dict = team_in.model_dump(exclude_unset=True)

        # Check duplicate name within department if name changes
        new_name = team_in_dict.get("name")
        target_dept_id = team_in_dict.get("department_id", team.department_id)

        if (new_name and new_name != team.name) or (target_dept_id != team.department_id):
            check_name = new_name or team.name
            existing = self.team_repo.get_by_name_and_dept(check_name, target_dept_id)
            if existing and existing.id != team.id:
                raise DuplicateRecordError(f"A team named '{check_name}' already exists in the target department.")

        # Validate leader
        if "leader_id" in team_in_dict and team_in_dict["leader_id"] is not None:
            leader = self.user_repo.get_by_id(team_in_dict["leader_id"])
            if not leader:
                raise ObjectNotFoundError(f"Team Leader User with ID {team_in_dict['leader_id']} not found.")

        old_val = f"Name: {team.name}, DeptID: {team.department_id}, LeaderID: {team.leader_id}, Status: {team.status}"
        updated_team = self.team_repo.update(team, team_in_dict)

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Update",
            module="Team",
            old_value=old_val,
            new_value=f"Name: {updated_team.name}, LeaderID: {updated_team.leader_id}, Status: {updated_team.status}",
            reason="Team configurations updated"
        )
        return updated_team

    def delete_team(self, db: Session, team_id: int, actor_id: Optional[int]) -> Team:
        """Delete/Deactivate team and write audit log."""
        team = self.team_repo.get_by_id(team_id)
        if not team:
            raise ObjectNotFoundError(f"Team with ID {team_id} not found.")

        old_val = f"Name: {team.name}, Status: {team.status}"
        updated_team = self.team_repo.update(team, {"status": "Inactive"})

        # Audit Logging
        AuditLogService.log_event(
            db=db,
            actor_id=actor_id,
            action="Deactivate",
            module="Team",
            old_value=old_val,
            new_value=f"Status: {updated_team.status}",
            reason="Team marked Inactive (soft-deleted)"
        )
        return updated_team
