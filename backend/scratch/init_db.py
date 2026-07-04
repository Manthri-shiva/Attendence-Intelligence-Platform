import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

def init_database():
    # Parse current DATABASE_URL
    original_url = settings.DATABASE_URL
    print(f"Target connection URL: {original_url}")
    
    # Connect to default 'postgres' database to check/create target database
    # Extract connection parameters
    db_url = URL.create(
        drivername="postgresql",
        username=settings.DATABASE_URL.split("://")[1].split(":")[0],
        password=settings.DATABASE_URL.split(":")[-1].split("@")[0] if "@" in settings.DATABASE_URL.split(":")[-1] else settings.DATABASE_URL.split("://")[1].split(":")[1].split("@")[0],
        host=settings.DATABASE_URL.split("@")[1].split(":")[0],
        port=int(settings.DATABASE_URL.split("@")[1].split(":")[1].split("/")[0]),
        database="postgres"
    )
    
    print(f"Connecting to default system database 'postgres' to verify target database...")
    try:
        temp_engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
        with temp_engine.connect() as conn:
            # Check if target database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'attendance_platform'")
            ).fetchone()
            
            if not result:
                print("Database 'attendance_platform' does not exist. Creating database...")
                conn.execute(text("CREATE DATABASE attendance_platform"))
                print("Database 'attendance_platform' created successfully.")
            else:
                print("Database 'attendance_platform' already exists.")
    except Exception as e:
        print("Failed to check/create database using 'postgres' default database:")
        print(e)
        sys.exit(1)

    # Now verify connection to the target database
    print("\nVerifying connection to 'attendance_platform' database...")
    try:
        engine = create_engine(original_url)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1")).fetchone()[0]
            print(f"Verification Success! Connection test returned: {res}")
    except Exception as e:
        print("Failed to connect to the target database:")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    init_database()
