import os
from pathlib import Path

basedir = Path(__file__).resolve().parent

root_files = [
    basedir / 'run_audit_verification.py',
    basedir / 'run_dynamic_verification.py',
    basedir / 'run_linter_checks.py',
    basedir / 'run_tests_to_log.py'
]

for f in root_files:
    if f.exists():
        os.remove(f)
        print(f"Removed root duplicate: {f.name}")

print("Root script cleanup complete.")
