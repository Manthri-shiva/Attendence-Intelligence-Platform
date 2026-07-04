import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.models import Base, User, Organization, Department, Team, Session, Attendance, Activity, Notification, Report, AuditLog
    print("Success: All SQLAlchemy models imported correctly!")
    print("Mapped Tables in Metadata:")
    for table_name in Base.metadata.tables.keys():
        print(f" - {table_name}")
except Exception as e:
    print("Failed to import models:")
    print(e)
    sys.exit(1)
