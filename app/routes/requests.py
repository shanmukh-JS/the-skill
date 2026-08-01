from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.request import Request
from app.models.skill import Skill
from app.models.chat import Chat
from app.models.history import LearningHistory
from app.forms.request_forms import RequestForm
from app.utils.notifications import create_notification

requests_bp = Blueprint('requests', __name__, url_prefix='/requests')

@requests_bp.route('/')
@login_required
def list_requests():
    tab = request.args.get('tab', 'received')
    page = request.args.get('page', 1, type=int)
    if tab == 'sent':
        pagination = Request.query.filter_by(sender_id=current_user.id).order_by(Request.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    else:
        pagination = Request.query.filter_by(receiver_id=current_user.id).order_by(Request.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('requests/list.html', requests=pagination.items, pagination=pagination, tab=tab)

@requests_bp.route('/send/<int:skill_id>', methods=['GET', 'POST'])
@login_required
def send_request(skill_id):
    skill = Skill.query.filter_by(id=skill_id, is_active=True).first_or_404()
    
    # Block self-request
    if skill.user_id == current_user.id:
        flash('You cannot send a learning request to yourself for your own skill!', 'warning')
        return redirect(url_for('search.search_skills'))

    # Check for existing active request
    existing = Request.query.filter(
        Request.sender_id == current_user.id,
        Request.receiver_id == skill.user_id,
        Request.skill_id == skill.id,
        Request.status.in_(['pending', 'accepted'])
    ).first()
    if existing:
        flash('You already have an active request for this skill with this teacher.', 'info')
        return redirect(url_for('requests.list_requests'))

    form = RequestForm(skill_id=skill.id)
    if form.validate_on_submit():
        req = Request(
            sender_id=current_user.id,
            receiver_id=skill.user_id,
            skill_id=skill.id,
            message=form.message.data.strip() if form.message.data else None,
            status='pending'
        )
        db.session.add(req)
        db.session.commit()

        # Notify teacher
        create_notification(
            user_id=skill.user_id,
            notif_type='request_received',
            reference_id=req.id,
            message=f"{current_user.username} sent you a request to learn '{skill.name}'."
        )

        flash('Learning request sent successfully!', 'success')
        return redirect(url_for('requests.list_requests', tab='sent'))

    return render_template('requests/send.html', form=form, skill=skill)

@requests_bp.route('/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_request(request_id):
    req = Request.query.get_or_404(request_id)
    if req.receiver_id != current_user.id:
        flash('Unauthorized transition attempt.', 'danger')
        return redirect(url_for('requests.list_requests'))

    if req.status != 'pending':
        flash(f'Cannot accept request in "{req.status}" state.', 'warning')
        return redirect(url_for('requests.list_requests'))

    req.status = 'accepted'
    
    # Automatically create Chat thread
    if not req.chat:
        chat = Chat(request_id=req.id)
        db.session.add(chat)

    # Notify sender
    create_notification(
        user_id=req.sender_id,
        notif_type='request_accepted',
        reference_id=req.id,
        message=f"{current_user.username} accepted your request for '{req.skill.name}'!"
    )

    db.session.commit()
    flash(f'Request accepted! You can now chat with {req.sender.username}.', 'success')
    return redirect(url_for('chat.chat_room', request_id=req.id))

@requests_bp.route('/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_request(request_id):
    req = Request.query.get_or_404(request_id)
    if req.receiver_id != current_user.id:
        flash('Unauthorized transition attempt.', 'danger')
        return redirect(url_for('requests.list_requests'))

    if req.status != 'pending':
        flash(f'Cannot reject request in "{req.status}" state.', 'warning')
        return redirect(url_for('requests.list_requests'))

    req.status = 'rejected'

    # Notify sender
    create_notification(
        user_id=req.sender_id,
        notif_type='request_rejected',
        reference_id=req.id,
        message=f"{current_user.username} declined your request for '{req.skill.name}'."
    )

    db.session.commit()
    flash('Request declined.', 'info')
    return redirect(url_for('requests.list_requests'))

@requests_bp.route('/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_request(request_id):
    req = Request.query.get_or_404(request_id)
    if req.sender_id != current_user.id:
        flash('Unauthorized transition attempt.', 'danger')
        return redirect(url_for('requests.list_requests'))

    if req.status != 'pending':
        flash('Only pending requests can be cancelled.', 'warning')
        return redirect(url_for('requests.list_requests'))

    req.status = 'cancelled'
    db.session.commit()
    flash('Request cancelled.', 'info')
    return redirect(url_for('requests.list_requests', tab='sent'))

@requests_bp.route('/<int:request_id>/complete', methods=['POST'])
@login_required
def complete_request(request_id):
    req = Request.query.get_or_404(request_id)
    if current_user.id not in [req.sender_id, req.receiver_id]:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('requests.list_requests'))

    if req.status != 'accepted':
        flash('Only accepted active sessions can be marked complete.', 'warning')
        return redirect(url_for('requests.list_requests'))

    req.status = 'completed'

    # Log 2 LearningHistory records: 1 for teacher, 1 for learner
    teacher_record = LearningHistory(
        user_id=req.receiver_id,
        skill_id=req.skill_id,
        role='teacher',
        request_id=req.id
    )
    learner_record = LearningHistory(
        user_id=req.sender_id,
        skill_id=req.skill_id,
        role='learner',
        request_id=req.id
    )
    db.session.add(teacher_record)
    db.session.add(learner_record)

    # Notify counterpart
    other_user_id = req.sender_id if current_user.id == req.receiver_id else req.receiver_id
    create_notification(
        user_id=other_user_id,
        notif_type='request_completed',
        reference_id=req.id,
        message=f"{current_user.username} marked the session for '{req.skill.name}' as completed! Don't forget to leave a review."
    )

    db.session.commit()
    flash('Session marked as completed! You can now rate and review your experience.', 'success')
    return redirect(url_for('ratings.give_rating', request_id=req.id))
