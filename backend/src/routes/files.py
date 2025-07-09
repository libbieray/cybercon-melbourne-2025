from flask import Blueprint, request, jsonify, send_file, current_app
import os
import hashlib
import magic
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from datetime import datetime
from src.models import db, SessionFile, Session, User, AuditLog
from src.utils.security import require_auth, require_role
from flask_jwt_extended import get_jwt_identity

files_bp = Blueprint('files', __name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'.pdf', '.ppt', '.pptx', '.mp4', '.mov'}

def ensure_upload_directory():
    """Ensure upload directory exists"""
    upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    os.makedirs(upload_path, exist_ok=True)
    return upload_path

def get_file_hash(file_path):
    """Calculate SHA-256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def validate_file(file):
    """Validate uploaded file"""
    if not file or not file.filename:
        return False, "No file selected"
    
    # Check file extension
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size (this is also handled by Flask config)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    return True, None

@files_bp.route('/upload', methods=['POST'])
@require_auth
def upload_file():
    """Upload a presentation file"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        session_id = request.form.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        # Validate file
        is_valid, error_message = validate_file(file)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Check if session exists and user has permission
        session = Session.query.filter_by(id=session_id, speaker_id=current_user_id).first()
        if not session:
            return jsonify({'error': 'Session not found or access denied'}), 404
        
        # Ensure upload directory exists
        upload_path = ensure_upload_directory()
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{session_id}_{timestamp}_{filename}"
        file_path = os.path.join(upload_path, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Calculate file hash
        file_hash = get_file_hash(file_path)
        
        # Detect MIME type
        mime_type = magic.from_file(file_path, mime=True)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create database record
        session_file = SessionFile(
            session_id=session_id,
            original_filename=filename,
            stored_filename=unique_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=mime_type,
            file_hash=file_hash,
            uploaded_by=current_user_id,
            upload_date=datetime.utcnow(),
            version=1
        )
        
        # If there's an existing file, increment version
        existing_file = SessionFile.query.filter_by(session_id=session_id).order_by(SessionFile.version.desc()).first()
        if existing_file:
            session_file.version = existing_file.version + 1
        
        db.session.add(session_file)
        
        # Update session current file
        session.current_file_id = session_file.id
        session.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user_id,
            action='file_upload',
            resource_type='session_file',
            resource_id=session_file.id,
            details=f"Uploaded file: {filename} (v{session_file.version})"
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': {
                'id': session_file.id,
                'original_filename': session_file.original_filename,
                'file_size': session_file.file_size,
                'file_type': session_file.file_type,
                'file_hash': session_file.file_hash,
                'upload_date': session_file.upload_date.isoformat(),
                'version': session_file.version
            }
        }), 201
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large'}), 413
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"File upload error: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

@files_bp.route('/<int:file_id>/download', methods=['GET'])
@require_auth
def download_file(file_id):
    """Download a presentation file"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get file record
        session_file = SessionFile.query.get_or_404(file_id)
        session = Session.query.get(session_file.session_id)
        
        # Check permissions
        user = User.query.get(current_user_id)
        can_access = (
            session.speaker_id == current_user_id or  # Speaker owns the session
            user.has_role('admin') or  # Admin can access all
            (user.has_role('manager') and session.assigned_reviewer_id == current_user_id)  # Assigned reviewer
        )
        
        if not can_access:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if file exists
        if not os.path.exists(session_file.file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user_id,
            action='file_download',
            resource_type='session_file',
            resource_id=file_id,
            details=f"Downloaded file: {session_file.original_filename}"
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return send_file(
            session_file.file_path,
            as_attachment=True,
            download_name=session_file.original_filename
        )
        
    except Exception as e:
        current_app.logger.error(f"File download error: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500

@files_bp.route('/<int:file_id>/view', methods=['GET'])
@require_auth
def view_file(file_id):
    """View a presentation file in browser"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get file record
        session_file = SessionFile.query.get_or_404(file_id)
        session = Session.query.get(session_file.session_id)
        
        # Check permissions
        user = User.query.get(current_user_id)
        can_access = (
            session.speaker_id == current_user_id or  # Speaker owns the session
            user.has_role('admin') or  # Admin can access all
            (user.has_role('manager') and session.assigned_reviewer_id == current_user_id)  # Assigned reviewer
        )
        
        if not can_access:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if file exists
        if not os.path.exists(session_file.file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user_id,
            action='file_view',
            resource_type='session_file',
            resource_id=file_id,
            details=f"Viewed file: {session_file.original_filename}"
        )
        db.session.add(audit_log)
        db.session.commit()
        
        # Return file for inline viewing
        return send_file(
            session_file.file_path,
            as_attachment=False,
            download_name=session_file.original_filename
        )
        
    except Exception as e:
        current_app.logger.error(f"File view error: {str(e)}")
        return jsonify({'error': 'View failed'}), 500

@files_bp.route('/<int:file_id>', methods=['DELETE'])
@require_auth
def delete_file(file_id):
    """Delete a presentation file"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get file record
        session_file = SessionFile.query.get_or_404(file_id)
        session = Session.query.get(session_file.session_id)
        
        # Check permissions (only speaker or admin can delete)
        user = User.query.get(current_user_id)
        can_delete = (
            session.speaker_id == current_user_id or  # Speaker owns the session
            user.has_role('admin')  # Admin can delete
        )
        
        if not can_delete:
            return jsonify({'error': 'Access denied'}), 403
        
        # Remove file from disk
        if os.path.exists(session_file.file_path):
            os.remove(session_file.file_path)
        
        # Update session if this was the current file
        if session.current_file_id == file_id:
            session.current_file_id = None
            session.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user_id,
            action='file_delete',
            resource_type='session_file',
            resource_id=file_id,
            details=f"Deleted file: {session_file.original_filename}"
        )
        db.session.add(audit_log)
        
        # Delete database record
        db.session.delete(session_file)
        db.session.commit()
        
        return jsonify({'message': 'File deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"File delete error: {str(e)}")
        return jsonify({'error': 'Delete failed'}), 500

@files_bp.route('/session/<int:session_id>', methods=['GET'])
@require_auth
def get_session_files(session_id):
    """Get all files for a session"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if session exists and user has permission
        session = Session.query.get_or_404(session_id)
        user = User.query.get(current_user_id)
        
        can_access = (
            session.speaker_id == current_user_id or  # Speaker owns the session
            user.has_role('admin') or  # Admin can access all
            (user.has_role('manager') and session.assigned_reviewer_id == current_user_id)  # Assigned reviewer
        )
        
        if not can_access:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get all files for the session
        files = SessionFile.query.filter_by(session_id=session_id).order_by(SessionFile.version.desc()).all()
        
        files_data = []
        for file in files:
            files_data.append({
                'id': file.id,
                'original_filename': file.original_filename,
                'file_size': file.file_size,
                'file_type': file.file_type,
                'file_hash': file.file_hash,
                'upload_date': file.upload_date.isoformat(),
                'version': file.version,
                'uploaded_by': {
                    'id': file.uploader.id,
                    'name': f"{file.uploader.first_name} {file.uploader.last_name}"
                } if file.uploader else None
            })
        
        return jsonify({
            'files': files_data,
            'current_file_id': session.current_file_id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get session files error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve files'}), 500

# Error handlers
@files_bp.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large'}), 413

@files_bp.errorhandler(404)
def file_not_found(error):
    return jsonify({'error': 'File not found'}), 404

