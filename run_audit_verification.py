import sys
import os
import json
import sqlite3
import pytest
from pathlib import Path

basedir = Path(__file__).resolve().parent
sys.path.insert(0, str(basedir))

def run_tests():
    print("=" * 60)
    print("RUNNING AUTOMATED PYTEST SUITE (15 TEST CASES)")
    print("=" * 60)
    result_code = pytest.main(['-v', 'tests'])
    print(f"\nPytest Exit Code: {result_code} (0 = All Passed)")
    return result_code == 0

def check_db_duplicates_and_schema(dry_run=False):
    print("\n" + "=" * 60)
    print("DATABASE INTEGRITY, MIGRATION & BACKUP VERIFICATION")
    print("=" * 60)
    
    db_paths = [
        basedir / 'app.db',
        basedir / 'instance' / 'app.db',
        basedir / 'app' / 'app.db'
    ]
    
    found_db = False
    for db_path in db_paths:
        if db_path.exists():
            found_db = True
            print(f"Inspecting physical database file: {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Query duplicate request rows
            cursor.execute("""
                SELECT id, sender_id, receiver_id, skill_id, status, created_at
                FROM requests
                WHERE (sender_id, receiver_id, skill_id, status) IN (
                    SELECT sender_id, receiver_id, skill_id, status
                    FROM requests
                    GROUP BY sender_id, receiver_id, skill_id, status
                    HAVING COUNT(*) > 1
                )
                ORDER BY sender_id, receiver_id, skill_id, created_at ASC
            """)
            duplicate_rows = cursor.fetchall()
            
            if duplicate_rows:
                print(f"⚠️ FOUND {len(duplicate_rows)} DUPLICATE REQUEST ROWS across table!")
                # Export backup JSON before any cleanup
                backup_file = basedir / 'backup_duplicate_requests.json'
                backup_data = [
                    {
                        'id': r[0],
                        'sender_id': r[1],
                        'receiver_id': r[2],
                        'skill_id': r[3],
                        'status': r[4],
                        'created_at': str(r[5])
                    } for r in duplicate_rows
                ]
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2)
                print(f"📁 Safely backed up duplicate rows to: {backup_file}")
                
                if not dry_run:
                    # Keep oldest record (MIN id), delete excess duplicates
                    cursor.execute("""
                        DELETE FROM requests
                        WHERE id NOT IN (
                            SELECT MIN(id)
                            FROM requests
                            GROUP BY sender_id, receiver_id, skill_id, status
                        )
                    """)
                    conn.commit()
                    print("✅ Duplicates cleaned successfully (oldest original record retained).")
            else:
                print("✅ Data Pre-check: Zero duplicate request rows found in database.")
                
            # Verify table schema & constraint consistency
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='requests'")
            row = cursor.fetchone()
            if row and row[0]:
                sql_schema = row[0]
                print(f"\nPhysical Requests Table Schema:\n{sql_schema}")
                if 'uq_pending_request' in sql_schema:
                    print("✅ Alembic migration constraint 'uq_pending_request' is present in physical schema.")
                else:
                    print("Applying Alembic-matching unique index 'uq_pending_request'...")
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_pending_request ON requests (sender_id, receiver_id, skill_id, status)")
                    conn.commit()
                    print("✅ Unique index 'uq_pending_request' applied cleanly.")
            conn.close()
            
    if not found_db:
        print("ℹ️ No physical SQLite file found prior to initialization. DB initializes clean.")

if __name__ == '__main__':
    dry_run_mode = '--dry-run' in sys.argv
    test_success = run_tests()
    check_db_duplicates_and_schema(dry_run=dry_run_mode)
    if not test_success:
        sys.exit(1)
