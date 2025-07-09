from functools import wraps
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import time
from collections import defaultdict
from datetime import datetime, timedelta

from src.models import User, AuditLog, db

# Rate limiting storage (in production, use Redis)
rate_limit_storage = defaultdict(list)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_role(*allowed_roles):
    """Decorator to require specific roles for access"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401
            
            user_roles = [role.name for role in user.roles]
            
            if not any(role in user_roles for role in allowed_roles):
                # Log unauthorized access attempt
                audit_log = AuditLog(
                    user_id=user.id,
                    action='unauthorized_access_attempt',
                    resource_type='endpoint',
                    details={
                        'endpoint': request.endpoint,
                        'required_roles': list(allowed_roles),
                        'user_roles': user_roles
                    },
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)
                db.session.commit()
                
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_roles': list(allowed_roles)
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_permission(permission):
    """Decorator to require specific permission for access"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401
            
            # Check if user has the required permission through any of their roles
            has_permission = False
            for role in user.roles:
                if role.has_permission(permission):
                    has_permission = True
                    break
            
            if not has_permission:
                # Log unauthorized access attempt
                audit_log = AuditLog(
                    user_id=user.id,
                    action='unauthorized_access_attempt',
                    resource_type='endpoint',
                    details={
                        'endpoint': request.endpoint,
                        'required_permission': permission,
                        'user_permissions': [p for role in user.roles for p in role.permissions.keys()]
                    },
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)
                db.session.commit()
                
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_permission': permission
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_ownership_or_role(*allowed_roles):
    """Decorator to require resource ownership or specific roles"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401
            
            user_roles = [role.name for role in user.roles]
            
            # Check if user has required role
            if any(role in user_roles for role in allowed_roles):
                return f(*args, **kwargs)
            
            # Check ownership (resource_id should be in kwargs or args)
            resource_id = kwargs.get('id') or kwargs.get('presentation_id') or kwargs.get('user_id')
            
            if resource_id:
                # For presentations, check if user is the speaker
                if 'presentation' in request.endpoint:
                    from src.models import Presentation
                    presentation = Presentation.query.get(resource_id)
                    if presentation and presentation.speaker_id == current_user_id:
                        return f(*args, **kwargs)
                
                # For user resources, check if it's the same user
                elif 'user' in request.endpoint:
                    if int(resource_id) == current_user_id:
                        return f(*args, **kwargs)
            
            # Log unauthorized access attempt
            audit_log = AuditLog(
                user_id=user.id,
                action='unauthorized_access_attempt',
                resource_type='endpoint',
                details={
                    'endpoint': request.endpoint,
                    'resource_id': resource_id,
                    'required_roles': list(allowed_roles)
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()
            
            return jsonify({
                'error': 'Access denied. Insufficient permissions or not resource owner.'
            }), 403
            
        return decorated_function
    return decorator

def rate_limit(max_requests=100, window_minutes=15):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier (IP + User ID if authenticated)
            client_id = request.remote_addr
            
            try:
                current_user_id = get_jwt_identity()
                if current_user_id:
                    client_id = f"{client_id}:{current_user_id}"
            except:
                pass  # Not authenticated, use IP only
            
            now = time.time()
            window_start = now - (window_minutes * 60)
            
            # Clean old entries
            rate_limit_storage[client_id] = [
                timestamp for timestamp in rate_limit_storage[client_id]
                if timestamp > window_start
            ]
            
            # Check rate limit
            if len(rate_limit_storage[client_id]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window_minutes * 60
                }), 429
            
            # Add current request
            rate_limit_storage[client_id].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_file_upload(allowed_extensions=None, max_size_mb=100):
    """Decorator to validate file uploads"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Check file extension
            if allowed_extensions:
                file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if file_ext not in allowed_extensions:
                    return jsonify({
                        'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
                    }), 400
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            max_size_bytes = max_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                return jsonify({
                    'error': f'File too large. Maximum size: {max_size_mb}MB'
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_api_access(f):
    """Decorator to log API access for audit purposes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            current_user_id = get_jwt_identity()
        except:
            current_user_id = None
        
        try:
            result = f(*args, **kwargs)
            status_code = result[1] if isinstance(result, tuple) else 200
            
            # Log successful API access
            if current_user_id:
                audit_log = AuditLog(
                    user_id=current_user_id,
                    action='api_access',
                    resource_type='endpoint',
                    details={
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'status_code': status_code,
                        'response_time_ms': round((time.time() - start_time) * 1000, 2)
                    },
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)
                db.session.commit()
            
            return result
            
        except Exception as e:
            # Log API error
            if current_user_id:
                audit_log = AuditLog(
                    user_id=current_user_id,
                    action='api_error',
                    resource_type='endpoint',
                    details={
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'error': str(e),
                        'response_time_ms': round((time.time() - start_time) * 1000, 2)
                    },
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)
                db.session.commit()
            
            raise
            
    return decorated_function

def get_current_user():
    """Helper function to get current authenticated user"""
    try:
        current_user_id = get_jwt_identity()
        if current_user_id:
            return User.query.get(current_user_id)
    except:
        pass
    return None

def check_user_permission(user, permission):
    """Check if user has specific permission"""
    if not user or not user.is_active:
        return False
    
    for role in user.roles:
        if role.has_permission(permission):
            return True
    
    return False

def check_user_role(user, role_name):
    """Check if user has specific role"""
    if not user or not user.is_active:
        return False
    
    return user.has_role(role_name)

def is_admin(user):
    """Check if user is admin"""
    return check_user_role(user, 'admin')

def is_manager(user):
    """Check if user is manager or admin"""
    return check_user_role(user, 'admin') or check_user_role(user, 'manager')

def is_speaker(user):
    """Check if user is speaker"""
    return check_user_role(user, 'speaker')

def sanitize_input(data):
    """Basic input sanitization"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            data = data.replace(char, '')
        return data.strip()
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    else:
        return data

class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

