from flask import Blueprint, render_template, request
from app.models.skill import Skill
from app.models.user import User
from app.models.rating import Rating

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
def search_skills():
    query_text = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    teacher_name = request.args.get('teacher', '').strip()
    page = request.args.get('page', 1, type=int)

    # Base query for active skills taught by active users
    query = Skill.query.join(User).filter(
        Skill.is_active == True,
        User.is_active == True
    )

    if query_text:
        query = query.filter(
            (Skill.name.ilike(f'%{query_text}%')) | (Skill.description.ilike(f'%{query_text}%'))
        )
    if category:
        query = query.filter(Skill.category == category)
    if teacher_name:
        query = query.filter(User.username.ilike(f'%{teacher_name}%'))

    pagination = query.order_by(Skill.created_at.desc()).paginate(page=page, per_page=10, error_out=False)

    # Fetch categories for search dropdown
    distinct_categories = [c[0] for c in Skill.query.with_entities(Skill.category).distinct().all() if c[0]]

    return render_template(
        'search/index.html',
        pagination=pagination,
        skills=pagination.items,
        query_text=query_text,
        category=category,
        teacher_name=teacher_name,
        categories=distinct_categories
    )


@search_bp.route('/teacher/<int:user_id>')
def teacher_profile(user_id):
    teacher = User.query.filter_by(id=user_id, is_active=True).first_or_404()
    taught_skills = Skill.query.filter_by(user_id=teacher.id, is_active=True).all()
    reviews = teacher.ratings_received.order_by(Rating.created_at.desc()).all()

    return render_template(
        'search/teacher_profile.html',
        teacher=teacher,
        taught_skills=taught_skills,
        reviews=reviews
    )
