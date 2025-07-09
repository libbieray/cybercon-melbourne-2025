from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Import db from user model to maintain consistency
from src.models.user import db

class SessionType(db.Model):
    """Session types for presentations"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=45)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='session_type', lazy=True)

    def __init__(self, name, description=None, duration_minutes=45):
        self.name = name
        self.description = description
        self.duration_minutes = duration_minutes

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<SessionType {self.name}>'


class Session(db.Model):
    """Updated session model with new requirements"""
    id = db.Column(db.Integer, primary_key=True)
    primary_speaker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_type_id = db.Column(db.Integer, db.ForeignKey('session_type.id'), nullable=False)
    
    # Session details
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=False)
    upload_comments = db.Column(db.Text)  # Comments from speaker about the upload
    
    # Status tracking
    status = db.Column(db.String(50), default='draft')  # draft, submitted, under_review, approved, rejected, scheduled
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    
    # Relationships
    primary_speaker = db.relationship('User', backref='primary_sessions')
    additional_speakers = db.relationship('SessionSpeaker', backref='session', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('SessionFile', backref='session', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('SessionReview', backref='session', lazy=True, cascade='all, delete-orphan')
    questions = db.relationship('SessionQuestion', backref='session', lazy=True, cascade='all, delete-orphan')
    schedule = db.relationship('SessionSchedule', backref='session', uselist=False, cascade='all, delete-orphan')

    def __init__(self, primary_speaker_id, session_type_id, title, description, **kwargs):
        self.primary_speaker_id = primary_speaker_id
        self.session_type_id = session_type_id
        self.title = title
        self.description = description
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def all_speakers(self):
        """Get all speakers including primary and additional"""
        speakers = [self.primary_speaker]
        speakers.extend([ss.speaker for ss in self.additional_speakers])
        return speakers

    @property
    def current_file(self):
        """Get the current version of the session file"""
        return SessionFile.query.filter_by(
            session_id=self.id, 
            is_current_version=True
        ).first()

    @property
    def review_summary(self):
        """Get summary of review status"""
        reviews = self.reviews
        if not reviews:
            return {
                'total_reviews': 0,
                'completed_reviews': 0,
                'average_score': None,
                'recommendation': None
            }
        
        completed_reviews = [r for r in reviews if r.status == 'completed']
        scores = [r.overall_score for r in completed_reviews if r.overall_score]
        
        return {
            'total_reviews': len(reviews),
            'completed_reviews': len(completed_reviews),
            'average_score': sum(scores) / len(scores) if scores else None,
            'recommendation': self._get_overall_recommendation(completed_reviews)
        }

    def _get_overall_recommendation(self, completed_reviews):
        """Determine overall recommendation based on completed reviews"""
        if not completed_reviews:
            return None
        
        recommendations = [r.recommendation for r in completed_reviews if r.recommendation]
        if not recommendations:
            return None
        
        approve_count = recommendations.count('approve')
        reject_count = recommendations.count('reject')
        
        if approve_count > reject_count:
            return 'approve'
        elif reject_count > approve_count:
            return 'reject'
        else:
            return 'pending'

    def submit(self):
        """Submit session for review"""
        if self.status == 'draft':
            self.status = 'submitted'
            self.submitted_at = datetime.utcnow()

    def reset_to_pending(self):
        """Reset session status to pending (for re-submissions)"""
        self.status = 'submitted'
        self.submitted_at = datetime.utcnow()
        # Mark all files as not current, new upload will set current
        for file in self.files:
            file.is_current_version = False

    def can_edit(self, user):
        """Check if user can edit this session"""
        # Primary speaker can edit their own sessions if not yet approved
        if user.id == self.primary_speaker_id and self.status in ['draft', 'submitted']:
            return True
        
        # Additional speakers can edit if session is draft
        if self.status == 'draft':
            for speaker in self.additional_speakers:
                if speaker.speaker_id == user.id:
                    return True
        
        # Managers and admins can always edit
        return user.has_role('manager') or user.has_role('admin')

    def can_view(self, user):
        """Check if user can view this session"""
        # Any speaker can view their sessions
        if user.id == self.primary_speaker_id:
            return True
        
        for speaker in self.additional_speakers:
            if speaker.speaker_id == user.id:
                return True
        
        # Managers and admins can view all sessions
        return user.has_role('manager') or user.has_role('admin')

    def to_dict(self, include_files=True, include_reviews=False, include_speakers=True):
        """Convert session to dictionary representation"""
        data = {
            'id': self.id,
            'primary_speaker_id': self.primary_speaker_id,
            'session_type_id': self.session_type_id,
            'title': self.title,
            'description': self.description,
            'upload_comments': self.upload_comments,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'review_summary': self.review_summary
        }
        
        if include_speakers:
            data['primary_speaker'] = self.primary_speaker.to_dict() if self.primary_speaker else None
            data['additional_speakers'] = [ss.to_dict() for ss in self.additional_speakers]
            data['session_type'] = self.session_type.to_dict() if self.session_type else None
        
        if include_files:
            data['files'] = [f.to_dict() for f in self.files]
            data['current_file'] = self.current_file.to_dict() if self.current_file else None
        
        if include_reviews:
            data['reviews'] = [r.to_dict() for r in self.reviews]
        
        if self.schedule:
            data['schedule'] = self.schedule.to_dict()
        
        return data

    def __repr__(self):
        return f'<Session {self.title}>'


class SessionSpeaker(db.Model):
    """Additional speakers for sessions"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    speaker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(100))  # Co-presenter, Moderator, etc.
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    speaker = db.relationship('User', foreign_keys=[speaker_id], backref='additional_sessions')
    added_by_user = db.relationship('User', foreign_keys=[added_by])

    def __init__(self, session_id, speaker_id, role=None, added_by=None):
        self.session_id = session_id
        self.speaker_id = speaker_id
        self.role = role
        self.added_by = added_by

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'speaker_id': self.speaker_id,
            'speaker': self.speaker.to_dict() if self.speaker else None,
            'role': self.role,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'added_by': self.added_by
        }

    def __repr__(self):
        return f'<SessionSpeaker {self.speaker_id} for Session {self.session_id}>'


