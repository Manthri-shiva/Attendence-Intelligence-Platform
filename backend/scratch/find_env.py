import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

root_dir = r"c:\Users\Shiva\OneDrive\Desktop\Attendance-Platform"
for root, dirs, files in os.walk(root_dir):
    # prune venv and git
    dirs[:] = [d for d in dirs if d not in ['.venv', '.git', 'node_modules']]
    for f in files:
        if f.endswith('.env') or f == '.env':
            print(os.path.join(root, f))
