from flask import Blueprint, render_template
from app.models.skill import Skill
from app.models.user import User

from sqlalchemy.orm import joinedload

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured_skills = Skill.query.options(
        joinedload(Skill.teacher).selectinload(User.ratings_received)
    ).filter_by(is_active=True).order_by(Skill.created_at.desc()).limit(6).all()
    user_count = User.query.filter_by(is_active=True).count()
    skill_count = Skill.query.filter_by(is_active=True).count()
    return render_template('main/index.html', featured_skills=featured_skills, user_count=user_count, skill_count=skill_count)

@main_bp.route('/about')
def about():
    return render_template('main/about.html')
