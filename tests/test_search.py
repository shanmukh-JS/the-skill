import pytest
from app.extensions import db
from app.models import Skill

def test_search_and_filtering(client, teacher_user, app):
    s1 = Skill(user_id=teacher_user.id, name='Flask Framework', category='Programming & Tech', proficiency_level='Advanced')
    s2 = Skill(user_id=teacher_user.id, name='Cooking Italian Pasta', category='Cooking & Crafts', proficiency_level='Expert')
    db.session.add_all([s1, s2])
    db.session.commit()

    # Search keyword match
    res = client.get('/search/?q=Flask')
    assert b'Flask Framework' in res.data
    assert b'Cooking Italian Pasta' not in res.data

    # Search category filter
    res_cat = client.get('/search/?category=Cooking+%26+Crafts')
    assert b'Cooking Italian Pasta' in res_cat.data
    assert b'Flask Framework' not in res_cat.data

    # Search empty state
    res_empty = client.get('/search/?q=NonExistentSkillKeyword')
    assert b'No skills matched your search' in res_empty.data
