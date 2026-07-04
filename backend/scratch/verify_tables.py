import sys
import os
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

def verify_tables():
    engine = create_engine(settings.DATABASE_URL)
    
    print("Fetching tables list from PostgreSQL 'public' schema...")
    query_tables = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """
    
    with engine.connect() as conn:
        tables = conn.execute(text(query_tables)).fetchall()
        table_names = [t[0] for t in tables]
        
        print(f"Total tables found: {len(table_names)}")
        for name in table_names:
            print(f" - {name}")
            
        print("\nVerifying Alembic Version:")
        alembic_ver = conn.execute(text("SELECT version_num FROM alembic_version;")).fetchone()
        print(f"Current Alembic Revision: {alembic_ver[0] if alembic_ver else 'None'}")
        
        print("\nVerifying Index Count:")
        query_indexes = """
            SELECT tablename, indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            ORDER BY tablename, indexname;
        """
        indexes = conn.execute(text(query_indexes)).fetchall()
        print(f"Total indexes found: {len(indexes)}")
        # Print a few major index details
        for idx in indexes[:15]:
            print(f" - Table '{idx[0]}': index '{idx[1]}'")
        if len(indexes) > 15:
            print("   ... (remaining indexes omitted for brevity)")

if __name__ == "__main__":
    verify_tables()
