from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.skill import Skill, LearningInterest
from app.models.request import Request
from app.forms.skill_forms import SkillForm
from app.forms.profile_forms import LearningInterestForm

skills_bp = Blueprint('skills', __name__, url_prefix='/skills')

@skills_bp.route('/')
@login_required
def manage_skills():
    user_skills = Skill.query.filter_by(user_id=current_user.id, is_active=True).all()
    user_interests = LearningInterest.query.filter_by(user_id=current_user.id).all()
    interest_form = LearningInterestForm()
    return render_template('skills/manage.html', skills=user_skills, interests=user_interests, interest_form=interest_form)

@skills_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_skill():
    form = SkillForm()
    if form.validate_on_submit():
        skill = Skill(
            user_id=current_user.id,
            name=form.name.data.strip(),
            category=form.category.data,
            description=form.description.data.strip() if form.description.data else None,
            proficiency_level=form.proficiency_level.data
        )
        db.session.add(skill)
        db.session.commit()
        flash(f'Skill "{skill.name}" added successfully!', 'success')
        return redirect(url_for('skills.manage_skills'))
    return render_template('skills/add.html', form=form)

@skills_bp.route('/<int:skill_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    if skill.user_id != current_user.id and not current_user.is_admin:
        flash('Permission denied: You do not own this skill.', 'danger')
        return redirect(url_for('skills.manage_skills'))
        
    form = SkillForm(obj=skill)
    if form.validate_on_submit():
        skill.name = form.name.data.strip()
        skill.category = form.category.data
        skill.description = form.description.data.strip() if form.description.data else None
        skill.proficiency_level = form.proficiency_level.data
        db.session.commit()
        flash(f'Skill "{skill.name}" updated successfully!', 'success')
        return redirect(url_for('skills.manage_skills'))
    return render_template('skills/edit.html', form=form, skill=skill)

@skills_bp.route('/<int:skill_id>/delete', methods=['POST'])
@login_required
def delete_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    if skill.user_id != current_user.id and not current_user.is_admin:
        flash('Permission denied: You do not own this skill.', 'danger')
        return redirect(url_for('skills.manage_skills'))

    # Check active requests referencing this skill
    active_requests = Request.query.filter(
        Request.skill_id == skill.id,
        Request.status.in_(['pending', 'accepted'])
    ).count()

    if active_requests > 0:
        flash(f'Cannot delete skill "{skill.name}" because it has {active_requests} active (pending/accepted) request(s). Please complete or resolve requests first.', 'warning')
        return redirect(url_for('skills.manage_skills'))

    # Soft delete to preserve FK referential integrity
    skill.is_active = False
    db.session.commit()
    flash(f'Skill "{skill.name}" removed successfully.', 'info')
    return redirect(url_for('skills.manage_skills'))

@skills_bp.route('/interest/add', methods=['POST'])
@login_required
def add_interest():
    form = LearningInterestForm()
    if form.validate_on_submit():
        interest = LearningInterest(
            user_id=current_user.id,
            skill_name=form.skill_name.data.strip(),
            category=form.category.data.strip() if form.category.data else None
        )
        db.session.add(interest)
        db.session.commit()
        flash(f'Learning interest "{interest.skill_name}" added!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error adding interest: {error}', 'danger')
    return redirect(url_for('skills.manage_skills'))

@skills_bp.route('/interest/<int:interest_id>/delete', methods=['POST'])
@login_required
def delete_interest(interest_id):
    interest = LearningInterest.query.get_or_404(interest_id)
    if interest.user_id != current_user.id and not current_user.is_admin:
        flash('Permission denied.', 'danger')
        return redirect(url_for('skills.manage_skills'))
    db.session.delete(interest)
    db.session.commit()
    flash('Learning interest removed.', 'info')
    return redirect(url_for('skills.manage_skills'))
