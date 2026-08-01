import pytest
from app.extensions import db
from app.models import Skill, Request, Chat, LearningHistory

def test_request_lifecycle(app, client, test_user, teacher_user):
    # Log in test_user
    client.post('/auth/login', data={'username_or_email': 'testuser', 'password': 'Password123'})

    # Create teacher skill
    skill = Skill(user_id=teacher_user.id, name='Data Analysis', category='Programming & Tech', proficiency_level='Advanced')
    db.session.add(skill)
    db.session.commit()

    # 1. Send request
    res = client.post(f'/requests/send/{skill.id}', data={'skill_id': skill.id, 'message': 'Hi teacher!'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Learning request sent successfully' in res.data

    req = Request.query.filter_by(sender_id=test_user.id, receiver_id=teacher_user.id).first()
    assert req is not None
    assert req.status == 'pending'

    # 2. Log in teacher to accept request
    client.post('/auth/logout')
    client.post('/auth/login', data={'username_or_email': 'teacher', 'password': 'Password123'})

    res_accept = client.post(f'/requests/{req.id}/accept', follow_redirects=True)
    assert res_accept.status_code == 200
    assert req.status == 'accepted'
    assert req.chat is not None  # Auto-created chat

    # 3. Complete request
    res_complete = client.post(f'/requests/{req.id}/complete', follow_redirects=True)
    assert res_complete.status_code == 200
    assert req.status == 'completed'

    # Check LearningHistory records (1 teacher, 1 learner)
    history_records = LearningHistory.query.filter_by(request_id=req.id).all()
    assert len(history_records) == 2
    roles = {h.role for h in history_records}
    assert roles == {'teacher', 'learner'}

def test_block_self_request(client, test_user, app):
    client.post('/auth/login', data={'username_or_email': 'testuser', 'password': 'Password123'})
    
    skill = Skill(user_id=test_user.id, name='Self Skill', category='Other', proficiency_level='Beginner')
    db.session.add(skill)
    db.session.commit()

    res = client.post(f'/requests/send/{skill.id}', data={'skill_id': skill.id}, follow_redirects=True)
    assert b'cannot send a learning request to yourself' in res.data

def test_duplicate_pending_request_rejection(client, test_user, teacher_user, app):
    client.post('/auth/login', data={'username_or_email': 'testuser', 'password': 'Password123'})

    skill = Skill(user_id=teacher_user.id, name='Unique Skill', category='Programming & Tech', proficiency_level='Intermediate')
    db.session.add(skill)
    db.session.commit()

    # First request
    res1 = client.post(f'/requests/send/{skill.id}', data={'skill_id': skill.id, 'message': 'First'}, follow_redirects=True)
    assert b'Learning request sent successfully' in res1.data

    # Second active request attempt
    res2 = client.post(f'/requests/send/{skill.id}', data={'skill_id': skill.id, 'message': 'Second'}, follow_redirects=True)
    assert b'already have an active request' in res2.data
