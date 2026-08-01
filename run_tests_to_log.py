import io
import sys
import pytest
from pathlib import Path

basedir = Path(__file__).resolve().parent
sys.path.insert(0, str(basedir))

# Redirect stdout to capture complete pytest output
output_buffer = io.StringIO()
old_stdout = sys.stdout
sys.stdout = output_buffer

try:
    exit_code = pytest.main(['-v', 'tests'])
finally:
    sys.stdout = old_stdout

captured_output = output_buffer.getvalue()

log_file = basedir / 'tests_output.log'
with open(log_file, 'w', encoding='utf-8') as f:
    f.write(f"Pytest Exit Code: {exit_code}\n")
    f.write("=" * 60 + "\n")
    f.write(captured_output)

print(f"Tests execution complete. Log written to {log_file}")
