import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text

passwords = ["admin", "root", "", "password123", "shiva", "postgres", "password"]
db_names = ["attendance_platform", "postgres"]

for db_name in db_names:
    for pwd in passwords:
        url = f"postgresql://postgres:{pwd}@localhost:5432/{db_name}"
        try:
            engine = create_engine(url, connect_args={'connect_timeout': 2})
            with engine.connect() as conn:
                res = conn.execute(text("SELECT 1")).fetchone()[0]
                print(f"SUCCESS: Connected to '{db_name}' with password '{pwd}'! Result: {res}")
                sys.exit(0)
        except Exception as e:
            # check if it's database not exists vs password fail
            msg = str(e)
            if "database" in msg and "does not exist" in msg:
                print(f"DATABASE EXISTS FAIL: password '{pwd}' is CORRECT, but database '{db_name}' does not exist.")
                sys.exit(0)
            # print(f"Failed {pwd} for {db_name}: {msg[:100]}")
            continue

print("All common password attempts failed.")
