from app.extensions import db
from app.models.notification import Notification

def create_notification(user_id, notif_type, reference_id, message):
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        reference_id=reference_id,
        message=message
    )
    db.session.add(notif)
    db.session.commit()
    return notif

def mark_notification_as_read(notification_id, user_id):
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notif and not notif.is_read:
        notif.is_read = True
        db.session.commit()
        return True
    return False

def mark_all_notifications_as_read(user_id):
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
