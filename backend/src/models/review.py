from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# Import db from user model to maintain consistency
from src.models.user import db

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentation.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Review status and priority
    status = db.Column(db.String(50), default='assigned')  # assigned, in_progress, completed, overdue
    priority = db.Column(db.Integer, default=3)  # 1=high, 2=medium, 3=low, 4=very_low
    
    # Timing
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    
    # Review content
    overall_score = db.Column(db.Integer)  # 1-10 scale
    recommendation = db.Column(db.String(50))  # approve, reject, conditional_approve, needs_revision
    
    # Detailed scoring (can be expanded based on conference criteria)
    technical_score = db.Column(db.Integer)  # 1-10
    relevance_score = db.Column(db.Integer)  # 1-10
    presentation_quality_score = db.Column(db.Integer)  # 1-10
    innovation_score = db.Column(db.Integer)  # 1-10
    
    # Comments and feedback
    internal_notes = db.Column(db.Text)  # Private notes for other reviewers/managers
    speaker_feedback = db.Column(db.Text)  # Feedback to be shared with speaker
    strengths = db.Column(db.Text)  # What's good about the presentation
    weaknesses = db.Column(db.Text)  # Areas for improvement
    suggestions = db.Column(db.Text)  # Specific suggestions for improvement
    
    # Metadata
    review_criteria = db.Column(db.JSON)  # Flexible criteria scoring
    
    # Relationships
    comments = db.relationship('ReviewComment', backref='review', lazy=True, cascade='all, delete-orphan')

    def __init__(self, presentation_id, reviewer_id, due_date=None, **kwargs):
        self.presentation_id = presentation_id
        self.reviewer_id = reviewer_id
        
        # Set default due date to 7 days from assignment
        if due_date:
            self.due_date = due_date
        else:
            self.due_date = datetime.utcnow() + timedelta(days=7)
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def start_review(self):
        """Mark review as started"""
        if self.status == 'assigned':
            self.status = 'in_progress'
            self.started_at = datetime.utcnow()

    def complete_review(self, overall_score, recommendation, **kwargs):
        """Complete the review with scores and recommendation"""
        self.overall_score = overall_score
        self.recommendation = recommendation
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def is_overdue(self):
        """Check if review is overdue"""
        if self.status == 'completed':
            return False
        return datetime.utcnow() > self.due_date

    @property
    def days_remaining(self):
        """Get days remaining until due date"""
        if self.status == 'completed':
            return None
        delta = self.due_date - datetime.utcnow()
        return delta.days

    @property
    def time_spent(self):
        """Calculate time spent on review"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return end_time - self.started_at

    def calculate_overall_score(self):
        """Calculate overall score from individual scores"""
        scores = [
            self.technical_score,
            self.relevance_score,
            self.presentation_quality_score,
            self.innovation_score
        ]
        
        valid_scores = [s for s in scores if s is not None]
        if valid_scores:
            return round(sum(valid_scores) / len(valid_scores))
        return None

    def to_dict(self, include_comments=False):
        """Convert review to dictionary representation"""
        data = {
            'id': self.id,
            'presentation_id': self.presentation_id,
            'reviewer_id': self.reviewer_id,
            'status': self.status,
            'priority': self.priority,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_overdue': self.is_overdue,
            'days_remaining': self.days_remaining,
            'overall_score': self.overall_score,
            'recommendation': self.recommendation,
            'technical_score': self.technical_score,
            'relevance_score': self.relevance_score,
            'presentation_quality_score': self.presentation_quality_score,
            'innovation_score': self.innovation_score,
            'internal_notes': self.internal_notes,
            'speaker_feedback': self.speaker_feedback,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'suggestions': self.suggestions,
            'review_criteria': self.review_criteria
        }
        
        if include_comments:
            data['comments'] = [c.to_dict() for c in self.comments]
        
        return data

    def __repr__(self):
        return f'<Review {self.id} for Presentation {self.presentation_id}>'


class ReviewComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    commenter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    comment_text = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(50), default='general')  # general, question, suggestion, concern
    is_internal = db.Column(db.Boolean, default=False)  # Internal comments not shared with speaker
    
    # Threading support
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('review_comment.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    commenter = db.relationship('User', backref='review_comments')
    parent_comment = db.relationship('ReviewComment', remote_side=[id], backref='replies')

    def __init__(self, review_id, commenter_id, comment_text, **kwargs):
        self.review_id = review_id
        self.commenter_id = commenter_id
        self.comment_text = comment_text
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.parent_comment_id is not None

    def to_dict(self, include_replies=True):
        """Convert comment to dictionary representation"""
        data = {
            'id': self.id,
            'review_id': self.review_id,
            'commenter_id': self.commenter_id,
            'comment_text': self.comment_text,
            'comment_type': self.comment_type,
            'is_internal': self.is_internal,
            'parent_comment_id': self.parent_comment_id,
            'is_reply': self.is_reply,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_replies and not self.is_reply:
            data['replies'] = [reply.to_dict(include_replies=False) for reply in self.replies]
        
        return data

    def __repr__(self):
        return f'<ReviewComment {self.id} on Review {self.review_id}>'


class ReviewAssignment(db.Model):
    """Manages assignment of presentations to reviewers/managers"""
    id = db.Column(db.Integer, primary_key=True)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentation.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    assignment_type = db.Column(db.String(50), default='primary')  # primary, secondary, expert_review
    status = db.Column(db.String(50), default='active')  # active, completed, cancelled
    
    # Assignment details
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Assignment criteria and notes
    assignment_criteria = db.Column(db.JSON)  # Why this manager was assigned
    assignment_notes = db.Column(db.Text)  # Special instructions
    
    # Relationships
    assigner = db.relationship('User', foreign_keys=[assigned_by], 
                              backref='assignments_made')

    def __init__(self, presentation_id, manager_id, assigned_by, **kwargs):
        self.presentation_id = presentation_id
        self.manager_id = manager_id
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
            'presentation_id': self.presentation_id,
            'manager_id': self.manager_id,
            'assigned_by': self.assigned_by,
            'assignment_type': self.assignment_type,
            'status': self.status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'assignment_criteria': self.assignment_criteria,
            'assignment_notes': self.assignment_notes
        }

    def __repr__(self):
        return f'<ReviewAssignment {self.id}: Presentation {self.presentation_id} to Manager {self.manager_id}>'

