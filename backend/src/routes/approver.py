from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import and_, or_

from src.models import (
    db, Session, SessionReview, SessionReviewComment, SessionAssignment,
    SessionQuestion, SessionQuestionResponse, User, SessionSchedule, Room
)
from src.utils.security import (
    require_role, log_api_access, get_current_user, sanitize_input
)

approver_bp = Blueprint('approver', __name__)

@approver_bp.route('/assigned-sessions', methods=['GET'])
@jwt_required()
@require_role('admin', 'manager')
@log_api_access
def get_assigned_sessions():
    """Get sessions assigned to the current approver"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        if current_user.has_role('admin'):
            # Admins can see all sessions
            query = Session.query
        else:
            # Managers can only see assigned sessions
            assigned_session_ids = [a.session_id for a in current_user.assigned_sessions if a.status == 'active']
            query = Session.query.filter(Session.id.in_(assigned_session_ids))
        
        # Apply status filter
        if status:
            query = query.filter(Session.status == status)
        
        # Order by submission date
        query = query.order_by(Session.submitted_at.desc().nullslast(), Session.created_at.desc())
        
        # Paginate results
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        sessions = pagination.items
        
        return jsonify({
            'sessions': [s.to_dict(include_files=True) for s in sessions],
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
        current_app.logger.error(f"Error fetching assigned sessions: {str(e)}")
        return jsonify({'error': 'Failed to fetch assigned sessions'}), 500

@approver_bp.route('/sessions/<int:session_id>/review', methods=['POST'])
@jwt_required()
@require_role('admin', 'manager')
@log_api_access
def create_review(session_id):
    """Create or update a review for a session"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        current_user = get_current_user()
        
        # Check if user can review this session
        if not current_user.has_role('admin'):
            assignment = SessionAssignment.query.filter_by(
                session_id=session_id,
                approver_id=current_user.id,
                status='active'
            ).first()
            if not assignment:
                return jsonify({'error': 'You are not assigned to review this session'}), 403
        
        data = request.get_json()
        if not data.get('decision'):
            return jsonify({'error': 'Decision is required (approve/reject)'}), 400
        
        if data['decision'] not in ['approve', 'reject']:
            return jsonify({'error': 'Decision must be approve or reject'}), 400
        
        data = sanitize_input(data)
        
        # Check if review already exists
        existing_review = SessionReview.query.filter_by(
            session_id=session_id,
            reviewer_id=current_user.id
        ).first()
        
        if existing_review:
            # Update existing review
            review = existing_review
            review.complete_review(
                decision=data['decision'],
                overall_score=data.get('overall_score'),
                internal_comments=data.get('internal_comments'),
                speaker_feedback=data.get('speaker_feedback')
            )
        else:
            # Create new review
            review = SessionReview(
                session_id=session_id,
                reviewer_id=current_user.id
            )
            review.complete_review(
                decision=data['decision'],
                overall_score=data.get('overall_score'),
                internal_comments=data.get('internal_comments'),
                speaker_feedback=data.get('speaker_feedback')
            )
            db.session.add(review)
        
        # Update session status based on review
        if data['decision'] == 'approve':
            session.status = 'approved'
        else:
            session.status = 'rejected'
        
        db.session.commit()
        
        return jsonify({
            'message': f'Session {data["decision"]}d successfully',
            'review': review.to_dict(),
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating review for session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to create review'}), 500

@approver_bp.route('/sessions/<int:session_id>/review-comments', methods=['POST'])
@jwt_required()
@require_role('admin', 'manager')
@log_api_access
def add_review_comment(session_id):
    """Add a comment to a session review"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        current_user = get_current_user()
        
        # Check if user can comment on this session
        if not current_user.has_role('admin'):
            assignment = SessionAssignment.query.filter_by(
                session_id=session_id,
                approver_id=current_user.id,
                status='active'
            ).first()
            if not assignment:
                return jsonify({'error': 'You are not assigned to review this session'}), 403
        
        data = request.get_json()
        if not data.get('comment_text'):
            return jsonify({'error': 'Comment text is required'}), 400
        
        data = sanitize_input(data)
        
        # Get or create review
        review = SessionReview.query.filter_by(
            session_id=session_id,
            reviewer_id=current_user.id
        ).first()
        
        if not review:
            review = SessionReview(
                session_id=session_id,
                reviewer_id=current_user.id
            )
            db.session.add(review)
            db.session.flush()
        
        # Add comment
        comment = SessionReviewComment(
            review_id=review.id,
            commenter_id=current_user.id,
            comment_text=data['comment_text'],
            is_internal=data.get('is_internal', False)
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding comment to session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to add comment'}), 500

@approver_bp.route('/questions', methods=['GET'])
@jwt_required()
@require_role('admin', 'manager')
@log_api_access
def get_questions():
    """Get questions that need responses"""
    try:
        current_user = get_current_user()
        
        # Get query parameters
        status = request.args.get('status', 'open')
        urgent_only = request.args.get('urgent_only', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        if current_user.has_role('admin'):
            # Admins can see all questions
            query = SessionQuestion.query
        else:
            # Managers can only see questions for assigned sessions
            assigned_session_ids = [a.session_id for a in current_user.assigned_sessions if a.status == 'active']
            query = SessionQuestion.query.filter(SessionQuestion.session_id.in_(assigned_session_ids))
        
        # Apply filters
        if status:
            query = query.filter(SessionQuestion.status == status)
        if urgent_only:
            query = query.filter(SessionQuestion.is_urgent == True)
        
        # Order by urgency and creation date
        query = query.order_by(
            SessionQuestion.is_urgent.desc(),
            SessionQuestion.created_at.desc()
        )
        
        # Paginate results
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        questions = pagination.items
        
        return jsonify({
            'questions': [q.to_dict() for q in questions],
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
        current_app.logger.error(f"Error fetching questions: {str(e)}")
        return jsonify({'error': 'Failed to fetch questions'}), 500

@approver_bp.route('/questions/<int:question_id>/respond', methods=['POST'])
@jwt_required()
@require_role('admin', 'manager')
@log_api_access
def respond_to_question(question_id):
    """Respond to a session question"""
    try:
        question = SessionQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        current_user = get_current_user()
        
        # Check if user can respond to this question
        if not current_user.has_role('admin'):
            assignment = SessionAssignment.query.filter_by(
                session_id=question.session_id,
                approver_id=current_user.id,
                status='active'
            ).first()
            if not assignment:
                return jsonify({'error': 'You are not assigned to this session'}), 403
        
        data = request.get_json()
        if not data.get('response_text'):
            return jsonify({'error': 'Response text is required'}), 400
        
        data = sanitize_input(data)
        
        # Create response
        response = SessionQuestionResponse(
            question_id=question.id,
            responded_by=current_user.id,
            response_text=data['response_text'],
            is_internal=data.get('is_internal', False)
        )
        
        db.session.add(response)
        
        # Mark question as answered if this is not an internal response
        if not data.get('is_internal', False):
            question.mark_answered()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Response added successfully',
            'response': response.to_dict(),
            'question': question.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error responding to question {question_id}: {str(e)}")
        return jsonify({'error': 'Failed to respond to question'}), 500

@approver_bp.route('/sessions/<int:session_id>/schedule', methods=['POST'])
@jwt_required()
@require_role('admin', 'manager')
@log_api_access
def schedule_session(session_id):
    """Schedule an approved session"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session.status != 'approved':
            return jsonify({'error': 'Session must be approved before scheduling'}), 400
        
        data = request.get_json()
        required_fields = ['room_id', 'day', 'start_time', 'end_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate room exists
        room = Room.query.get(data['room_id'])
        if not room or not room.is_active:
            return jsonify({'error': 'Invalid room'}), 400
        
        # Parse date and time
        try:
            from datetime import datetime, date, time
            day = datetime.strptime(data['day'], '%Y-%m-%d').date()
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid date or time format'}), 400
        
        # Check for scheduling conflicts
        conflict = SessionSchedule.query.filter(
            and_(
                SessionSchedule.room_id == data['room_id'],
                SessionSchedule.day == day,
                SessionSchedule.status.in_(['tentative', 'confirmed']),
                or_(
                    and_(
                        SessionSchedule.start_time <= start_time,
                        SessionSchedule.end_time > start_time
                    ),
                    and_(
                        SessionSchedule.start_time < end_time,
                        SessionSchedule.end_time >= end_time
                    ),
                    and_(
                        SessionSchedule.start_time >= start_time,
                        SessionSchedule.end_time <= end_time
                    )
                )
            )
        ).first()
        
        if conflict:
            return jsonify({
                'error': 'Scheduling conflict detected',
                'conflict_session_id': conflict.session_id
            }), 409
        
        current_user = get_current_user()
        
        # Create or update schedule
        existing_schedule = SessionSchedule.query.filter_by(session_id=session_id).first()
        if existing_schedule:
            # Update existing schedule
            existing_schedule.room_id = data['room_id']
            existing_schedule.day = day
            existing_schedule.start_time = start_time
            existing_schedule.end_time = end_time
            existing_schedule.setup_notes = data.get('setup_notes')
            existing_schedule.special_requirements = data.get('special_requirements')
            existing_schedule.scheduled_by = current_user.id
            existing_schedule.scheduled_at = datetime.utcnow()
            schedule = existing_schedule
        else:
            # Create new schedule
            schedule = SessionSchedule(
                session_id=session_id,
                room_id=data['room_id'],
                day=day,
                start_time=start_time,
                end_time=end_time,
                scheduled_by=current_user.id,
                setup_notes=data.get('setup_notes'),
                special_requirements=data.get('special_requirements')
            )
            db.session.add(schedule)
        
        # Update session status
        session.status = 'scheduled'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Session scheduled successfully',
            'schedule': schedule.to_dict(),
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error scheduling session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to schedule session'}), 500

@approver_bp.route('/rooms', methods=['GET'])
@jwt_required()
@require_role('admin', 'manager')
@log_api_access
def get_rooms():
    """Get all available rooms"""
    try:
        rooms = Room.query.filter_by(is_active=True).all()
        return jsonify({
            'rooms': [room.to_dict() for room in rooms]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching rooms: {str(e)}")
        return jsonify({'error': 'Failed to fetch rooms'}), 500

@approver_bp.route('/schedule', methods=['GET'])
@jwt_required()
@require_role('admin', 'manager')
@log_api_access
def get_schedule():
    """Get the conference schedule"""
    try:
        # Get query parameters
        day = request.args.get('day')
        room_id = request.args.get('room_id')
        
        query = SessionSchedule.query.filter(
            SessionSchedule.status.in_(['tentative', 'confirmed'])
        )
        
        if day:
            try:
                from datetime import datetime
                day_date = datetime.strptime(day, '%Y-%m-%d').date()
                query = query.filter(SessionSchedule.day == day_date)
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        
        if room_id:
            query = query.filter(SessionSchedule.room_id == room_id)
        
        # Order by day, start time
        schedules = query.order_by(
            SessionSchedule.day,
            SessionSchedule.start_time
        ).all()
        
        return jsonify({
            'schedules': [s.to_dict() for s in schedules]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching schedule: {str(e)}")
        return jsonify({'error': 'Failed to fetch schedule'}), 500

@approver_bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
@require_role('admin', 'manager')
@log_api_access
def get_dashboard_stats():
    """Get dashboard statistics for approvers"""
    try:
        current_user = get_current_user()
        
        if current_user.has_role('admin'):
            # Admin stats - all sessions
            total_sessions = Session.query.count()
            pending_sessions = Session.query.filter_by(status='submitted').count()
            approved_sessions = Session.query.filter_by(status='approved').count()
            rejected_sessions = Session.query.filter_by(status='rejected').count()
            scheduled_sessions = Session.query.filter_by(status='scheduled').count()
            
            # Questions stats
            open_questions = SessionQuestion.query.filter_by(status='open').count()
            urgent_questions = SessionQuestion.query.filter(
                and_(SessionQuestion.status == 'open', SessionQuestion.is_urgent == True)
            ).count()
        else:
            # Manager stats - only assigned sessions
            assigned_session_ids = [a.session_id for a in current_user.assigned_sessions if a.status == 'active']
            
            total_sessions = len(assigned_session_ids)
            pending_sessions = Session.query.filter(
                and_(Session.id.in_(assigned_session_ids), Session.status == 'submitted')
            ).count()
            approved_sessions = Session.query.filter(
                and_(Session.id.in_(assigned_session_ids), Session.status == 'approved')
            ).count()
            rejected_sessions = Session.query.filter(
                and_(Session.id.in_(assigned_session_ids), Session.status == 'rejected')
            ).count()
            scheduled_sessions = Session.query.filter(
                and_(Session.id.in_(assigned_session_ids), Session.status == 'scheduled')
            ).count()
            
            # Questions stats for assigned sessions
            open_questions = SessionQuestion.query.filter(
                and_(
                    SessionQuestion.session_id.in_(assigned_session_ids),
                    SessionQuestion.status == 'open'
                )
            ).count()
            urgent_questions = SessionQuestion.query.filter(
                and_(
                    SessionQuestion.session_id.in_(assigned_session_ids),
                    SessionQuestion.status == 'open',
                    SessionQuestion.is_urgent == True
                )
            ).count()
        
        return jsonify({
            'stats': {
                'total_sessions': total_sessions,
                'pending_sessions': pending_sessions,
                'approved_sessions': approved_sessions,
                'rejected_sessions': rejected_sessions,
                'scheduled_sessions': scheduled_sessions,
                'open_questions': open_questions,
                'urgent_questions': urgent_questions
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard stats'}), 500

