# This verification script has been moved to scripts/run_audit_verification.py
from scripts.run_audit_verification import *
if __name__ == '__main__':
    import sys, subprocess
    subprocess.run([sys.executable, 'scripts/run_audit_verification.py'] + sys.argv[1:])
