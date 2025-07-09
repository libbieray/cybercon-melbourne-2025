from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import os

# Import db from user model to maintain consistency
from src.models.user import db

class Presentation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    speaker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    duration_minutes = db.Column(db.Integer)
    technical_requirements = db.Column(db.Text)
    target_audience = db.Column(db.String(100))
    
    # Status tracking
    status = db.Column(db.String(50), default='draft')  # draft, submitted, under_review, approved, rejected, scheduled
    submission_deadline = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    
    # Relationships
    files = db.relationship('PresentationFile', backref='presentation', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='presentation', lazy=True, cascade='all, delete-orphan')
    schedule = db.relationship('PresentationSchedule', backref='presentation', uselist=False, cascade='all, delete-orphan')

    def __init__(self, speaker_id, title, **kwargs):
        self.speaker_id = speaker_id
        self.title = title
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def current_file(self):
        """Get the current version of the presentation file"""
        return PresentationFile.query.filter_by(
            presentation_id=self.id, 
            is_current_version=True
        ).first()

    @property
    def file_versions(self):
        """Get all file versions ordered by version number"""
        return PresentationFile.query.filter_by(
            presentation_id=self.id
        ).order_by(PresentationFile.version_number.desc()).all()

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
        
        # Simple majority logic - can be enhanced based on business rules
        approve_count = recommendations.count('approve')
        reject_count = recommendations.count('reject')
        
        if approve_count > reject_count:
            return 'approve'
        elif reject_count > approve_count:
            return 'reject'
        else:
            return 'pending'

    def submit(self):
        """Submit presentation for review"""
        if self.status == 'draft':
            self.status = 'submitted'
            self.submitted_at = datetime.utcnow()

    def can_edit(self, user):
        """Check if user can edit this presentation"""
        # Speaker can edit their own presentations if not yet approved
        if user.id == self.speaker_id and self.status in ['draft', 'submitted']:
            return True
        
        # Managers and admins can always edit
        return user.has_role('manager') or user.has_role('admin')

    def can_view(self, user):
        """Check if user can view this presentation"""
        # Speaker can view their own presentations
        if user.id == self.speaker_id:
            return True
        
        # Managers and admins can view all presentations
        return user.has_role('manager') or user.has_role('admin')

    def to_dict(self, include_files=True, include_reviews=False):
        """Convert presentation to dictionary representation"""
        data = {
            'id': self.id,
            'speaker_id': self.speaker_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'duration_minutes': self.duration_minutes,
            'technical_requirements': self.technical_requirements,
            'target_audience': self.target_audience,
            'status': self.status,
            'submission_deadline': self.submission_deadline.isoformat() if self.submission_deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'review_summary': self.review_summary
        }
        
        if include_files:
            data['files'] = [f.to_dict() for f in self.files]
            data['current_file'] = self.current_file.to_dict() if self.current_file else None
        
        if include_reviews:
            data['reviews'] = [r.to_dict() for r in self.reviews]
        
        if self.schedule:
            data['schedule'] = self.schedule.to_dict()
        
        return data

    def __repr__(self):
        return f'<Presentation {self.title}>'


class PresentationFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentation.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # System filename
    original_filename = db.Column(db.String(255), nullable=False)  # User's original filename
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash for integrity
    
    # Version control
    version_number = db.Column(db.Integer, default=1)
    is_current_version = db.Column(db.Boolean, default=True)
    version_notes = db.Column(db.Text)
    
    # Security and validation
    scan_status = db.Column(db.String(50), default='pending')  # pending, clean, infected, error
    scan_details = db.Column(db.JSON)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    uploader = db.relationship('User', backref='uploaded_files')

    def __init__(self, presentation_id, filename, original_filename, file_path, 
                 file_size, mime_type, uploaded_by, **kwargs):
        self.presentation_id = presentation_id
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
        # Get the highest version number for this presentation
        max_version = db.session.query(db.func.max(PresentationFile.version_number)).filter_by(
            presentation_id=self.presentation_id
        ).scalar()
        
        self.version_number = (max_version or 0) + 1
        
        # Mark all other versions as not current
        if self.is_current_version:
            PresentationFile.query.filter_by(
                presentation_id=self.presentation_id
            ).update({'is_current_version': False})

    @property
    def file_extension(self):
        """Get file extension"""
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
            'presentation_id': self.presentation_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'file_extension': self.file_extension,
            'version_number': self.version_number,
            'is_current_version': self.is_current_version,
            'version_notes': self.version_notes,
            'scan_status': self.scan_status,
            'is_safe': self.is_safe,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'uploaded_by': self.uploaded_by,
            'download_url': self.get_download_url(),
            'view_url': self.get_view_url()
        }

    def __repr__(self):
        return f'<PresentationFile {self.original_filename} v{self.version_number}>'

