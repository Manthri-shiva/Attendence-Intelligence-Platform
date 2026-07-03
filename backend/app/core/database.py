from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Synchronous connection engine (PostgreSQL default driver: psycopg2)
# If transitioning to async later, this url will change to postgresql+asyncpg:// 
# and utilize create_async_engine and AsyncSession.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative base class for models mapping to PostgreSQL tables
Base = declarative_base()

def get_db():
    """
    FastAPI dependency that yields a database session.
    Automatically closes the session once the request is complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
