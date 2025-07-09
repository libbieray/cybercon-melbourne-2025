from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import os
import zipfile
import tempfile
from sqlalchemy import and_, or_

from src.models import (
    db, User, Role, ApproverInvitation, FAQ, BroadcastMessage, MessageDelivery,
    SessionAssignment, Session, SessionFile
)
from src.utils.security import (
    require_role, log_api_access, get_current_user, sanitize_input
)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_role('admin')
@log_api_access
def get_users():
    """Get all users with filtering and pagination"""
    try:
        # Get query parameters
        role = request.args.get('role')
        search = request.args.get('search')
        is_active = request.args.get('is_active')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = User.query
        
        # Apply filters
        if role:
            query = query.join(User.roles).filter(Role.name == role)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.organization.ilike(search_term)
                )
            )
        
        if is_active is not None:
            active_filter = is_active.lower() == 'true'
            query = query.filter(User.is_active == active_filter)
        
        # Order by creation date
        query = query.order_by(User.created_at.desc())
        
        # Paginate results
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users = pagination.items
        
        return jsonify({
            'users': [user.to_dict() for user in users],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching users: {str(e)}")
        return jsonify({'error': 'Failed to fetch users'}), 500

@admin_bp.route('/users/<int:user_id>/roles', methods=['PUT'])
@jwt_required()
@require_role('admin')
@log_api_access
def update_user_roles(user_id):
    """Update user roles"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        role_names = data.get('roles', [])
        
        if not isinstance(role_names, list):
            return jsonify({'error': 'Roles must be a list'}), 400
        
        # Validate roles exist
        roles = Role.query.filter(Role.name.in_(role_names)).all()
        if len(roles) != len(role_names):
            return jsonify({'error': 'One or more invalid roles'}), 400
        
        # Update user roles
        user.roles = roles
        db.session.commit()
        
        return jsonify({
            'message': 'User roles updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user roles: {str(e)}")
        return jsonify({'error': 'Failed to update user roles'}), 500

@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@jwt_required()
@require_role('admin')
@log_api_access
def activate_user(user_id):
    """Activate or deactivate a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        is_active = data.get('is_active', True)
        
        user.is_active = is_active
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        action = 'activated' if is_active else 'deactivated'
        return jsonify({
            'message': f'User {action} successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user status: {str(e)}")
        return jsonify({'error': 'Failed to update user status'}), 500

@admin_bp.route('/invitations', methods=['POST'])
@jwt_required()
@require_role('admin')
@log_api_access
def create_invitation():
    """Create an invitation for an approver"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        required_fields = ['email', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        if data['role'] not in ['manager', 'admin']:
            return jsonify({'error': 'Role must be manager or admin'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email'].lower()).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Check if invitation already exists and is valid
        existing_invitation = ApproverInvitation.query.filter_by(
            email=data['email'].lower(),
            is_used=False
        ).first()
        
        if existing_invitation and existing_invitation.is_valid:
            return jsonify({'error': 'Valid invitation already exists for this email'}), 409
        
        data = sanitize_input(data)
        
        # Create invitation
        invitation = ApproverInvitation(
            email=data['email'].lower(),
            invited_by=current_user.id,
            role=data['role'],
            message=data.get('message'),
            expires_days=data.get('expires_days', 7)
        )
        
        db.session.add(invitation)
        db.session.commit()
        
        return jsonify({
            'message': 'Invitation created successfully',
            'invitation': invitation.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating invitation: {str(e)}")
        return jsonify({'error': 'Failed to create invitation'}), 500

@admin_bp.route('/invitations', methods=['GET'])
@jwt_required()
@require_role('admin')
@log_api_access
def get_invitations():
    """Get all invitations"""
    try:
        # Get query parameters
        status = request.args.get('status')  # valid, used, expired
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = ApproverInvitation.query
        
        # Apply status filter
        if status == 'valid':
            query = query.filter(
                and_(
                    ApproverInvitation.is_used == False,
                    ApproverInvitation.expires_at > datetime.utcnow()
                )
            )
        elif status == 'used':
            query = query.filter(ApproverInvitation.is_used == True)
        elif status == 'expired':
            query = query.filter(
                and_(
                    ApproverInvitation.is_used == False,
                    ApproverInvitation.expires_at <= datetime.utcnow()
                )
            )
        
        # Order by creation date
        query = query.order_by(ApproverInvitation.created_at.desc())
        
        # Paginate results
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        invitations = pagination.items
        
        return jsonify({
            'invitations': [inv.to_dict() for inv in invitations],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching invitations: {str(e)}")
        return jsonify({'error': 'Failed to fetch invitations'}), 500

@admin_bp.route('/sessions/assign', methods=['POST'])
@jwt_required()
@require_role('admin')
@log_api_access
def assign_session():
    """Assign a session to an approver"""
    try:
        data = request.get_json()
        
        required_fields = ['session_id', 'approver_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate session exists
        session = Session.query.get(data['session_id'])
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Validate approver exists and has appropriate role
        approver = User.query.get(data['approver_id'])
        if not approver or not (approver.has_role('manager') or approver.has_role('admin')):
            return jsonify({'error': 'Invalid approver'}), 400
        
        # Check if assignment already exists
        existing_assignment = SessionAssignment.query.filter_by(
            session_id=data['session_id'],
            approver_id=data['approver_id'],
            status='active'
        ).first()
        
        if existing_assignment:
            return jsonify({'error': 'Session already assigned to this approver'}), 409
        
        current_user = get_current_user()
        data = sanitize_input(data)
        
        # Create assignment
        assignment = SessionAssignment(
            session_id=data['session_id'],
            approver_id=data['approver_id'],
            assigned_by=current_user.id,
            assignment_type=data.get('assignment_type', 'primary'),
            assignment_notes=data.get('assignment_notes')
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return jsonify({
            'message': 'Session assigned successfully',
            'assignment': assignment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning session: {str(e)}")
        return jsonify({'error': 'Failed to assign session'}), 500

@admin_bp.route('/faqs', methods=['GET'])
@jwt_required()
@log_api_access
def get_faqs():
    """Get all FAQs"""
    try:
        # Get query parameters
        category = request.args.get('category')
        published_only = request.args.get('published_only', 'true').lower() == 'true'
        
        query = FAQ.query
        
        # Apply filters
        if category:
            query = query.filter(FAQ.category == category)
        
        if published_only:
            query = query.filter(FAQ.is_published == True)
        
        # Order by category and order_index
        faqs = query.order_by(FAQ.category, FAQ.order_index, FAQ.created_at).all()
        
        return jsonify({
            'faqs': [faq.to_dict() for faq in faqs]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching FAQs: {str(e)}")
        return jsonify({'error': 'Failed to fetch FAQs'}), 500

@admin_bp.route('/faqs', methods=['POST'])
@jwt_required()
@require_role('admin')
@log_api_access
def create_faq():
    """Create a new FAQ"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        required_fields = ['question', 'answer']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        data = sanitize_input(data)
        
        faq = FAQ(
            question=data['question'],
            answer=data['answer'],
            category=data.get('category'),
            created_by=current_user.id
        )
        
        if 'order_index' in data:
            faq.order_index = data['order_index']
        
        if 'is_published' in data:
            faq.is_published = data['is_published']
        
        db.session.add(faq)
        db.session.commit()
        
        return jsonify({
            'message': 'FAQ created successfully',
            'faq': faq.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating FAQ: {str(e)}")
        return jsonify({'error': 'Failed to create FAQ'}), 500

@admin_bp.route('/faqs/<int:faq_id>', methods=['PUT'])
@jwt_required()
@require_role('admin')
@log_api_access
def update_faq(faq_id):
    """Update an FAQ"""
    try:
        faq = FAQ.query.get(faq_id)
        if not faq:
            return jsonify({'error': 'FAQ not found'}), 404
        
        data = request.get_json()
        data = sanitize_input(data)
        
        # Update allowed fields
        allowed_fields = ['question', 'answer', 'category', 'order_index', 'is_published']
        for field in allowed_fields:
            if field in data:
                setattr(faq, field, data[field])
        
        faq.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'FAQ updated successfully',
            'faq': faq.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating FAQ: {str(e)}")
        return jsonify({'error': 'Failed to update FAQ'}), 500

@admin_bp.route('/faqs/<int:faq_id>', methods=['DELETE'])
@jwt_required()
@require_role('admin')
@log_api_access
def delete_faq(faq_id):
    """Delete an FAQ"""
    try:
        faq = FAQ.query.get(faq_id)
        if not faq:
            return jsonify({'error': 'FAQ not found'}), 404
        
        db.session.delete(faq)
        db.session.commit()
        
        return jsonify({
            'message': 'FAQ deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting FAQ: {str(e)}")
        return jsonify({'error': 'Failed to delete FAQ'}), 500

@admin_bp.route('/broadcast-messages', methods=['POST'])
@jwt_required()
@require_role('admin')
@log_api_access
def create_broadcast_message():
    """Create and send a broadcast message"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        required_fields = ['subject', 'message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        data = sanitize_input(data)
        
        # Create broadcast message
        broadcast = BroadcastMessage(
            subject=data['subject'],
            message=data['message'],
            sent_by=current_user.id,
            message_type=data.get('message_type', 'general'),
            target_audience=data.get('target_audience', 'all_speakers'),
            target_session_status=data.get('target_session_status')
        )
        
        db.session.add(broadcast)
        db.session.flush()  # Get the message ID
        
        # Determine target users
        target_users = []
        
        if broadcast.target_audience == 'all_speakers':
            target_users = User.query.join(User.roles).filter(Role.name == 'speaker').all()
        elif broadcast.target_audience == 'submitted_speakers':
            # Users who have submitted sessions
            target_users = User.query.join(Session, User.id == Session.primary_speaker_id).filter(
                Session.status.in_(['submitted', 'under_review', 'approved', 'rejected', 'scheduled'])
            ).distinct().all()
        elif broadcast.target_audience == 'approved_speakers':
            # Users with approved sessions
            target_users = User.query.join(Session, User.id == Session.primary_speaker_id).filter(
                Session.status.in_(['approved', 'scheduled'])
            ).distinct().all()
        
        # Apply session status filter if specified
        if broadcast.target_session_status:
            target_users = User.query.join(Session, User.id == Session.primary_speaker_id).filter(
                Session.status == broadcast.target_session_status
            ).distinct().all()
        
        # Create delivery records
        for user in target_users:
            delivery = MessageDelivery(
                message_id=broadcast.id,
                recipient_id=user.id
            )
            db.session.add(delivery)
        
        # Mark message as sent
        broadcast.send_message()
        
        db.session.commit()
        
        return jsonify({
            'message': f'Broadcast message sent to {len(target_users)} recipients',
            'broadcast': broadcast.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating broadcast message: {str(e)}")
        return jsonify({'error': 'Failed to create broadcast message'}), 500

@admin_bp.route('/broadcast-messages', methods=['GET'])
@jwt_required()
@require_role('admin')
@log_api_access
def get_broadcast_messages():
    """Get all broadcast messages"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        pagination = BroadcastMessage.query.order_by(
            BroadcastMessage.created_at.desc()
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        messages = pagination.items
        
        return jsonify({
            'messages': [msg.to_dict() for msg in messages],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching broadcast messages: {str(e)}")
        return jsonify({'error': 'Failed to fetch broadcast messages'}), 500

@admin_bp.route('/bulk-download', methods=['POST'])
@jwt_required()
@require_role('admin')
@log_api_access
def bulk_download_presentations():
    """Create a bulk download of presentation files"""
    try:
        data = request.get_json()
        
        # Get filter criteria
        status = data.get('status')
        session_type_id = data.get('session_type_id')
        include_metadata = data.get('include_metadata', True)
        
        # Build query for sessions
        query = Session.query
        
        if status:
            if isinstance(status, list):
                query = query.filter(Session.status.in_(status))
            else:
                query = query.filter(Session.status == status)
        
        if session_type_id:
            query = query.filter(Session.session_type_id == session_type_id)
        
        sessions = query.all()
        
        if not sessions:
            return jsonify({'error': 'No sessions found matching criteria'}), 404
        
        # Create temporary zip file
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'presentations.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for session in sessions:
                current_file = session.current_file
                if current_file and os.path.exists(current_file.file_path):
                    # Create safe filename
                    safe_title = "".join(c for c in session.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_title = safe_title[:50]  # Limit length
                    
                    file_extension = current_file.file_extension
                    mapped_filename = f"{session.id:04d}_{safe_title}{file_extension}"
                    
                    # Add file to zip
                    zipf.write(current_file.file_path, mapped_filename)
                    
                    # Add metadata if requested
                    if include_metadata:
                        metadata = {
                            'session_id': session.id,
                            'title': session.title,
                            'description': session.description,
                            'primary_speaker': session.primary_speaker.to_dict() if session.primary_speaker else None,
                            'additional_speakers': [ss.to_dict() for ss in session.additional_speakers],
                            'session_type': session.session_type.to_dict() if session.session_type else None,
                            'status': session.status,
                            'submitted_at': session.submitted_at.isoformat() if session.submitted_at else None,
                            'file_info': current_file.to_dict()
                        }
                        
                        import json
                        metadata_filename = f"{session.id:04d}_{safe_title}_metadata.json"
                        zipf.writestr(metadata_filename, json.dumps(metadata, indent=2))
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f'cybercon_presentations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error creating bulk download: {str(e)}")
        return jsonify({'error': 'Failed to create bulk download'}), 500

@admin_bp.route('/system-stats', methods=['GET'])
@jwt_required()
@require_role('admin')
@log_api_access
def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        # User stats
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        speakers = User.query.join(User.roles).filter(Role.name == 'speaker').count()
        managers = User.query.join(User.roles).filter(Role.name == 'manager').count()
        admins = User.query.join(User.roles).filter(Role.name == 'admin').count()
        
        # Session stats
        total_sessions = Session.query.count()
        draft_sessions = Session.query.filter_by(status='draft').count()
        submitted_sessions = Session.query.filter_by(status='submitted').count()
        approved_sessions = Session.query.filter_by(status='approved').count()
        rejected_sessions = Session.query.filter_by(status='rejected').count()
        scheduled_sessions = Session.query.filter_by(status='scheduled').count()
        
        # File stats
        total_files = SessionFile.query.count()
        total_file_size = db.session.query(db.func.sum(SessionFile.file_size)).scalar() or 0
        
        # Question stats
        total_questions = SessionQuestion.query.count()
        open_questions = SessionQuestion.query.filter_by(status='open').count()
        answered_questions = SessionQuestion.query.filter_by(status='answered').count()
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_sessions = Session.query.filter(Session.created_at >= week_ago).count()
        recent_users = User.query.filter(User.created_at >= week_ago).count()
        
        return jsonify({
            'stats': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'speakers': speakers,
                    'managers': managers,
                    'admins': admins
                },
                'sessions': {
                    'total': total_sessions,
                    'draft': draft_sessions,
                    'submitted': submitted_sessions,
                    'approved': approved_sessions,
                    'rejected': rejected_sessions,
                    'scheduled': scheduled_sessions
                },
                'files': {
                    'total_files': total_files,
                    'total_size_mb': round(total_file_size / (1024 * 1024), 2)
                },
                'questions': {
                    'total': total_questions,
                    'open': open_questions,
                    'answered': answered_questions
                },
                'recent_activity': {
                    'new_sessions_week': recent_sessions,
                    'new_users_week': recent_users
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching system stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch system stats'}), 500

