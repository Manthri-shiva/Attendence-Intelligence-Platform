import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.database import engine

def test_connection():
    print(f"Connecting to database at url: {engine.url}")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Successfully connected! Output:", result.fetchone()[0])
    except Exception as e:
        print("Database connection failed!")
        print(e)

if __name__ == "__main__":
    test_connection()
