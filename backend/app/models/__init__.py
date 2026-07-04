# Models package initialization
# All database models will be registered here to support Alembic autogeneration imports.
from app.core.database import Base
from app.models.user import User, UserRole

