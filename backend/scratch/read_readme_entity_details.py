import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

readme_path = r"c:\Users\Shiva\OneDrive\Desktop\Attendance-Platform\Attendence-Intelligence-Platform\README.md"

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's locate lines by line number or regex
# Let's search for lines containing these exact headers
headers_to_find = [
    "# Organization Information",
    "# Department Information",
    "# Team Information",
    "# Member Profile",
    "# Session Information",
    "# Attendance Record",
    "# Activity Information",
    "# Audit Record"
]

lines = content.splitlines()
for h in headers_to_find:
    found_idx = -1
    for i, line in enumerate(lines):
        if h.lower() in line.lower() and line.strip().startswith('#'):
            found_idx = i
            break
    if found_idx != -1:
        print("="*80)
        print(f"HEADER: {lines[found_idx]}")
        print("="*80)
        # Print next 40 lines
        print("\n".join(lines[found_idx:found_idx+40]))
        print("\n...\n")
