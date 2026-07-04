import sys
import os
from sqlalchemy import create_engine, text

passwords = [
    "Shiva", "shiva", "Shiva@123", "shiva123", "postgres123", "Admin@123", 
    "admin123", "123456", "12345678", "password", "postgres", "admin", "root", ""
]

for pwd in passwords:
    url = f"postgresql://postgres:{pwd}@127.0.0.1:5432/postgres"
    try:
        engine = create_engine(url, connect_args={'connect_timeout': 1})
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1")).fetchone()[0]
            print(f"SUCCESS: Connected with password '{pwd}'!")
            sys.exit(0)
    except Exception as e:
        continue

print("Failed to authenticate with all common patterns.")
sys.exit(1)
