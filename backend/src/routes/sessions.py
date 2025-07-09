from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
import mimetypes

from src.models import (
    db, Session, SessionType, SessionSpeaker, SessionFile, User, 
    SessionQuestion, SessionQuestionResponse, SessionReview, SessionAssignment
)
from src.utils.security import (
    require_role, require_ownership_or_role, validate_file_upload, 
    log_api_access, get_current_user, sanitize_input
)

sessions_bp = Blueprint('sessions', __name__)

# Allowed file extensions for presentations
ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'mp4', 'mov'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@sessions_bp.route('/session-types', methods=['GET'])
@jwt_required()
@log_api_access
def get_session_types():
    """Get all available session types"""
    try:
        session_types = SessionType.query.filter_by(is_active=True).all()
        return jsonify({
            'session_types': [st.to_dict() for st in session_types]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching session types: {str(e)}")
        return jsonify({'error': 'Failed to fetch session types'}), 500

@sessions_bp.route('/sessions', methods=['POST'])
@jwt_required()
@log_api_access
def create_session():
    """Create a new session submission"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['session_type_id', 'title', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Sanitize input data
        data = sanitize_input(data)
        
        # Validate session type exists
        session_type = SessionType.query.get(data['session_type_id'])
        if not session_type or not session_type.is_active:
            return jsonify({'error': 'Invalid session type'}), 400
        
        # Create new session
        session = Session(
            primary_speaker_id=current_user.id,
            session_type_id=data['session_type_id'],
            title=data['title'],
            description=data['description'],
            upload_comments=data.get('upload_comments', '')
        )
        
        db.session.add(session)
        db.session.flush()  # Get the session ID
        
        # Add additional speakers if provided
        additional_speakers = data.get('additional_speakers', [])
        for speaker_data in additional_speakers:
            if 'email' in speaker_data:
                # Find user by email
                speaker_user = User.query.filter_by(email=speaker_data['email'].lower()).first()
                if speaker_user:
                    session_speaker = SessionSpeaker(
                        session_id=session.id,
                        speaker_id=speaker_user.id,
                        role=speaker_data.get('role', 'Co-presenter'),
                        added_by=current_user.id
                    )
                    db.session.add(session_speaker)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Session created successfully',
            'session': session.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating session: {str(e)}")
        return jsonify({'error': 'Failed to create session'}), 500

@sessions_bp.route('/sessions', methods=['GET'])
@jwt_required()
@log_api_access
def get_sessions():
    """Get sessions based on user role and permissions"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        status = request.args.get('status')
        session_type_id = request.args.get('session_type_id')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Build query based on user role
        if current_user.has_role('admin'):
            # Admins can see all sessions
            query = Session.query
        elif current_user.has_role('manager'):
            # Managers can see assigned sessions and all submitted sessions
            assigned_session_ids = [a.session_id for a in current_user.assigned_sessions if a.status == 'active']
            query = Session.query.filter(
                db.or_(
                    Session.id.in_(assigned_session_ids),
                    Session.status.in_(['submitted', 'under_review', 'approved', 'rejected'])
                )
            )
        else:
            # Speakers can only see their own sessions
            speaker_session_ids = [s.session_id for s in current_user.additional_sessions]
            speaker_session_ids.append(current_user.id)  # Primary speaker sessions
            query = Session.query.filter(
                db.or_(
                    Session.primary_speaker_id == current_user.id,
                    Session.id.in_(speaker_session_ids)
                )
            )
        
        # Apply filters
        if status:
            query = query.filter(Session.status == status)
        if session_type_id:
            query = query.filter(Session.session_type_id == session_type_id)
        
        # Order by creation date (newest first)
        query = query.order_by(Session.created_at.desc())
        
        # Paginate results
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        sessions = pagination.items
        
        return jsonify({
            'sessions': [s.to_dict() for s in sessions],
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
        current_app.logger.error(f"Error fetching sessions: {str(e)}")
        return jsonify({'error': 'Failed to fetch sessions'}), 500

@sessions_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
@require_ownership_or_role('admin', 'manager')
@log_api_access
def get_session(session_id):
    """Get a specific session by ID"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        current_user = get_current_user()
        if not session.can_view(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'session': session.to_dict(include_files=True, include_reviews=True)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch session'}), 500

@sessions_bp.route('/sessions/<int:session_id>', methods=['PUT'])
@jwt_required()
@require_ownership_or_role('admin', 'manager')
@log_api_access
def update_session(session_id):
    """Update a session"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        current_user = get_current_user()
        if not session.can_edit(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        data = sanitize_input(data)
        
        # Update allowed fields
        allowed_fields = ['title', 'description', 'upload_comments', 'session_type_id']
        for field in allowed_fields:
            if field in data:
                if field == 'session_type_id':
                    # Validate session type
                    session_type = SessionType.query.get(data[field])
                    if not session_type or not session_type.is_active:
                        return jsonify({'error': 'Invalid session type'}), 400
                
                setattr(session, field, data[field])
        
        session.updated_at = datetime.utcnow()
        
        # Handle additional speakers updates
        if 'additional_speakers' in data:
            # Remove existing additional speakers
            SessionSpeaker.query.filter_by(session_id=session.id).delete()
            
            # Add new additional speakers
            for speaker_data in data['additional_speakers']:
                if 'email' in speaker_data:
                    speaker_user = User.query.filter_by(email=speaker_data['email'].lower()).first()
                    if speaker_user:
                        session_speaker = SessionSpeaker(
                            session_id=session.id,
                            speaker_id=speaker_user.id,
                            role=speaker_data.get('role', 'Co-presenter'),
                            added_by=current_user.id
                        )
                        db.session.add(session_speaker)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Session updated successfully',
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to update session'}), 500

@sessions_bp.route('/sessions/<int:session_id>/submit', methods=['POST'])
@jwt_required()
@require_ownership_or_role('admin', 'manager')
@log_api_access
def submit_session(session_id):
    """Submit a session for review"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        current_user = get_current_user()
        if not session.can_edit(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if session has required information
        if not session.title or not session.description:
            return jsonify({'error': 'Session must have title and description'}), 400
        
        # Check if session has a current file
        if not session.current_file:
            return jsonify({'error': 'Session must have an uploaded file'}), 400
        
        session.submit()
        db.session.commit()
        
        return jsonify({
            'message': 'Session submitted for review successfully',
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to submit session'}), 500

@sessions_bp.route('/sessions/<int:session_id>/resubmit', methods=['POST'])
@jwt_required()
@require_ownership_or_role('admin', 'manager')
@log_api_access
def resubmit_session(session_id):
    """Re-submit a session (resets status to pending)"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        current_user = get_current_user()
        if not session.can_edit(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        session.reset_to_pending()
        db.session.commit()
        
        return jsonify({
            'message': 'Session re-submitted successfully. Status reset to pending.',
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error re-submitting session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to re-submit session'}), 500

@sessions_bp.route('/sessions/<int:session_id>/files', methods=['POST'])
@jwt_required()
@require_ownership_or_role('admin', 'manager')
@validate_file_upload(allowed_extensions=ALLOWED_EXTENSIONS, max_size_mb=100)
@log_api_access
def upload_session_file(session_id):
    """Upload a file for a session"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        current_user = get_current_user()
        if not session.can_edit(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        file = request.files['file']
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'sessions', str(session_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        
        # Create file record
        session_file = SessionFile(
            session_id=session.id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=current_user.id
        )
        
        db.session.add(session_file)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': session_file.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading file for session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to upload file'}), 500

@sessions_bp.route('/sessions/<int:session_id>/files/<int:file_id>/download', methods=['GET'])
@jwt_required()
@require_ownership_or_role('admin', 'manager')
@log_api_access
def download_session_file(session_id, file_id):
    """Download a session file"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session_file = SessionFile.query.filter_by(
            id=file_id, session_id=session_id
        ).first()
        if not session_file:
            return jsonify({'error': 'File not found'}), 404
        
        current_user = get_current_user()
        if not session.can_view(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if file exists
        if not os.path.exists(session_file.file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        return send_file(
            session_file.file_path,
            as_attachment=True,
            download_name=session_file.original_filename,
            mimetype=session_file.mime_type
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading file {file_id}: {str(e)}")
        return jsonify({'error': 'Failed to download file'}), 500

@sessions_bp.route('/sessions/<int:session_id>/files/<int:file_id>/view', methods=['GET'])
@jwt_required()
@require_ownership_or_role('admin', 'manager')
@log_api_access
def view_session_file(session_id, file_id):
    """View a session file in browser"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session_file = SessionFile.query.filter_by(
            id=file_id, session_id=session_id
        ).first()
        if not session_file:
            return jsonify({'error': 'File not found'}), 404
        
        current_user = get_current_user()
        if not session.can_view(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if file exists
        if not os.path.exists(session_file.file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        return send_file(
            session_file.file_path,
            mimetype=session_file.mime_type
        )
        
    except Exception as e:
        current_app.logger.error(f"Error viewing file {file_id}: {str(e)}")
        return jsonify({'error': 'Failed to view file'}), 500

@sessions_bp.route('/sessions/<int:session_id>/questions', methods=['POST'])
@jwt_required()
@require_ownership_or_role('admin', 'manager')
@log_api_access
def submit_question(session_id):
    """Submit a question about a session"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        current_user = get_current_user()
        if not session.can_view(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data.get('question_text'):
            return jsonify({'error': 'Question text is required'}), 400
        
        data = sanitize_input(data)
        
        question = SessionQuestion(
            session_id=session.id,
            asked_by=current_user.id,
            question_text=data['question_text'],
            is_urgent=data.get('is_urgent', False)
        )
        
        db.session.add(question)
        db.session.commit()
        
        return jsonify({
            'message': 'Question submitted successfully',
            'question': question.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting question for session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to submit question'}), 500

@sessions_bp.route('/sessions/<int:session_id>/questions', methods=['GET'])
@jwt_required()
@require_ownership_or_role('admin', 'manager')
@log_api_access
def get_session_questions(session_id):
    """Get questions for a session"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        current_user = get_current_user()
        if not session.can_view(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        questions = SessionQuestion.query.filter_by(session_id=session_id).order_by(
            SessionQuestion.created_at.desc()
        ).all()
        
        return jsonify({
            'questions': [q.to_dict() for q in questions]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching questions for session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch questions'}), 500

