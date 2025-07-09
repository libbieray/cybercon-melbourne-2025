from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# Import db from user model to maintain consistency
from src.models.user import db

class SessionReview(db.Model):
    """Reviews for session submissions"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Review status and priority
    status = db.Column(db.String(50), default='assigned')  # assigned, in_progress, completed
    
    # Timing
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Review decision
    decision = db.Column(db.String(50))  # approve, reject
    overall_score = db.Column(db.Integer)  # 1-10 scale
    
    # Comments and feedback
    internal_comments = db.Column(db.Text)  # Private notes for other reviewers/managers
    speaker_feedback = db.Column(db.Text)  # Feedback to be shared with speaker
    
    # Relationships
    reviewer = db.relationship('User', backref='session_reviews')
    comments = db.relationship('SessionReviewComment', backref='review', lazy=True, cascade='all, delete-orphan')

    def __init__(self, session_id, reviewer_id, **kwargs):
        self.session_id = session_id
        self.reviewer_id = reviewer_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def start_review(self):
        """Mark review as started"""
        if self.status == 'assigned':
            self.status = 'in_progress'
            self.started_at = datetime.utcnow()

    def complete_review(self, decision, overall_score=None, **kwargs):
        """Complete the review with decision and feedback"""
        self.decision = decision
        self.overall_score = overall_score
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def recommendation(self):
        """Get recommendation based on decision"""
        return self.decision

    def to_dict(self, include_comments=False):
        """Convert review to dictionary representation"""
        data = {
            'id': self.id,
            'session_id': self.session_id,
            'reviewer_id': self.reviewer_id,
            'reviewer': self.reviewer.to_dict() if self.reviewer else None,
            'status': self.status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'decision': self.decision,
            'overall_score': self.overall_score,
            'internal_comments': self.internal_comments,
            'speaker_feedback': self.speaker_feedback
        }
        
        if include_comments:
            data['comments'] = [c.to_dict() for c in self.comments]
        
        return data

    def __repr__(self):
        return f'<SessionReview {self.id} for Session {self.session_id}>'


class SessionReviewComment(db.Model):
    """Comments on session reviews"""
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('session_review.id'), nullable=False)
    commenter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    comment_text = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)  # Internal comments not shared with speaker
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    commenter = db.relationship('User', backref='session_review_comments')

    def __init__(self, review_id, commenter_id, comment_text, is_internal=False):
        self.review_id = review_id
        self.commenter_id = commenter_id
        self.comment_text = comment_text
        self.is_internal = is_internal

    def to_dict(self):
        """Convert comment to dictionary representation"""
        return {
            'id': self.id,
            'review_id': self.review_id,
            'commenter_id': self.commenter_id,
            'commenter': self.commenter.to_dict() if self.commenter else None,
            'comment_text': self.comment_text,
            'is_internal': self.is_internal,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<SessionReviewComment {self.id} on Review {self.review_id}>'


class SessionAssignment(db.Model):
    """Assignment of sessions to approvers/managers"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    assignment_type = db.Column(db.String(50), default='primary')  # primary, secondary
    status = db.Column(db.String(50), default='active')  # active, completed, cancelled
    
    # Assignment details
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    assignment_notes = db.Column(db.Text)  # Special instructions
    
    # Relationships
    session = db.relationship('Session', backref='assignments')
    approver = db.relationship('User', foreign_keys=[approver_id], backref='assigned_sessions')
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref='session_assignments_made')

    def __init__(self, session_id, approver_id, assigned_by, **kwargs):
        self.session_id = session_id
        self.approver_id = approver_id
        self.assigned_by = assigned_by
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def complete_assignment(self):
        """Mark assignment as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()

    def to_dict(self):
        """Convert assignment to dictionary representation"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'approver_id': self.approver_id,
            'approver': self.approver.to_dict() if self.approver else None,
            'assigned_by': self.assigned_by,
            'assigner': self.assigner.to_dict() if self.assigner else None,
            'assignment_type': self.assignment_type,
            'status': self.status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'assignment_notes': self.assignment_notes
        }

    def __repr__(self):
        return f'<SessionAssignment {self.id}: Session {self.session_id} to Approver {self.approver_id}>'


class Room(db.Model):
    """Conference rooms for session scheduling"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(200))
    capacity = db.Column(db.Integer)
    features = db.Column(db.JSON)  # AV equipment, accessibility features, etc.
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    schedules = db.relationship('SessionSchedule', backref='room', lazy=True)

    def __init__(self, name, location=None, capacity=None, features=None):
        self.name = name
        self.location = location
        self.capacity = capacity
        self.features = features or {}

    def to_dict(self):
        """Convert room to dictionary representation"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'capacity': self.capacity,
            'features': self.features,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Room {self.name}>'


class SessionSchedule(db.Model):
    """Scheduling information for approved sessions"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    
    # Scheduling details
    day = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='tentative')  # tentative, confirmed, cancelled
    
    # Additional details
    setup_notes = db.Column(db.Text)
    special_requirements = db.Column(db.Text)
    
    # Scheduling metadata
    scheduled_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    
    # Relationships
    scheduler = db.relationship('User', backref='scheduled_sessions')

    def __init__(self, session_id, room_id, day, start_time, end_time, scheduled_by, **kwargs):
        self.session_id = session_id
        self.room_id = room_id
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.scheduled_by = scheduled_by
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def confirm_schedule(self):
        """Confirm the schedule"""
        self.status = 'confirmed'
        self.confirmed_at = datetime.utcnow()

    def cancel_schedule(self):
        """Cancel the schedule"""
        self.status = 'cancelled'

    @property
    def datetime_start(self):
        """Get combined datetime for start"""
        return datetime.combine(self.day, self.start_time)

    @property
    def datetime_end(self):
        """Get combined datetime for end"""
        return datetime.combine(self.day, self.end_time)

    @property
    def duration_minutes(self):
        """Get duration in minutes"""
        start_dt = self.datetime_start
        end_dt = self.datetime_end
        return int((end_dt - start_dt).total_seconds() / 60)

    def to_dict(self):
        """Convert schedule to dictionary representation"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'room_id': self.room_id,
            'room': self.room.to_dict() if self.room else None,
            'day': self.day.isoformat() if self.day else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'datetime_start': self.datetime_start.isoformat() if self.datetime_start else None,
            'datetime_end': self.datetime_end.isoformat() if self.datetime_end else None,
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'setup_notes': self.setup_notes,
            'special_requirements': self.special_requirements,
            'scheduled_by': self.scheduled_by,
            'scheduler': self.scheduler.to_dict() if self.scheduler else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None
        }

    def __repr__(self):
        return f'<SessionSchedule {self.session_id} on {self.day} at {self.start_time}>'

