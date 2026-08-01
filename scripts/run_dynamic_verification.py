import io
import sys
import os
import json
import pytest
from pathlib import Path

basedir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(basedir))

from app import create_app
from app.extensions import db
from app.models import User, Skill, Request, Rating, Chat, Message, LearningHistory

def execute_dynamic_audit():
    report_lines = []
    def log(msg=""):
        print(msg)
        report_lines.append(msg)

    log("=" * 80)
    log("DYNAMIC VERIFICATION AUDIT & RE-EVALUATION REPORT")
    log("=" * 80)

    log("\n[STEP 0] STANDING UP LIVE APPLICATION INSTANCE")
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    with app.app_context():
        db.create_all()

        user_a = User.query.filter_by(username='user_a').first()
        if not user_a:
            user_a = User(username='user_a', email='user_a@example.com')
            user_a.set_password('Password123!')
            db.session.add(user_a)

        user_b = User.query.filter_by(username='user_b').first()
        if not user_b:
            user_b = User(username='user_b', email='user_b@example.com')
            user_b.set_password('Password123!')
            db.session.add(user_b)

        admin = User.query.filter_by(username='admin_user').first()
        if not admin:
            admin = User(username='admin_user', email='admin@example.com', is_admin=True)
            admin.set_password('AdminPassword123!')
            db.session.add(admin)

        db.session.commit()

        user_a_id = user_a.id
        user_b_id = user_b.id
        admin_id = admin.id

        res_index = client.get('/')
        log(f"LITERAL GET / -> Status Code: {res_index.status_code}")
        assert res_index.status_code == 200

        # Session Security Check
        c_a = app.test_client()
        res_login_a = c_a.post('/auth/login', data={'username_or_email': 'user_a@example.com', 'password': 'Password123!'}, follow_redirects=False)
        set_cookie_a = res_login_a.headers.get_all('Set-Cookie')
        log(f"Set-Cookie Header: {set_cookie_a}")

        # IDOR Skills Check
        skill_a = Skill(user_id=user_a_id, name='Python Mastery', category='Programming & Tech', proficiency_level='Expert')
        db.session.add(skill_a)
        db.session.commit()

        c_b = app.test_client()
        c_b.post('/auth/login', data={'username_or_email': 'user_b@example.com', 'password': 'Password123!'}, follow_redirects=True)
        res_idor = c_b.post(f'/skills/{skill_a.id}/edit', data={'name': 'Hacked'}, follow_redirects=False)
        log(f"IDOR Skill Edit Status: {res_idor.status_code}")

        # Pytest
        test_buf = io.StringIO()
        old_out = sys.stdout
        sys.stdout = test_buf
        pytest_code = pytest.main(['-v', 'tests'])
        sys.stdout = old_out
        log(f"Pytest Exit Code: {pytest_code}")

    report_file = basedir / 'scripts' / 'dynamic_verification_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    print(f"\nReport written to {report_file}")

if __name__ == '__main__':
    execute_dynamic_audit()
