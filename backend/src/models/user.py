from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

db = SQLAlchemy()
jwt = JWTManager()

# Association table for many-to-many relationship between users and roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow),
    db.Column('assigned_by', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    organization = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    profile_image_url = db.Column(db.String(500))
    
    # Account status and security
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100))
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
                           primaryjoin='User.id == user_roles.c.user_id',
                           secondaryjoin='Role.id == user_roles.c.role_id',
                           backref=db.backref('users', lazy=True))
    presentations = db.relationship('Presentation', backref='speaker', lazy=True)
    reviews = db.relationship('Review', backref='reviewer', lazy=True)
    assigned_reviews = db.relationship('ReviewAssignment', 
                                     foreign_keys='ReviewAssignment.manager_id',
                                     backref='manager', lazy=True)

    def __init__(self, email, password, first_name, last_name, **kwargs):
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.email_verification_token = secrets.token_urlsafe(32)
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)

    def add_role(self, role):
        """Add a role to the user"""
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role):
        """Remove a role from the user"""
        if role in self.roles:
            self.roles.remove(role)

    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary representation"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'organization': self.organization,
            'phone': self.phone,
            'bio': self.bio,
            'profile_image_url': self.profile_image_url,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'roles': [role.name for role in self.roles]
        }
        
        if include_sensitive:
            data.update({
                'mfa_enabled': self.mfa_enabled,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            })
        
        return data

    def __repr__(self):
        return f'<User {self.email}>'


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.JSON)  # Store permissions as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, description=None, permissions=None):
        self.name = name
        self.description = description
        self.permissions = permissions or {}

    def has_permission(self, permission):
        """Check if role has a specific permission"""
        return self.permissions.get(permission, False)

    def add_permission(self, permission):
        """Add a permission to the role"""
        if not self.permissions:
            self.permissions = {}
        self.permissions[permission] = True

    def remove_permission(self, permission):
        """Remove a permission from the role"""
        if self.permissions and permission in self.permissions:
            del self.permissions[permission]

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Role {self.name}>'


class AuditLog(db.Model):
    """Audit log for tracking all significant system events"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='audit_logs')

    def __init__(self, action, resource_type, user_id=None, resource_id=None, 
                 details=None, ip_address=None, user_agent=None):
        self.action = action
        self.resource_type = resource_type
        self.user_id = user_id
        self.resource_id = resource_id
        self.details = details or {}
        self.ip_address = ip_address
        self.user_agent = user_agent

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

    def __repr__(self):
        return f'<AuditLog {self.action} on {self.resource_type}>'

