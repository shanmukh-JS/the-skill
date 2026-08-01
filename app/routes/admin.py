from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from sqlalchemy import func

from app.extensions import db
from app.models.user import User
from app.models.skill import Skill
from app.models.request import Request
from app.models.rating import Rating
from app.models.history import LearningHistory
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@admin_required
def index():
    user_count = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    skill_count = Skill.query.filter_by(is_active=True).count()
    request_count = Request.query.count()
    completed_sessions = Request.query.filter_by(status='completed').count()

    return render_template(
        'admin/index.html',
        user_count=user_count,
        active_users=active_users,
        skill_count=skill_count,
        request_count=request_count,
        completed_sessions=completed_sessions
    )

@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()

    query = User.query
    if search:
        query = query.filter((User.username.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%')))

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/users.html', pagination=pagination, users=pagination.items, search=search)

@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own admin account!', 'warning')
        return redirect(url_for('admin.users_list'))

    user.is_active = not user.is_active
    db.session.commit()
    status_str = "activated" if user.is_active else "deactivated (soft-banned)"
    flash(f'User "{user.username}" has been {status_str}.', 'info')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/skills')
@login_required
@admin_required
def skills_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()

    query = Skill.query.join(User)
    if search:
        query = query.filter((Skill.name.ilike(f'%{search}%')) | (User.username.ilike(f'%{search}%')))

    pagination = query.order_by(Skill.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/skills.html', pagination=pagination, skills=pagination.items, search=search)

@admin_bp.route('/skills/<int:skill_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_skill_active(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    skill.is_active = not skill.is_active
    db.session.commit()
    status_str = "restored" if skill.is_active else "soft-deleted/hidden"
    flash(f'Skill "{skill.name}" has been {status_str}.', 'info')
    return redirect(url_for('admin.skills_list'))

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    # 1. Most popular skills (requests grouped by skill_id)
    popular_skills = db.session.query(
        Skill.name,
        Skill.category,
        User.username.label('teacher'),
        func.count(Request.id).label('request_count')
    ).join(Skill, Request.skill_id == Skill.id)\
     .join(User, Skill.user_id == User.id)\
     .group_by(Skill.id, Skill.name, Skill.category, User.username)\
     .order_by(func.count(Request.id).desc())\
     .limit(10).all()

    # 2. Top-rated teachers (minimum threshold of 3 ratings)
    top_teachers_raw = db.session.query(
        User,
        func.avg(Rating.score).label('avg_score'),
        func.count(Rating.id).label('review_count')
    ).join(Rating, Rating.rated_user_id == User.id)\
     .group_by(User.id)\
     .having(func.count(Rating.id) >= 3)\
     .order_by(func.avg(Rating.score).desc())\
     .limit(10).all()

    # 3. Active learners in last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    active_learners = db.session.query(
        User,
        func.count(Request.id).label('recent_requests')
    ).join(Request, Request.sender_id == User.id)\
     .filter(Request.created_at >= thirty_days_ago)\
     .group_by(User.id)\
     .order_by(func.count(Request.id).desc())\
     .limit(10).all()

    # 4. Request statistics breakdown
    status_counts = dict(
        db.session.query(Request.status, func.count(Request.id))
        .group_by(Request.status).all()
    )

    # Pending requests backlog older than 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    old_pending_count = Request.query.filter(
        Request.status == 'pending',
        Request.created_at <= seven_days_ago
    ).count()

    return render_template(
        'admin/analytics.html',
        popular_skills=popular_skills,
        top_teachers=top_teachers_raw,
        active_learners=active_learners,
        status_counts=status_counts,
        old_pending_count=old_pending_count
    )
