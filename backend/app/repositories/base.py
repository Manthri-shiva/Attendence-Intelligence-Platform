from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Base Repository containing common CRUD logic to eliminate duplication.
    """
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Retrieve a record by primary key id."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Retrieve records with optional pagination offsets."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Insert a new model record into the database."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """Update fields of an existing model record."""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: Any) -> Optional[ModelType]:
        """Delete a record by primary key id."""
        db_obj = self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
        return db_obj
