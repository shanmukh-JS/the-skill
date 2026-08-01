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
