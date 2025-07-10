"""
Database models for the Cybercon Melbourne 2025 Speaker Presentation Management System
"""

from src.models.user import db, User, Role, AuditLog, user_roles, jwt
from src.models.presentation import Presentation, PresentationFile
from src.models.review import Review, ReviewComment, ReviewAssignment
from src.models.schedule import TimeSlot, PresentationSchedule, ScheduleConflict
from src.models.session import SessionType, Session, SessionSpeaker, SessionFile
from flask_jwt_extended import JWTManager
from src.models.communication import (
    SessionQuestion, SessionQuestionResponse, FAQ, BroadcastMessage, 
    MessageDelivery, ApproverInvitation
)
from src.models.session_review import (
    SessionReview, SessionReviewComment, SessionAssignment, 
    Room, SessionSchedule
)
from src.models.notification import (
    Notification, NotificationPreference, NotificationDelivery
)

# Export all models for easy importing
__all__ = [
    'db',
    'jwt'
    'User',
    'Role', 
    'AuditLog',
    'user_roles',
    'Presentation',
    'PresentationFile',
    'Review',
    'ReviewComment',
    'ReviewAssignment',
    'TimeSlot',
    'PresentationSchedule',
    'ScheduleConflict',
    'SessionType',
    'Session',
    'SessionSpeaker',
    'SessionFile',
    'SessionQuestion',
    'SessionQuestionResponse',
    'FAQ',
    'BroadcastMessage',
    'MessageDelivery',
    'ApproverInvitation',
    'SessionReview',
    'SessionReviewComment',
    'SessionAssignment',
    'Room',
    'SessionSchedule',
    'Notification',
    'NotificationPreference',
    'NotificationDelivery'
]

