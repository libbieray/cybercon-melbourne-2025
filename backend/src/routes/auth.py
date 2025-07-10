from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import pyotp
import qrcode
import io
import base64
import secrets
import re

from src.models import db, User, Role, AuditLog

auth_bp = Blueprint('auth', __name__)

# Token blacklist for logout functionality
blacklisted_tokens = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """Check if JWT token is blacklisted"""
    return jwt_payload['jti'] in blacklisted_tokens

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired token"""
    return jsonify({'error': 'Token has expired', 'code': 'TOKEN_EXPIRED'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid token"""
    return jsonify({'error': 'Invalid token', 'code': 'INVALID_TOKEN'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    """Handle missing token"""
    return jsonify({'error': 'Authorization token required', 'code': 'TOKEN_REQUIRED'}), 401

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def log_auth_event(user_id, action, details=None, ip_address=None, user_agent=None):
    """Log authentication events for security monitoring"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type='authentication',
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.session.add(audit_log)
    db.session.commit()

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email'].lower()).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Validate password strength
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Create new user
        user = User(
            email=data['email'].lower(),
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            organization=data.get('organization', ''),
            phone=data.get('phone', ''),
            bio=data.get('bio', '')
        )
        
        # Assign default role (speaker)
        default_role = Role.query.filter_by(name='speaker').first()
        if default_role:
            user.add_role(default_role)
        
        db.session.add(user)
        db.session.commit()
        
        # Log registration event
        log_auth_event(
            user_id=user.id,
            action='user_registered',
            details={'email': user.email, 'role': 'speaker'},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Registration successful. Please verify your email.',
            'user_id': user.id,
            'email_verification_required': True
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Find user
        user = User.query.filter_by(email=data['email'].lower()).first()
        
        if not user or not user.check_password(data['password']):
            # Log failed login attempt
            log_auth_event(
                user_id=user.id if user else None,
                action='login_failed',
                details={'email': data['email'], 'reason': 'invalid_credentials'},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            log_auth_event(
                user_id=user.id,
                action='login_failed',
                details={'email': user.email, 'reason': 'account_disabled'},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            return jsonify({'error': 'Account is disabled'}), 401
        
        # Check MFA if enabled
        if user.mfa_enabled:
            mfa_code = data.get('mfa_code')
            if not mfa_code:
                return jsonify({
                    'error': 'MFA code required',
                    'mfa_required': True
                }), 200
            
            # Verify MFA code
            totp = pyotp.TOTP(user.mfa_secret)
            if not totp.verify(mfa_code, valid_window=1):
                log_auth_event(
                    user_id=user.id,
                    action='login_failed',
                    details={'email': user.email, 'reason': 'invalid_mfa'},
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                return jsonify({'error': 'Invalid MFA code'}), 401
        
        # Create JWT tokens
        additional_claims = {
            'roles': [role.name for role in user.roles],
            'email': user.email,
            'user_id': user.id
        }
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=1)
        )
        
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log successful login
        log_auth_event(
            user_id=user.id,
            action='login_successful',
            details={'email': user.email, 'mfa_used': user.mfa_enabled},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
            'expires_in': 3600
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Create new access token
        additional_claims = {
            'roles': [role.name for role in user.roles],
            'email': user.email,
            'user_id': user.id
        }
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=1)
        )
        
        return jsonify({
            'access_token': access_token,
            'expires_in': 3600
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user and blacklist token"""
    try:
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        
        current_user_id = get_jwt_identity()
        
        # Log logout event
        log_auth_event(
            user_id=current_user_id,
            action='logout',
            details={'token_jti': jti},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'message': 'Successfully logged out'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict(include_sensitive=True)}), 200
        
    except Exception as e:
        current_app.logger.error(f"Profile retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'organization', 'phone', 'bio']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log profile update
        log_auth_event(
            user_id=user.id,
            action='profile_updated',
            details={'updated_fields': list(data.keys())},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password required'}), 400
        
        # Verify current password
        if not user.check_password(data['current_password']):
            log_auth_event(
                user_id=user.id,
                action='password_change_failed',
                details={'reason': 'invalid_current_password'},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        user.set_password(data['new_password'])
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log password change
        log_auth_event(
            user_id=user.id,
            action='password_changed',
            details={'changed_by': 'user'},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password change error: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500

@auth_bp.route('/setup-mfa', methods=['POST'])
@jwt_required()
def setup_mfa():
    """Setup multi-factor authentication"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.mfa_enabled:
            return jsonify({'error': 'MFA is already enabled'}), 400
        
        # Generate MFA secret
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="Cybercon Melbourne 2025"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        db.session.commit()
        
        return jsonify({
            'secret': secret,
            'qr_code': f"data:image/png;base64,{qr_code_base64}",
            'manual_entry_key': secret
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"MFA setup error: {str(e)}")
        return jsonify({'error': 'Failed to setup MFA'}), 500

@auth_bp.route('/verify-mfa', methods=['POST'])
@jwt_required()
def verify_mfa():
    """Verify and enable MFA"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.mfa_enabled:
            return jsonify({'error': 'MFA is already enabled'}), 400
        
        data = request.get_json()
        mfa_code = data.get('mfa_code')
        
        if not mfa_code:
            return jsonify({'error': 'MFA code required'}), 400
        
        # Verify MFA code
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(mfa_code, valid_window=1):
            return jsonify({'error': 'Invalid MFA code'}), 401
        
        # Enable MFA
        user.mfa_enabled = True
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log MFA enablement
        log_auth_event(
            user_id=user.id,
            action='mfa_enabled',
            details={'enabled_by': 'user'},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'message': 'MFA enabled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"MFA verification error: {str(e)}")
        return jsonify({'error': 'Failed to verify MFA'}), 500

@auth_bp.route('/disable-mfa', methods=['POST'])
@jwt_required()
def disable_mfa():
    """Disable multi-factor authentication"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.mfa_enabled:
            return jsonify({'error': 'MFA is not enabled'}), 400
        
        data = request.get_json()
        
        # Verify current password
        if not data.get('password') or not user.check_password(data['password']):
            return jsonify({'error': 'Password verification required'}), 401
        
        # Verify MFA code
        mfa_code = data.get('mfa_code')
        if not mfa_code:
            return jsonify({'error': 'MFA code required'}), 400
        
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(mfa_code, valid_window=1):
            return jsonify({'error': 'Invalid MFA code'}), 401
        
        # Disable MFA
        user.mfa_enabled = False
        user.mfa_secret = None
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log MFA disablement
        log_auth_event(
            user_id=user.id,
            action='mfa_disabled',
            details={'disabled_by': 'user'},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'message': 'MFA disabled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"MFA disable error: {str(e)}")
        return jsonify({'error': 'Failed to disable MFA'}), 500

