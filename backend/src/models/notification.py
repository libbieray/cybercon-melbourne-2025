from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Notification(db.Model):
    """User notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False, default='info')  # info, session_status, question_response, schedule_update, system_announcement, assignment, urgent
    priority = db.Column(db.String(20), nullable=False, default='normal')  # low, normal, high, urgent
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    related_session_id = db.Column(db.Integer, nullable=True)  # Remove FK constraint for now
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    # related_session = db.relationship('Session', backref='notifications')  # Remove for now
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'priority': self.priority,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'related_session_id': self.related_session_id
        }

class NotificationPreference(db.Model):
    """User notification preferences"""
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Email notification preferences
    email_enabled = db.Column(db.Boolean, nullable=False, default=True)
    email_session_updates = db.Column(db.Boolean, nullable=False, default=True)
    email_question_responses = db.Column(db.Boolean, nullable=False, default=True)
    email_schedule_changes = db.Column(db.Boolean, nullable=False, default=True)
    email_system_announcements = db.Column(db.Boolean, nullable=False, default=True)
    email_assignment_notifications = db.Column(db.Boolean, nullable=False, default=True)
    
    # Push notification preferences
    push_notifications = db.Column(db.Boolean, nullable=False, default=True)
    
    # Digest preferences
    digest_frequency = db.Column(db.String(20), nullable=False, default='daily')  # immediate, daily, weekly
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notification_preferences', uselist=False))
    
    def __repr__(self):
        return f'<NotificationPreference {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_enabled': self.email_enabled,
            'email_session_updates': self.email_session_updates,
            'email_question_responses': self.email_question_responses,
            'email_schedule_changes': self.email_schedule_changes,
            'email_system_announcements': self.email_system_announcements,
            'email_assignment_notifications': self.email_assignment_notifications,
            'push_notifications': self.push_notifications,
            'digest_frequency': self.digest_frequency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class NotificationDelivery(db.Model):
    """Track notification delivery status"""
    __tablename__ = 'notification_deliveries'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id'), nullable=False)
    delivery_method = db.Column(db.String(20), nullable=False)  # email, push, sms
    delivery_status = db.Column(db.String(20), nullable=False, default='pending')  # pending, sent, delivered, failed
    delivery_attempt = db.Column(db.Integer, nullable=False, default=1)
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    notification = db.relationship('Notification', backref='deliveries')
    
    def __repr__(self):
        return f'<NotificationDelivery {self.id}: {self.delivery_method} - {self.delivery_status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'notification_id': self.notification_id,
            'delivery_method': self.delivery_method,
            'delivery_status': self.delivery_status,
            'delivery_attempt': self.delivery_attempt,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None
        }

