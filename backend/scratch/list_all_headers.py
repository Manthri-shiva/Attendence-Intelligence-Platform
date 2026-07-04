import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

readme_path = r"c:\Users\Shiva\OneDrive\Desktop\Attendance-Platform\Attendence-Intelligence-Platform\README.md"

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.splitlines()
for i, line in enumerate(lines, 1):
    if line.strip().startswith('#'):
        print(f"Line {i}: {line}")
