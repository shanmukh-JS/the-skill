import pytest
from app.models import User
from app.utils.rate_limiter import is_rate_limited, record_failed_login

def test_user_password_hashing(app):
    user = User(username='hashuser', email='hash@example.com')
    user.set_password('Secret123')
    assert user.password_hash != 'Secret123'
    assert user.check_password('Secret123') is True
    assert user.check_password('WrongPass') is False

def test_registration_success(client, app):
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Account created successfully!' in response.data
    
    user = User.query.filter_by(username='newuser').first()
    assert user is not None
    assert user.email == 'newuser@example.com'

def test_duplicate_registration_rejection(client, test_user):
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'different@example.com',
        'password': 'Password123',
        'confirm_password': 'Password123'
    })
    assert b'Username is already taken' in response.data

    response2 = client.post('/auth/register', data={
        'username': 'differentuser',
        'email': 'testuser@example.com',
        'password': 'Password123',
        'confirm_password': 'Password123'
    })
    assert b'Email address is already registered' in response2.data

def test_password_complexity_rejection(client):
    response = client.post('/auth/register', data={
        'username': 'weakuser',
        'email': 'weak@example.com',
        'password': 'simplepassword',  # missing numbers
        'confirm_password': 'simplepassword'
    })
    assert b'Password must contain at least one digit' in response.data

def test_login_success_and_logout(client, test_user):
    # Login
    res = client.post('/auth/login', data={
        'username_or_email': 'testuser',
        'password': 'Password123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Welcome back, testuser!' in res.data

    # Logout
    res_out = client.post('/auth/logout', follow_redirects=True)
    assert b'You have been logged out' in res_out.data

def test_login_failure(client, test_user):
    res = client.post('/auth/login', data={
        'username_or_email': 'testuser',
        'password': 'WrongPassword123'
    })
    assert b'Invalid username/email or password' in res.data

def test_database_rate_limiter(app):
    ip = '192.168.1.100'
    username = 'target_user'
    
    assert is_rate_limited(ip, username, max_attempts=5) is False
    for _ in range(5):
        record_failed_login(ip, username)
        
    assert is_rate_limited(ip, username, max_attempts=5) is True

def test_password_reset_token_invalidated_after_password_change(client, test_user, app):
    from itsdangerous import URLSafeTimedSerializer
    import hashlib
    
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    hash_binding = hashlib.sha256(test_user.password_hash.encode('utf-8')).hexdigest()[:16]
    token = s.dumps({'email': test_user.email, 'hash': hash_binding}, salt='password-reset-salt')

    # Change password
    test_user.set_password('NewPassword123!')
    from app.extensions import db
    db.session.commit()

    # Attempt to reset password using old token
    res = client.get(f'/auth/reset-password/{token}', follow_redirects=True)
    assert b'no longer valid because the password was previously updated' in res.data

def test_forgot_password_stdout_sanitized(client, test_user, capsys):
    client.post('/auth/forgot-password', data={'email': test_user.email}, follow_redirects=True)
    captured = capsys.readouterr()
    assert '[DEV MODE - PASSWORD RESET LINK]' not in captured.out
    assert test_user.email not in captured.out

def test_multi_device_session_invalidation_on_password_change(app, test_user):
    c1 = app.test_client()
    c1.post('/auth/login', data={'username_or_email': 'testuser', 'password': 'Password123'})
    
    c2 = app.test_client()
    c2.post('/auth/login', data={'username_or_email': 'testuser', 'password': 'Password123'})

    # Password change on Device 1
    c1.post('/auth/change-password', data={'current_password': 'Password123', 'new_password': 'NewPassword123!', 'confirm_password': 'NewPassword123!'}, follow_redirects=True)

    from flask import g
    if hasattr(g, '_login_user'):
        delattr(g, '_login_user')

    # Device 2 request to protected route
    res_c2 = c2.get('/dashboard/', follow_redirects=False)
    assert res_c2.status_code == 302
    assert '/auth/login' in res_c2.headers.get('Location')
