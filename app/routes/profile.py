import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models.user import User
from app.models.skill import Skill, LearningInterest
from app.models.rating import Rating
from app.forms.profile_forms import ProfileEditForm
from app.utils.validators import allowed_file, validate_image_stream

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/')
@profile_bp.route('/<username>')
def view_profile(username=None):
    if username is None:
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        user = current_user
    else:
        user = User.query.filter_by(username=username).first_or_404()
        
    taught_skills = Skill.query.filter_by(user_id=user.id, is_active=True).all()
    interests = LearningInterest.query.filter_by(user_id=user.id).all()
    reviews = Rating.query.filter_by(rated_user_id=user.id).order_by(Rating.created_at.desc()).all()
    
    return render_template(
        'profile/view.html',
        user=user,
        taught_skills=taught_skills,
        interests=interests,
        reviews=reviews
    )

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileEditForm(obj=current_user)
    if form.validate_on_submit():
        current_user.bio = form.bio.data.strip() if form.bio.data else None
        
        file = form.profile_picture.data
        if file and file.filename != '':
            if allowed_file(file.filename) and validate_image_stream(file.stream):
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                
                current_user.profile_picture = unique_filename
            else:
                flash('Invalid image format or corrupted file header! Only valid PNG, JPG, and JPEG images are allowed.', 'danger')
                return render_template('profile/edit.html', form=form)
                
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.view_profile'))
        
    return render_template('profile/edit.html', form=form)
