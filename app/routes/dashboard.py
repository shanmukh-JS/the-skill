from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models.skill import Skill
from app.models.request import Request
from app.models.history import LearningHistory
from app.models.notification import Notification
from app.models.chat import Message, Chat
from app.utils.notifications import mark_notification_as_read, mark_all_notifications_as_read

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    taught_count = current_user.skills.filter_by(is_active=True).count()
    
    # Active requests (pending + accepted) involving user
    active_requests = Request.query.filter(
        (Request.sender_id == current_user.id) | (Request.receiver_id == current_user.id),
        Request.status.in_(['pending', 'accepted'])
    ).all()
    
    # Pending requests requiring action specifically by current_user as receiver
    pending_action_requests = Request.query.filter_by(
        receiver_id=current_user.id,
        status='pending'
    ).all()
    
    avg_rating = current_user.average_rating()
    completed_teaching = current_user.completed_teaching_count()
    completed_learning = current_user.completed_learning_count()

    # Recent unread chat messages for quick access
    user_chats = Chat.query.join(Request).filter(
        (Request.sender_id == current_user.id) | (Request.receiver_id == current_user.id),
        Request.status.in_(['accepted', 'completed'])
    ).all()
    
    recent_messages = []
    for chat in user_chats:
        last_msg = chat.messages.order_by(Message.sent_at.desc()).first()
        if last_msg:
            recent_messages.append({'chat': chat, 'message': last_msg})
    recent_messages.sort(key=lambda x: x['message'].sent_at, reverse=True)
    recent_messages = recent_messages[:5]

    return render_template(
        'dashboard/index.html',
        taught_count=taught_count,
        active_requests_count=len(active_requests),
        pending_action_requests=pending_action_requests,
        avg_rating=avg_rating,
        completed_teaching=completed_teaching,
        completed_learning=completed_learning,
        recent_messages=recent_messages
    )

@dashboard_bp.route('/history')
@login_required
def history():
    role_filter = request.args.get('role', 'all')
    query = LearningHistory.query.filter_by(user_id=current_user.id)

    if role_filter in ['teacher', 'learner']:
        query = query.filter_by(role=role_filter)

    records = query.order_by(LearningHistory.completed_at.desc()).all()
    return render_template('dashboard/history.html', records=records, role_filter=role_filter)

@dashboard_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('dashboard/notifications.html', notifications=notifs)

@dashboard_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    success = mark_notification_as_read(notif_id, current_user.id)
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success' if success else 'failed'})
    flash('Notification marked as read.', 'info')
    return redirect(url_for('dashboard.notifications'))

@dashboard_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    mark_all_notifications_as_read(current_user.id)
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success'})
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('dashboard.notifications'))
