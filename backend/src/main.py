import os
from sqlalchemy import text
import sys
# DON'T CHANGE: Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from src.models import (
    db, User, Role, AuditLog, SessionType, Room
)
from src.routes.user import user_bp
from src.routes.auth import auth_bp, jwt
from src.routes.sessions import sessions_bp
from src.routes.approver import approver_bp
from src.routes.admin import admin_bp
from src.routes.files import files_bp
from src.routes.notifications import notifications_bp
from src.utils.security import SecurityHeaders

def create_app():
    app = Flask(__name__)
    
    # Production configuration
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = 'this-is-a-super-secret-key-for-testing'
    
    # Database configuration for Render
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        # Fix for SQLAlchemy 1.4+ compatibility
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # File upload configuration
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
    
    # Production settings
    app.config['DEBUG'] = os.environ.get('DEBUG', 'false').lower() == 'true'
    app.config['TESTING'] = False
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate = Migrate(app, db)
    
    # Enable CORS for all origins (required for frontend-backend communication)
    CORS(app, origins="*", supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(sessions_bp, url_prefix='/api/sessions')
    app.register_blueprint(approver_bp, url_prefix='/api/approver')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    
    # Health check endpoint for Render
    @app.route('/api/health')
    def health_check():
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 500
    
    @app.after_request
    def after_request(response):
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:;"
        
        # CORS headers for production
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return {'error': 'File too large. Maximum size is 100MB.'}, 413
    
    # Serve static files in production
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_static(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    return app

def init_database(app):
    """Initialize database with default data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Check if roles exist
        if not Role.query.first():
            # Create default roles
            admin_role = Role(name='Admin', description='System administrator with full access')
            manager_role = Role(name='Manager', description='Conference manager with review and approval permissions')
            speaker_role = Role(name='Speaker', description='Conference speaker with submission permissions')
            
            db.session.add_all([admin_role, manager_role, speaker_role])
            db.session.commit()
            print("✓ Default roles created")
        
        # Check if admin user exists
        if not User.query.filter_by(email='admin@cybercon2025.com').first():
            admin_role = Role.query.filter_by(name='Admin').first()
            admin_user = User(
                email='admin@cybercon2025.com',
                password='CyberconAdmin2025!',
                first_name='System',
                last_name='Administrator',
                organisation='Cybercon Melbourne 2025',
                phone='+61400000000',
                is_active=True,
                email_verified=True
            )
            admin_user.roles.append(admin_role)
        
            db.session.add(admin_user)
            db.session.commit()
            print("✓ Default admin user created")
        
        # Check if session types exist
        if not SessionType.query.first():
            session_types = [
                SessionType(name='Keynote', description='Main conference keynote presentation', duration_minutes=60),
                SessionType(name='Technical', description='Technical presentation or workshop', duration_minutes=45),
                SessionType(name='Workshop', description='Interactive workshop session', duration_minutes=90),
                SessionType(name='Panel', description='Panel discussion with multiple speakers', duration_minutes=60),
                SessionType(name='Lightning Talk', description='Short presentation', duration_minutes=15),
                SessionType(name='Demo', description='Product or technology demonstration', duration_minutes=30)
            ]
            
            db.session.add_all(session_types)
            db.session.commit()
            print("✓ Default session types created")
        
        # Check if rooms exist
        #if not Room.query.first():
        #    rooms = [
        #       Room(name='Main Auditorium', capacity=500, location='Level 1', 
        #             equipment='Projector, Audio System, Live Streaming'),
        #        Room(name='Conference Room A', capacity=100, location='Level 2', 
        #             equipment='Projector, Audio System'),
        #        Room(name='Conference Room B', capacity=100, location='Level 2', 
        #             equipment='Projector, Audio System'),
        #        Room(name='Workshop Space', capacity=50, location='Level 3', 
        #             equipment='Interactive Whiteboards, Breakout Areas')
        #    ]
        #    
        #    db.session.add_all(rooms)
        #    db.session.commit()
        #    print("✓ Default rooms created")
        
        print("✓ Database initialization complete")

if __name__ == '__main__':
    app = create_app()
    
    # Initialize database on startup
    init_database(app)
    
    # Get port from environment variable (Render sets this automatically)
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting Cybercon Melbourne 2025 Speaker System on {host}:{port}")
    print(f"🔧 Debug mode: {app.config['DEBUG']}")
    print(f"🗄️  Database: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    
    # Run the application
    app.run(host=host, port=port, debug=app.config['DEBUG'])

