from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# Import db from user model to maintain consistency
from src.models.user import db

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    # Room information
    room_name = db.Column(db.String(100))
    room_capacity = db.Column(db.Integer)
    room_location = db.Column(db.String(200))
    room_features = db.Column(db.JSON)  # AV equipment, accessibility features, etc.
    
    # Slot configuration
    slot_type = db.Column(db.String(50), default='presentation')  # presentation, keynote, break, lunch, workshop
    is_available = db.Column(db.Boolean, default=True)
    max_presentations = db.Column(db.Integer, default=1)  # For parallel sessions
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    creator = db.relationship('User', backref='created_time_slots')
    schedules = db.relationship('PresentationSchedule', backref='time_slot', lazy=True)

    def __init__(self, start_time, end_time, **kwargs):
        self.start_time = start_time
        self.end_time = end_time
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def duration_minutes(self):
        """Get duration of time slot in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    @property
    def is_past(self):
        """Check if time slot is in the past"""
        return self.end_time < datetime.utcnow()

    @property
    def is_current(self):
        """Check if time slot is currently active"""
        now = datetime.utcnow()
        return self.start_time <= now <= self.end_time

    @property
    def scheduled_presentations_count(self):
        """Get count of presentations scheduled in this slot"""
        return len([s for s in self.schedules if s.status == 'confirmed'])

    @property
    def available_capacity(self):
        """Get remaining capacity for this time slot"""
        return self.max_presentations - self.scheduled_presentations_count

    @property
    def is_fully_booked(self):
        """Check if time slot is fully booked"""
        return self.available_capacity <= 0

    def can_schedule_presentation(self, presentation=None):
        """Check if a presentation can be scheduled in this slot"""
        if not self.is_available or self.is_past or self.is_fully_booked:
            return False
        
        if presentation:
            # Check if presentation duration fits in the slot
            if presentation.duration_minutes and presentation.duration_minutes > self.duration_minutes:
                return False
        
        return True

    def to_dict(self, include_schedules=False):
        """Convert time slot to dictionary representation"""
        data = {
            'id': self.id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': self.duration_minutes,
            'room_name': self.room_name,
            'room_capacity': self.room_capacity,
            'room_location': self.room_location,
            'room_features': self.room_features,
            'slot_type': self.slot_type,
            'is_available': self.is_available,
            'max_presentations': self.max_presentations,
            'scheduled_presentations_count': self.scheduled_presentations_count,
            'available_capacity': self.available_capacity,
            'is_fully_booked': self.is_fully_booked,
            'is_past': self.is_past,
            'is_current': self.is_current,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
        
        if include_schedules:
            data['schedules'] = [s.to_dict() for s in self.schedules]
        
        return data

    def __repr__(self):
        return f'<TimeSlot {self.start_time} - {self.end_time} ({self.room_name})>'


class PresentationSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentation.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'), nullable=False)
    
    # Scheduling details
    scheduled_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='tentative')  # tentative, confirmed, cancelled
    
    # Presentation-specific timing
    setup_time_minutes = db.Column(db.Integer, default=15)
    qa_time_minutes = db.Column(db.Integer, default=15)
    actual_duration_minutes = db.Column(db.Integer)  # Actual duration if different from planned
    
    # Special requirements and notes
    special_requirements = db.Column(db.Text)
    technical_notes = db.Column(db.Text)
    scheduling_notes = db.Column(db.Text)
    
    # Conflict tracking
    has_conflicts = db.Column(db.Boolean, default=False)
    conflict_resolution = db.Column(db.Text)
    
    # Timestamps
    confirmed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Relationships
    scheduler = db.relationship('User', backref='scheduled_presentations')
    conflicts = db.relationship('ScheduleConflict', backref='schedule', lazy=True, cascade='all, delete-orphan')

    def __init__(self, presentation_id, time_slot_id, scheduled_by, **kwargs):
        self.presentation_id = presentation_id
        self.time_slot_id = time_slot_id
        self.scheduled_by = scheduled_by
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def confirm_schedule(self):
        """Confirm the schedule"""
        self.status = 'confirmed'
        self.confirmed_at = datetime.utcnow()

    def cancel_schedule(self, reason=None):
        """Cancel the schedule"""
        self.status = 'cancelled'
        self.cancelled_at = datetime.utcnow()
        if reason:
            self.scheduling_notes = f"Cancelled: {reason}"

    @property
    def total_time_needed(self):
        """Calculate total time needed including setup and Q&A"""
        from src.models.presentation import Presentation
        presentation = Presentation.query.get(self.presentation_id)
        base_duration = presentation.duration_minutes if presentation else 45
        return base_duration + self.setup_time_minutes + self.qa_time_minutes

    @property
    def effective_start_time(self):
        """Get effective start time including setup"""
        if not self.time_slot:
            return None
        return self.time_slot.start_time

    @property
    def presentation_start_time(self):
        """Get actual presentation start time (after setup)"""
        if not self.time_slot:
            return None
        return self.time_slot.start_time + timedelta(minutes=self.setup_time_minutes)

    @property
    def presentation_end_time(self):
        """Get presentation end time (before Q&A)"""
        if not self.time_slot:
            return None
        from src.models.presentation import Presentation
        presentation = Presentation.query.get(self.presentation_id)
        duration = presentation.duration_minutes if presentation else 45
        return self.presentation_start_time + timedelta(minutes=duration)

    def check_conflicts(self):
        """Check for scheduling conflicts"""
        conflicts = []
        
        # Check if total time exceeds slot duration
        if self.time_slot and self.total_time_needed > self.time_slot.duration_minutes:
            conflicts.append({
                'type': 'duration_overflow',
                'description': f'Total time needed ({self.total_time_needed} min) exceeds slot duration ({self.time_slot.duration_minutes} min)'
            })
        
        # Check for speaker conflicts (same speaker in overlapping slots)
        from src.models.presentation import Presentation
        presentation = Presentation.query.get(self.presentation_id)
        if presentation and self.time_slot:
            overlapping_schedules = PresentationSchedule.query.join(Presentation).filter(
                Presentation.speaker_id == presentation.speaker_id,
                PresentationSchedule.id != self.id,
                PresentationSchedule.status.in_(['tentative', 'confirmed'])
            ).all()
            
            for other_schedule in overlapping_schedules:
                if other_schedule.time_slot and self._times_overlap(other_schedule.time_slot):
                    conflicts.append({
                        'type': 'speaker_conflict',
                        'description': f'Speaker has another presentation at {other_schedule.time_slot.start_time}',
                        'conflicting_schedule_id': other_schedule.id
                    })
        
        self.has_conflicts = len(conflicts) > 0
        return conflicts

    def _times_overlap(self, other_time_slot):
        """Check if this schedule overlaps with another time slot"""
        return (self.time_slot.start_time < other_time_slot.end_time and 
                self.time_slot.end_time > other_time_slot.start_time)

    def to_dict(self, include_conflicts=False):
        """Convert schedule to dictionary representation"""
        data = {
            'id': self.id,
            'presentation_id': self.presentation_id,
            'time_slot_id': self.time_slot_id,
            'scheduled_by': self.scheduled_by,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'status': self.status,
            'setup_time_minutes': self.setup_time_minutes,
            'qa_time_minutes': self.qa_time_minutes,
            'actual_duration_minutes': self.actual_duration_minutes,
            'total_time_needed': self.total_time_needed,
            'special_requirements': self.special_requirements,
            'technical_notes': self.technical_notes,
            'scheduling_notes': self.scheduling_notes,
            'has_conflicts': self.has_conflicts,
            'conflict_resolution': self.conflict_resolution,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'effective_start_time': self.effective_start_time.isoformat() if self.effective_start_time else None,
            'presentation_start_time': self.presentation_start_time.isoformat() if self.presentation_start_time else None,
            'presentation_end_time': self.presentation_end_time.isoformat() if self.presentation_end_time else None
        }
        
        if include_conflicts:
            data['conflicts'] = [c.to_dict() for c in self.conflicts]
        
        return data

    def __repr__(self):
        return f'<PresentationSchedule {self.presentation_id} at {self.time_slot_id}>'


class ScheduleConflict(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('presentation_schedule.id'), nullable=False)
    
    conflict_type = db.Column(db.String(50), nullable=False)  # duration_overflow, speaker_conflict, room_conflict
    conflict_description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Resolution tracking
    resolution_status = db.Column(db.String(50), default='unresolved')  # unresolved, resolved, ignored
    resolution_notes = db.Column(db.Text)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    resolved_at = db.Column(db.DateTime)
    
    # Metadata
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    auto_detected = db.Column(db.Boolean, default=True)
    
    # Relationships
    resolver = db.relationship('User', backref='resolved_conflicts')

    def __init__(self, schedule_id, conflict_type, conflict_description, **kwargs):
        self.schedule_id = schedule_id
        self.conflict_type = conflict_type
        self.conflict_description = conflict_description
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def resolve_conflict(self, resolved_by, resolution_notes=None):
        """Mark conflict as resolved"""
        self.resolution_status = 'resolved'
        self.resolved_by = resolved_by
        self.resolved_at = datetime.utcnow()
        if resolution_notes:
            self.resolution_notes = resolution_notes

    def ignore_conflict(self, resolved_by, reason=None):
        """Mark conflict as ignored"""
        self.resolution_status = 'ignored'
        self.resolved_by = resolved_by
        self.resolved_at = datetime.utcnow()
        if reason:
            self.resolution_notes = f"Ignored: {reason}"

    def to_dict(self):
        """Convert conflict to dictionary representation"""
        return {
            'id': self.id,
            'schedule_id': self.schedule_id,
            'conflict_type': self.conflict_type,
            'conflict_description': self.conflict_description,
            'severity': self.severity,
            'resolution_status': self.resolution_status,
            'resolution_notes': self.resolution_notes,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'auto_detected': self.auto_detected
        }

    def __repr__(self):
        return f'<ScheduleConflict {self.conflict_type} for Schedule {self.schedule_id}>'

