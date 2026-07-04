import sys
import os
import subprocess
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.models import Base

def count_records(engine):
    counts = {}
    with engine.connect() as conn:
        for table_name in Base.metadata.tables.keys():
            res = conn.execute(text(f"SELECT count(*) FROM {table_name}")).fetchone()[0]
            counts[table_name] = res
    return counts

def verify_seeding():
    engine = create_engine(settings.DATABASE_URL)
    
    print("Step 1: Counting baseline records in PostgreSQL...")
    initial_counts = count_records(engine)
    for table, count in initial_counts.items():
        print(f" - Table '{table}': {count} records")
        
    # Verify we seeded the default users
    assert initial_counts["users"] >= 5, "Should have seeded at least 5 users."
    assert initial_counts["organizations"] == 1, "Should have seeded 1 organization."
    assert initial_counts["departments"] == 2, "Should have seeded 2 departments."
    assert initial_counts["teams"] == 1, "Should have seeded 1 team."
    assert initial_counts["sessions"] == 3, "Should have seeded 3 sessions."
    
    print("\nStep 2: Triggering seed script again to verify idempotency...")
    # Run seed script
    res = subprocess.run(
        [r".venv\Scripts\python.exe", r"app\utils\seed.py"],
        capture_output=True,
        text=True
    )
    if res.returncode != 0:
        print("Re-seeding failed!")
        print(res.stderr)
        sys.exit(1)
    
    print("Re-seeding completed. Counting records again...")
    post_counts = count_records(engine)
    
    idempotent = True
    for table, count in post_counts.items():
        diff = count - initial_counts[table]
        # AuditLog represents log history so it might increase by 1 if logged again, but let's check
        if table != "audit_logs" and diff != 0:
            print(f"WARNING: Table '{table}' increased by {diff} records! Seeding is NOT idempotent!")
            idempotent = False
        else:
            print(f" - Table '{table}': {count} records (Change: {diff})")
            
    if idempotent:
        print("\nSUCCESS: Database seeding is verified and confirmed IDEMPOTENT!")
    else:
        print("\nFAILURE: Seeding is not idempotent.")
        sys.exit(1)

if __name__ == "__main__":
    # We must be in backend directory to run this properly
    verify_seeding()
