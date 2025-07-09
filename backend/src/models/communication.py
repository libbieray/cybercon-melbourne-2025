from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Import db from user model to maintain consistency
from src.models.user import db

class SessionQuestion(db.Model):
    """Questions submitted by speakers about their sessions"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    asked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    question_text = db.Column(db.Text, nullable=False)
    is_urgent = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='open')  # open, answered, closed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)
    
    # Relationships
    asker = db.relationship('User', backref='session_questions')
    responses = db.relationship('SessionQuestionResponse', backref='question', lazy=True, cascade='all, delete-orphan')

    def __init__(self, session_id, asked_by, question_text, is_urgent=False):
        self.session_id = session_id
        self.asked_by = asked_by
        self.question_text = question_text
        self.is_urgent = is_urgent

    @property
    def latest_response(self):
        """Get the latest response to this question"""
        return SessionQuestionResponse.query.filter_by(
            question_id=self.id
        ).order_by(SessionQuestionResponse.created_at.desc()).first()

    def mark_answered(self):
        """Mark question as answered"""
        self.status = 'answered'
        self.answered_at = datetime.utcnow()

    def to_dict(self, include_responses=True):
        """Convert question to dictionary representation"""
        data = {
            'id': self.id,
            'session_id': self.session_id,
            'asked_by': self.asked_by,
            'asker': self.asker.to_dict() if self.asker else None,
            'question_text': self.question_text,
            'is_urgent': self.is_urgent,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None
        }
        
        if include_responses:
            data['responses'] = [r.to_dict() for r in self.responses]
            data['latest_response'] = self.latest_response.to_dict() if self.latest_response else None
        
        return data

    def __repr__(self):
        return f'<SessionQuestion {self.id} for Session {self.session_id}>'


class SessionQuestionResponse(db.Model):
    """Responses to session questions from approvers/admins"""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('session_question.id'), nullable=False)
    responded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    response_text = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)  # Internal notes not visible to speaker
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    responder = db.relationship('User', backref='question_responses')

    def __init__(self, question_id, responded_by, response_text, is_internal=False):
        self.question_id = question_id
        self.responded_by = responded_by
        self.response_text = response_text
        self.is_internal = is_internal

    def to_dict(self):
        """Convert response to dictionary representation"""
        return {
            'id': self.id,
            'question_id': self.question_id,
            'responded_by': self.responded_by,
            'responder': self.responder.to_dict() if self.responder else None,
            'response_text': self.response_text,
            'is_internal': self.is_internal,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<SessionQuestionResponse {self.id} to Question {self.question_id}>'


class FAQ(db.Model):
    """Frequently Asked Questions"""
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))  # General, Technical, Submission, etc.
    order_index = db.Column(db.Integer, default=0)  # For ordering FAQs
    is_published = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    creator = db.relationship('User', backref='created_faqs')

    def __init__(self, question, answer, category=None, created_by=None):
        self.question = question
        self.answer = answer
        self.category = category
        self.created_by = created_by

    def to_dict(self):
        """Convert FAQ to dictionary representation"""
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'order_index': self.order_index,
            'is_published': self.is_published,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }

    def __repr__(self):
        return f'<FAQ {self.id}: {self.question[:50]}...>'


class BroadcastMessage(db.Model):
    """Broadcast messages sent to speakers"""
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='general')  # general, urgent, reminder
    
    # Targeting
    target_audience = db.Column(db.String(50), default='all_speakers')  # all_speakers, submitted_speakers, approved_speakers
    target_session_status = db.Column(db.String(50))  # Filter by session status
    
    # Delivery
    sent_at = db.Column(db.DateTime)
    sent_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_sent = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', backref='broadcast_messages')
    deliveries = db.relationship('MessageDelivery', backref='message', lazy=True, cascade='all, delete-orphan')

    def __init__(self, subject, message, sent_by, **kwargs):
        self.subject = subject
        self.message = message
        self.sent_by = sent_by
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def send_message(self):
        """Mark message as sent"""
        self.is_sent = True
        self.sent_at = datetime.utcnow()

    @property
    def delivery_stats(self):
        """Get delivery statistics"""
        total_deliveries = len(self.deliveries)
        read_count = len([d for d in self.deliveries if d.read_at])
        
        return {
            'total_sent': total_deliveries,
            'total_read': read_count,
            'read_percentage': (read_count / total_deliveries * 100) if total_deliveries > 0 else 0
        }

    def to_dict(self, include_deliveries=False):
        """Convert broadcast message to dictionary representation"""
        data = {
            'id': self.id,
            'subject': self.subject,
            'message': self.message,
            'message_type': self.message_type,
            'target_audience': self.target_audience,
            'target_session_status': self.target_session_status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'sent_by': self.sent_by,
            'sender': self.sender.to_dict() if self.sender else None,
            'is_sent': self.is_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'delivery_stats': self.delivery_stats
        }
        
        if include_deliveries:
            data['deliveries'] = [d.to_dict() for d in self.deliveries]
        
        return data

    def __repr__(self):
        return f'<BroadcastMessage {self.subject}>'


class MessageDelivery(db.Model):
    """Track delivery and reading of broadcast messages"""
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('broadcast_message.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Delivery tracking
    delivered_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    recipient = db.relationship('User', backref='message_deliveries')

    def __init__(self, message_id, recipient_id):
        self.message_id = message_id
        self.recipient_id = recipient_id

    def mark_read(self):
        """Mark message as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()

    def to_dict(self):
        """Convert delivery to dictionary representation"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'recipient_id': self.recipient_id,
            'recipient': self.recipient.to_dict() if self.recipient else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_read': self.is_read
        }

    def __repr__(self):
        return f'<MessageDelivery {self.message_id} to {self.recipient_id}>'


class ApproverInvitation(db.Model):
    """Invitations for approvers to register"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    invitation_token = db.Column(db.String(100), unique=True, nullable=False)
    invited_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Invitation details
    role = db.Column(db.String(50), default='manager')  # manager or admin
    message = db.Column(db.Text)  # Personal message from inviter
    
    # Status tracking
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    used_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    expires_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    inviter = db.relationship('User', foreign_keys=[invited_by], backref='sent_invitations')
    user = db.relationship('User', foreign_keys=[used_by], backref='used_invitations')

    def __init__(self, email, invited_by, role='manager', message=None, expires_days=7):
        import secrets
        from datetime import timedelta
        
        self.email = email.lower()
        self.invited_by = invited_by
        self.role = role
        self.message = message
        self.invitation_token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(days=expires_days)

    @property
    def is_expired(self):
        """Check if invitation is expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """Check if invitation is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired

    def use_invitation(self, user_id):
        """Mark invitation as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()
        self.used_by = user_id

    def to_dict(self):
        """Convert invitation to dictionary representation"""
        return {
            'id': self.id,
            'email': self.email,
            'invitation_token': self.invitation_token,
            'invited_by': self.invited_by,
            'inviter': self.inviter.to_dict() if self.inviter else None,
            'role': self.role,
            'message': self.message,
            'is_used': self.is_used,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired,
            'is_valid': self.is_valid,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<ApproverInvitation {self.email} ({self.role})>'

