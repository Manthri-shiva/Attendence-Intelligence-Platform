import os
import sys

for k, v in os.environ.items():
    if any(keyword in k.lower() for keyword in ['db', 'postgres', 'url', 'pass', 'sec']):
        print(f"{k} = {v}")
