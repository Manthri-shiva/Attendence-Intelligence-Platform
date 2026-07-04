import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

readme_path = r"c:\Users\Shiva\OneDrive\Desktop\Attendance-Platform\Attendence-Intelligence-Platform\README.md"

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find sections
# We'll split the file by H1 headers (lines starting with '# ')
parts = re.split(r'^(?=#\s)', content, flags=re.MULTILINE)

for part in parts:
    first_line = part.splitlines()[0] if part.splitlines() else ""
    if "54. Database Architecture" in first_line or "Entity Relationships" in first_line:
        print("="*60)
        print(f"SECTION: {first_line}")
        print("="*60)
        print(part)
        print("\n" + "="*60 + "\n")
