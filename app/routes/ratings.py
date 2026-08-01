from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.rating import Rating
from app.models.request import Request
from app.forms.request_forms import RatingForm

ratings_bp = Blueprint('ratings', __name__, url_prefix='/ratings')

@ratings_bp.route('/give/<int:request_id>', methods=['GET', 'POST'])
@login_required
def give_rating(request_id):
    req = Request.query.get_or_404(request_id)
    if current_user.id not in [req.sender_id, req.receiver_id]:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('requests.list_requests'))

    if req.status != 'completed':
        flash('Ratings can only be submitted for completed sessions.', 'warning')
        return redirect(url_for('requests.list_requests'))

    rated_user_id = req.receiver_id if current_user.id == req.sender_id else req.sender_id

    # Check if already rated
    existing_rating = Rating.query.filter_by(request_id=req.id, rater_id=current_user.id).first()
    if existing_rating:
        flash('You have already submitted a rating for this session. You can edit it below if within 24 hours.', 'info')
        return redirect(url_for('ratings.edit_rating', rating_id=existing_rating.id))

    form = RatingForm()
    if form.validate_on_submit():
        rating = Rating(
            request_id=req.id,
            rater_id=current_user.id,
            rated_user_id=rated_user_id,
            score=int(form.score.data),
            review_text=form.review_text.data.strip() if form.review_text.data else None
        )
        db.session.add(rating)
        db.session.commit()
        flash('Thank you! Your rating and review have been submitted.', 'success')
        return redirect(url_for('profile.view_profile', username=rating.rated_user.username))

    return render_template('ratings/give.html', form=form, request_obj=req, rated_user_id=rated_user_id)

@ratings_bp.route('/<int:rating_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rating(rating_id):
    rating = Rating.query.get_or_404(rating_id)
    if rating.rater_id != current_user.id and not current_user.is_admin:
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard.index'))

    if not rating.is_editable() and not current_user.is_admin:
        flash('The 24-hour editing window for this rating has expired.', 'warning')
        return redirect(url_for('profile.view_profile', username=rating.rated_user.username))

    form = RatingForm(score=str(rating.score), review_text=rating.review_text)
    if form.validate_on_submit():
        rating.score = int(form.score.data)
        rating.review_text = form.review_text.data.strip() if form.review_text.data else None
        db.session.commit()
        flash('Your rating and review have been updated.', 'success')
        return redirect(url_for('profile.view_profile', username=rating.rated_user.username))

    return render_template('ratings/edit.html', form=form, rating=rating)

@ratings_bp.route('/<int:rating_id>/delete', methods=['POST'])
@login_required
def delete_rating(rating_id):
    rating = Rating.query.get_or_404(rating_id)
    if rating.rater_id != current_user.id and not current_user.is_admin:
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard.index'))

    if not rating.is_editable() and not current_user.is_admin:
        flash('The 24-hour window to delete this rating has expired.', 'warning')
        return redirect(url_for('profile.view_profile', username=rating.rated_user.username))

    rated_username = rating.rated_user.username
    db.session.delete(rating)
    db.session.commit()
    flash('Rating deleted.', 'info')
    return redirect(url_for('profile.view_profile', username=rated_username))
