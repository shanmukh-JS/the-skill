import pytest
from app.extensions import db
from app.models import User, Skill, Rating, Request

def test_user_average_rating_calculation(app, test_user, teacher_user):
    # Setup skill and completed request
    skill = Skill(user_id=teacher_user.id, name='Python', category='Programming & Tech', proficiency_level='Expert')
    db.session.add(skill)
    db.session.commit()

    req = Request(sender_id=test_user.id, receiver_id=teacher_user.id, skill_id=skill.id, status='completed')
    db.session.add(req)
    db.session.commit()

    # Initial rating is 0.0
    assert teacher_user.average_rating() == 0.0

    # Add 5-star rating
    r1 = Rating(request_id=req.id, rater_id=test_user.id, rated_user_id=teacher_user.id, score=5, review_text='Great!')
    db.session.add(r1)
    db.session.commit()

    assert teacher_user.average_rating() == 5.0

def test_soft_deactivation_user_and_skill(app, teacher_user):
    skill = Skill(user_id=teacher_user.id, name='Guitar', category='Music & Audio', proficiency_level='Intermediate')
    db.session.add(skill)
    db.session.commit()

    # User active default
    assert teacher_user.is_active is True
    assert skill.is_active is True

    # Soft deactivate
    teacher_user.is_active = False
    skill.is_active = False
    db.session.commit()

    # Verify user row still exists in database (referential integrity preserved)
    user_db = db.session.get(User, teacher_user.id)
    assert user_db is not None
    assert user_db.is_active is False
