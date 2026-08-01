from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.chat import Chat, Message
from app.models.request import Request
from app.utils.notifications import create_notification

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/<int:request_id>')
@login_required
def chat_room(request_id):
    req = Request.query.get_or_404(request_id)
    if current_user.id not in [req.sender_id, req.receiver_id]:
        flash('Unauthorized: You are not a participant in this conversation.', 'danger')
        return redirect(url_for('requests.list_requests'))

    if req.status not in ['accepted', 'completed']:
        flash('Chat is only accessible for accepted or completed requests.', 'warning')
        return redirect(url_for('requests.list_requests'))

    chat = req.chat
    if not chat:
        chat = Chat(request_id=req.id)
        db.session.add(chat)
        db.session.commit()

    # Mark incoming unread messages as read
    unread_msgs = Message.query.filter(
        Message.chat_id == chat.id,
        Message.sender_id != current_user.id,
        Message.read_at.is_(None)
    ).all()
    for m in unread_msgs:
        m.read_at = datetime.now(timezone.utc)
    if unread_msgs:
        db.session.commit()

    messages = chat.messages.order_by(Message.sent_at.asc()).all()
    other_user = req.sender if current_user.id == req.receiver_id else req.receiver

    return render_template(
        'chat/room.html',
        chat=chat,
        request_obj=req,
        messages=messages,
        other_user=other_user
    )

@chat_bp.route('/<int:chat_id>/send', methods=['POST'])
@login_required
def send_message(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    req = chat.request
    if current_user.id not in [req.sender_id, req.receiver_id]:
        return jsonify({'error': 'Unauthorized'}), 403

    content = request.form.get('content', '').strip()
    if not content and request.is_json:
        data = request.get_json() or {}
        content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': 'Message content cannot be empty'}), 400
    if len(content) > 5000:
        return jsonify({'error': 'Message exceeds maximum length of 5000 characters'}), 400

    msg = Message(
        chat_id=chat.id,
        sender_id=current_user.id,
        content=content
    )
    db.session.add(msg)
    db.session.commit()

    # Notify counterpart
    recipient_id = req.sender_id if current_user.id == req.receiver_id else req.receiver_id
    create_notification(
        user_id=recipient_id,
        notif_type='chat_message',
        reference_id=req.id,
        message=f"New chat message from {current_user.username} regarding '{req.skill.name}'."
    )

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'message': {
                'id': msg.id,
                'sender_id': msg.sender_id,
                'sender_name': current_user.username,
                'content': msg.content,
                'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })

    return redirect(url_for('chat.chat_room', request_id=req.id))

@chat_bp.route('/<int:chat_id>/messages')
@login_required
def get_messages(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    req = chat.request
    if current_user.id not in [req.sender_id, req.receiver_id]:
        return jsonify({'error': 'Unauthorized'}), 403

    after_id = request.args.get('after', 0, type=int)

    query = Message.query.filter(Message.chat_id == chat.id)
    if after_id > 0:
        query = query.filter(Message.id > after_id)

    new_messages = query.order_by(Message.sent_at.asc()).all()

    # Mark as read if sent by other user
    updated = False
    for m in new_messages:
        if m.sender_id != current_user.id and m.read_at is None:
            m.read_at = datetime.now(timezone.utc)
            updated = True
    if updated:
        db.session.commit()

    return jsonify({
        'messages': [{
            'id': m.id,
            'sender_id': m.sender_id,
            'sender_name': m.sender.username,
            'content': m.content,
            'sent_at': m.sent_at.strftime('%Y-%m-%d %H:%M:%S')
        } for m in new_messages]
    })
