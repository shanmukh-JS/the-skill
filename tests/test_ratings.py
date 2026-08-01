import pytest
from app.extensions import db
from app.models import Skill, Request, Rating

def test_rating_submission_and_permissions(client, test_user, teacher_user, app):
    # Setup skill and completed request
    skill = Skill(user_id=teacher_user.id, name='French', category='Languages', proficiency_level='Expert')
    db.session.add(skill)
    db.session.commit()

    req = Request(sender_id=test_user.id, receiver_id=teacher_user.id, skill_id=skill.id, status='completed')
    db.session.add(req)
    db.session.commit()

    # Log in test_user
    client.post('/auth/login', data={'username_or_email': 'testuser', 'password': 'Password123'})

    # Submit 5-star rating
    res = client.post(f'/ratings/give/{req.id}', data={
        'score': '5',
        'review_text': 'Awesome French lesson!'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Thank you! Your rating and review have been submitted' in res.data

    rating = Rating.query.filter_by(request_id=req.id, rater_id=test_user.id).first()
    assert rating is not None
    assert rating.score == 5
    assert rating.is_editable() is True

    # Duplicate rating attempt redirects to edit rating
    res_dup = client.post(f'/ratings/give/{req.id}', data={
        'score': '4',
        'review_text': 'Duplicate attempt'
    }, follow_redirects=True)
    assert b'You have already submitted a rating for this session' in res_dup.data
