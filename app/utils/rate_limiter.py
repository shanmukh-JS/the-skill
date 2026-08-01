from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.user import FailedLogin

def cleanup_old_failed_logins(retention_hours=24):
    """Deletes FailedLogin records older than retention_hours to prevent table bloat."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
        FailedLogin.query.filter(FailedLogin.attempted_at < cutoff).delete(synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()

def record_failed_login(ip_address, username):
    cleanup_old_failed_logins()
    log = FailedLogin(ip_address=ip_address, username=username)
    db.session.add(log)
    db.session.commit()

def record_rate_limit_attempt(ip_address, action_tag):
    cleanup_old_failed_logins()
    log = FailedLogin(ip_address=ip_address, username=action_tag)
    db.session.add(log)
    db.session.commit()

def is_rate_limited(ip_address, username, max_attempts=5, window_minutes=15, max_ip_attempts=15):
    """
    Dual-counter rate limiter:
    - Blocks specific (IP, username) pair after max_attempts (default 5) to stop focused brute force.
    - Blocks IP after max_ip_attempts (default 15) to stop distributed credential stuffing across usernames.
    - Prevents cross-IP account lockout DoS against legitimate users.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    
    # Counter 1: Specific (IP, username) pair count
    pair_count = FailedLogin.query.filter(
        FailedLogin.ip_address == ip_address,
        FailedLogin.username == username,
        FailedLogin.attempted_at >= cutoff
    ).count()
    
    if pair_count >= max_attempts:
        return True

    # Counter 2: IP-only count (credential stuffing protection)
    ip_count = FailedLogin.query.filter(
        FailedLogin.ip_address == ip_address,
        FailedLogin.attempted_at >= cutoff
    ).count()

    return ip_count >= max_ip_attempts

def reset_failed_logins(ip_address, username):
    FailedLogin.query.filter(
        FailedLogin.ip_address == ip_address,
        FailedLogin.username == username
    ).delete(synchronize_session=False)
    db.session.commit()
