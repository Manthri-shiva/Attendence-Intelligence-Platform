import re
import sys

# Ensure UTF-8 stdout printing
sys.stdout.reconfigure(encoding='utf-8')

readme_path = r"c:\Users\Shiva\OneDrive\Desktop\Attendance-Platform\Attendence-Intelligence-Platform\README.md"

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all headers in the readme
headers = re.findall(r'^(#+\s+.*)$', content, re.MULTILINE)
print(f"Found {len(headers)} headers.")
print("Headers containing database, postgres, schema, model, phase, milestone or relationship:")
for h in headers:
    hl = h.lower()
    if any(kw in hl for kw in ['database', 'postgres', 'schema', 'model', 'phase', 'milestone', 'relationship']):
        print(h)

# Search for specific sections that mention database/schema design or tables
# We can find sections starting with ## and print them if they relate to db
print("\nPrinting occurrences of key phrases:")
for line_no, line in enumerate(content.splitlines(), 1):
    if "database" in line.lower() or "postgres" in line.lower() or "schema" in line.lower():
        if "integration" in line.lower() or "phase" in line.lower() or "table" in line.lower() or "relationship" in line.lower():
            print(f"Line {line_no}: {line}")
