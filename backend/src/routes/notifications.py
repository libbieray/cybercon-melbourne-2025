from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from src.models import db, User, Notification, NotificationPreference, AuditLog
from src.utils.security import require_auth, require_role
from flask_jwt_extended import get_jwt_identity
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

notifications_bp = Blueprint('notifications', __name__)

def send_email_notification(user, subject, message, priority='normal'):
    """Send email notification to user"""
    try:
        # Check user's email preferences
        preferences = NotificationPreference.query.filter_by(user_id=user.id).first()
        if not preferences or not preferences.email_enabled:
            return False
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = current_app.config.get('MAIL_FROM', 'noreply@cybercon2025.com')
        msg['To'] = user.email
        msg['Subject'] = f"[Cybercon 2025] {subject}"
        
        # Email body
        body = f"""
Dear {user.first_name} {user.last_name},

{message}

Best regards,
Cybercon Melbourne 2025 Team

---
This is an automated message. Please do not reply to this email.
If you need assistance, contact support@cybercon2025.com

To manage your notification preferences, log in to the speaker portal.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email (in production, use proper SMTP configuration)
        # For now, just log the email
        current_app.logger.info(f"Email notification sent to {user.email}: {subject}")
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {user.email}: {str(e)}")
        return False

def create_notification(user_id, title, message, notification_type='info', priority='normal', 
                       related_session_id=None, send_email=True):
    """Create a new notification"""
    try:
        # Create notification record
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            priority=priority,
            related_session_id=related_session_id,
            created_at=datetime.utcnow(),
            is_read=False
        )
        
        db.session.add(notification)
        
        # Send email if requested and user preferences allow
        if send_email:
            user = User.query.get(user_id)
            if user:
                send_email_notification(user, title, message, priority)
        
        db.session.commit()
        return notification
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create notification: {str(e)}")
        return None

@notifications_bp.route('', methods=['GET'])
@require_auth
def get_notifications():
    """Get user's notifications"""
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Build query
        query = Notification.query.filter_by(user_id=current_user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        # Get paginated results
        notifications = query.order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get unread count
        unread_count = Notification.query.filter_by(
            user_id=current_user_id, 
            is_read=False
        ).count()
        
        notifications_data = []
        for notification in notifications.items:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'related_session_id': notification.related_session_id
            })
        
        return jsonify({
            'notifications': notifications_data,
            'unread_count': unread_count,
            'pagination': {
                'page': notifications.page,
                'pages': notifications.pages,
                'per_page': notifications.per_page,
                'total': notifications.total,
                'has_next': notifications.has_next,
                'has_prev': notifications.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get notifications error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve notifications'}), 500

@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@require_auth
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=current_user_id
        ).first_or_404()
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Notification marked as read'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Mark notification read error: {str(e)}")
        return jsonify({'error': 'Failed to mark notification as read'}), 500

@notifications_bp.route('/mark-all-read', methods=['POST'])
@require_auth
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        current_user_id = get_jwt_identity()
        
        Notification.query.filter_by(
            user_id=current_user_id, 
            is_read=False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        
        db.session.commit()
        
        return jsonify({'message': 'All notifications marked as read'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Mark all notifications read error: {str(e)}")
        return jsonify({'error': 'Failed to mark notifications as read'}), 500

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@require_auth
def delete_notification(notification_id):
    """Delete a notification"""
    try:
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=current_user_id
        ).first_or_404()
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({'message': 'Notification deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete notification error: {str(e)}")
        return jsonify({'error': 'Failed to delete notification'}), 500

@notifications_bp.route('/preferences', methods=['GET'])
@require_auth
def get_notification_preferences():
    """Get user's notification preferences"""
    try:
        current_user_id = get_jwt_identity()
        
        preferences = NotificationPreference.query.filter_by(user_id=current_user_id).first()
        
        if not preferences:
            # Create default preferences
            preferences = NotificationPreference(
                user_id=current_user_id,
                email_enabled=True,
                email_session_updates=True,
                email_question_responses=True,
                email_schedule_changes=True,
                email_system_announcements=True,
                email_assignment_notifications=True,
                push_notifications=True,
                digest_frequency='daily'
            )
            db.session.add(preferences)
            db.session.commit()
        
        return jsonify({
            'preferences': {
                'email_enabled': preferences.email_enabled,
                'email_session_updates': preferences.email_session_updates,
                'email_question_responses': preferences.email_question_responses,
                'email_schedule_changes': preferences.email_schedule_changes,
                'email_system_announcements': preferences.email_system_announcements,
                'email_assignment_notifications': preferences.email_assignment_notifications,
                'push_notifications': preferences.push_notifications,
                'digest_frequency': preferences.digest_frequency
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get notification preferences error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve preferences'}), 500

@notifications_bp.route('/preferences', methods=['PUT'])
@require_auth
def update_notification_preferences():
    """Update user's notification preferences"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'preferences' not in data:
            return jsonify({'error': 'Preferences data required'}), 400
        
        preferences_data = data['preferences']
        
        preferences = NotificationPreference.query.filter_by(user_id=current_user_id).first()
        
        if not preferences:
            preferences = NotificationPreference(user_id=current_user_id)
            db.session.add(preferences)
        
        # Update preferences
        for key, value in preferences_data.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        
        preferences.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user_id,
            action='update_notification_preferences',
            resource_type='notification_preference',
            resource_id=preferences.id,
            details="Updated notification preferences"
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        return jsonify({'message': 'Preferences updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update notification preferences error: {str(e)}")
        return jsonify({'error': 'Failed to update preferences'}), 500

@notifications_bp.route('/send', methods=['POST'])
@require_role('admin')
def send_notification():
    """Send notification to users (admin only)"""
    try:
        data = request.get_json()
        
        required_fields = ['title', 'message', 'recipients']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        title = data['title']
        message = data['message']
        recipients = data['recipients']  # 'all', 'speakers', 'managers', or list of user IDs
        notification_type = data.get('type', 'system_announcement')
        priority = data.get('priority', 'normal')
        send_email = data.get('send_email', True)
        
        # Determine recipient users
        if recipients == 'all':
            users = User.query.filter_by(is_active=True).all()
        elif recipients == 'speakers':
            users = User.query.join(User.roles).filter(
                Role.name == 'speaker',
                User.is_active == True
            ).all()
        elif recipients == 'managers':
            users = User.query.join(User.roles).filter(
                Role.name.in_(['manager', 'admin']),
                User.is_active == True
            ).all()
        elif isinstance(recipients, list):
            users = User.query.filter(
                User.id.in_(recipients),
                User.is_active == True
            ).all()
        else:
            return jsonify({'error': 'Invalid recipients specification'}), 400
        
        # Create notifications for all recipients
        notifications_created = 0
        for user in users:
            notification = create_notification(
                user_id=user.id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                send_email=send_email
            )
            if notification:
                notifications_created += 1
        
        # Create audit log
        current_user_id = get_jwt_identity()
        audit_log = AuditLog(
            user_id=current_user_id,
            action='send_notification',
            resource_type='notification',
            details=f"Sent notification to {notifications_created} users: {title}"
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': f'Notification sent to {notifications_created} users',
            'recipients_count': notifications_created
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Send notification error: {str(e)}")
        return jsonify({'error': 'Failed to send notification'}), 500

# Utility functions for creating specific notification types
def notify_session_status_change(session, new_status, reviewer=None):
    """Notify speaker about session status change"""
    status_messages = {
        'under_review': 'Your session has been assigned for review.',
        'approved': 'Congratulations! Your session has been approved.',
        'rejected': 'Your session has been rejected. Please check the review comments for details.',
        'scheduled': 'Your session has been scheduled. Check your dashboard for details.'
    }
    
    message = status_messages.get(new_status, f'Your session status has been updated to: {new_status}')
    
    if reviewer:
        message += f" Reviewed by: {reviewer.first_name} {reviewer.last_name}"
    
    return create_notification(
        user_id=session.speaker_id,
        title=f'Session Status Update: {session.title}',
        message=message,
        notification_type='session_status',
        priority='normal' if new_status != 'rejected' else 'high',
        related_session_id=session.id
    )

def notify_question_response(question, response):
    """Notify speaker about question response"""
    return create_notification(
        user_id=question.asker_id,
        title=f'Response to your question about: {question.session.title}',
        message=f'Your question has been answered by {response.responder.first_name} {response.responder.last_name}.',
        notification_type='question_response',
        priority='normal',
        related_session_id=question.session_id
    )

def notify_session_assignment(session, reviewer):
    """Notify reviewer about session assignment"""
    return create_notification(
        user_id=reviewer.id,
        title=f'New Session Assignment: {session.title}',
        message=f'You have been assigned to review the session "{session.title}" by {session.speaker.first_name} {session.speaker.last_name}.',
        notification_type='assignment',
        priority='normal',
        related_session_id=session.id
    )