class SessionFile(db.Model):
    """Files uploaded for sessions"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # System filename
    original_filename = db.Column(db.String(255), nullable=False)  # User's original filename
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash for integrity
    
    # Version control
    version_number = db.Column(db.Integer, default=1)
    is_current_version = db.Column(db.Boolean, default=True)
    
    # Security and validation
    scan_status = db.Column(db.String(50), default='pending')  # pending, clean, infected, error
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    uploader = db.relationship('User', backref='uploaded_session_files')

    def __init__(self, session_id, filename, original_filename, file_path, 
                 file_size, mime_type, uploaded_by, **kwargs):
        self.session_id = session_id
        self.filename = filename
        self.original_filename = original_filename
        self.file_path = file_path
        self.file_size = file_size
        self.mime_type = mime_type
        self.uploaded_by = uploaded_by
        
        # Calculate file hash
        self.file_hash = self._calculate_file_hash(file_path)
        
        # Set version number
        self._set_version_number()
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def _calculate_file_hash(self, file_path):
        """Calculate SHA-256 hash of the file"""
        import hashlib
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""

    def _set_version_number(self):
        """Set the version number for this file"""
        # Get the highest version number for this session
        max_version = db.session.query(db.func.max(SessionFile.version_number)).filter_by(
            session_id=self.session_id
        ).scalar()
        
        self.version_number = (max_version or 0) + 1
        
        # Mark all other versions as not current
        if self.is_current_version:
            SessionFile.query.filter_by(
                session_id=self.session_id
            ).update({'is_current_version': False})

    @property
    def file_extension(self):
        """Get file extension"""
        import os
        return os.path.splitext(self.original_filename)[1].lower()

    @property
    def is_safe(self):
        """Check if file passed security scan"""
        return self.scan_status == 'clean'

    def get_download_url(self):
        """Get secure download URL for this file"""
        return f"/api/files/{self.id}/download"

    def get_view_url(self):
        """Get secure view URL for this file"""
        return f"/api/files/{self.id}/view"

    def to_dict(self):
        """Convert file to dictionary representation"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'file_extension': self.file_extension,
            'version_number': self.version_number,
            'is_current_version': self.is_current_version,
            'scan_status': self.scan_status,
            'is_safe': self.is_safe,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'uploaded_by': self.uploaded_by,
            'download_url': self.get_download_url(),
            'view_url': self.get_view_url()
        }

    def __repr__(self):
        return f'<SessionFile {self.original_filename} v{self.version_number}>'

