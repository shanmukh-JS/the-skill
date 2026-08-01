from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.user import FailedLogin

def record_failed_login(ip_address, username):
    log = FailedLogin(ip_address=ip_address, username=username)
    db.session.add(log)
    db.session.commit()

def is_rate_limited(ip_address, username, max_attempts=5, window_minutes=15):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    
    # Check attempts matching IP or Username in the sliding time window
    count = FailedLogin.query.filter(
        (FailedLogin.ip_address == ip_address) | (FailedLogin.username == username),
        FailedLogin.attempted_at >= cutoff
    ).count()
    
    return count >= max_attempts

def reset_failed_logins(ip_address, username):
    FailedLogin.query.filter(
        (FailedLogin.ip_address == ip_address) | (FailedLogin.username == username)
    ).delete(synchronize_session=False)
    db.session.commit()
