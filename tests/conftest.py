import pytest
from app import create_app
from app.extensions import db as _db
from app.models import User, Skill, Request, Rating

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
    yield app
    with app.app_context():
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    user = User(username='testuser', email='testuser@example.com')
    user.set_password('Password123')
    _db.session.add(user)
    _db.session.commit()
    return user

@pytest.fixture
def teacher_user(app):
    user = User(username='teacher', email='teacher@example.com')
    user.set_password('Password123')
    _db.session.add(user)
    _db.session.commit()
    return user

@pytest.fixture
def admin_user(app):
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.set_password('Password123')
    _db.session.add(admin)
    _db.session.commit()
    return admin
