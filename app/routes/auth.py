from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

from app.extensions import db
from app.models.user import User
from app.forms.auth_forms import RegistrationForm, LoginForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from app.utils.rate_limiter import is_rate_limited, record_failed_login, reset_failed_logins

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please log in to continue.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.username_or_email.data.strip()
        client_ip = request.remote_addr or '127.0.0.1'
        
        # Check database-backed rate limiter
        if is_rate_limited(client_ip, identifier):
            flash('Too many failed login attempts. Please wait 15 minutes before trying again.', 'danger')
            return render_template('auth/login.html', form=form), 429
            
        user = User.query.filter(
            (User.username.ilike(identifier)) | (User.email.ilike(identifier))
        ).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support or an administrator.', 'danger')
                return render_template('auth/login.html', form=form)
                
            reset_failed_logins(client_ip, identifier)
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            record_failed_login(client_ip, identifier)
            flash('Invalid username/email or password.', 'danger')
            
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated successfully!', 'success')
            return redirect(url_for('profile.view_profile'))
            
    return render_template('auth/change_password.html', form=form)


import hashlib

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter(User.email.ilike(email)).first()
        
        if user:
            s = get_serializer()
            hash_binding = hashlib.sha256(user.password_hash.encode('utf-8')).hexdigest()[:16]
            token = s.dumps({'email': user.email, 'hash': hash_binding}, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            if current_app.debug:
                current_app.logger.debug(f"Password reset link generated for {user.email}")
            
        # Generic flash message to avoid user enumeration
        flash('If an account with that email exists, a password reset link has been generated/sent.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    s = get_serializer()
    try:
        data = s.loads(token, salt='password-reset-salt', max_age=3600)  # 1 hour expiration
    except Exception:
        flash('The password reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    if isinstance(data, dict):
        email = data.get('email')
        token_hash = data.get('hash')
    else:
        email = data
        token_hash = None

    user = User.query.filter(User.email.ilike(email)).first()
    if not user:
        flash('Invalid account identifier.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    # Verify SHA-256 hash binding to invalidate token if password was changed
    current_hash_binding = hashlib.sha256(user.password_hash.encode('utf-8')).hexdigest()[:16]
    if token_hash and token_hash != current_hash_binding:
        flash('This password reset link is no longer valid because the password was previously updated.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset successfully! You may now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form)
