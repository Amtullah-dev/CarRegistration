# app.py
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from app.models.user_model import User
from app.models.user_model import User
from app.models.car_model import Car
from app.database import db
from app.schemas import ma, UserSchema, CarSchema
from app.config import config
import requests
import datetime
import os

app = Flask(__name__)


def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    bcrypt = Bcrypt(app)
    jwt = JWTManager(app)
    
    return app, bcrypt, jwt

app, bcrypt, jwt = create_app()

# Initialize Celery - Try SQLite broker first
try:
    from app.celery.celery_worker_sqlite import make_celery
    celery = make_celery(app)
    print("Using SQLite broker for Celery")
except ImportError:
    try:
        from app.celery.celery_worker import make_celery
        celery = make_celery(app)
        print("Using filesystem broker for Celery")
    except Exception as e:
        print(f"Celery initialization failed: {e}")
        celery = None

# Schemas
user_schema = UserSchema()
car_schema = CarSchema()
cars_schema = CarSchema(many=True)


# ---------------------- Auth ---------------------- #
@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    Expected JSON: {"username": "string", "password": "string"}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    errors = user_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "User already exists"}), 409
    
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(username=data['username'], password=hashed_pw)
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Registration failed"}), 500


@app.route('/login', methods=['POST'])
def login():
    """
    Login user and return JWT token
    Expected JSON: {"username": "string", "password": "string"}
    """
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Username and password required"}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        # Create token with expiration
        token = create_access_token(
            identity=user.username,
            expires_delta=datetime.timedelta(hours=24)
        )
        return jsonify({
            "access_token": token,
            "message": "Login successful"
        }), 200
    print(token)
    return jsonify({"message": "Invalid credentials"}), 401


# ---------------------- Manual Sync Cars ---------------------- #
@app.route('/sync-cars', methods=['POST'])
@jwt_required()
def sync_cars():
    """
    Manual trigger for car data synchronization
    Requires JWT authentication
    """
    if celery is None:
        # Fallback to direct sync if Celery is not available
        try:
            from app.celery.celery_worker_sqlite import sync_car_data_function
            result = sync_car_data_function()
            return jsonify({
                "message": "Car data sync completed (direct execution)",
                "result": result
            }), 200
        except Exception as e:
            return jsonify({"message": f"Sync failed: {str(e)}"}), 500
    
    try:
        # Try SQLite broker first
        try:
            from app.celery.celery_worker_sqlite import sync_car_data_task
            task = sync_car_data_task.delay()
        except ImportError:
            from app.celery.celery_worker import sync_car_data_task
            task = sync_car_data_task.delay()
        
        return jsonify({
            "message": "Car data sync initiated",
            "task_id": task.id
        }), 200
    except Exception as e:
        return jsonify({"message": f"Failed to initiate sync: {str(e)}"}), 500


@app.route('/sync-status/<task_id>', methods=['GET'])
@jwt_required()
def get_sync_status(task_id):
    """
    Check the status of a sync task
    """
    if celery is None:
        return jsonify({"message": "Celery not available"}), 503
    
    try:
        # Try SQLite broker first
        try:
            from app.celery.celery_worker_sqlite import sync_car_data_task
            task = sync_car_data_task.AsyncResult(task_id)
        except ImportError:
            from app.celery.celery_worker import sync_car_data_task
            task = sync_car_data_task.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'Task is waiting to be processed'
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'status': task.info.get('status', ''),
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1)
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'status': 'Task completed successfully',
                'result': task.info
            }
        else:  # FAILURE
            response = {
                'state': task.state,
                'status': 'Task failed',
                'error': str(task.info)
            }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"message": f"Failed to get task status: {str(e)}"}), 500


# ---------------------- Search API ---------------------- #
@app.route('/cars', methods=['GET'])
@jwt_required()
def get_cars():
    """
    Search and filter cars with pagination
    Query parameters:
    - make: Filter by car make (partial match)
    - model: Filter by car model (partial match)
    - year: Filter by exact year
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)
    """
    # Get query parameters
    make = request.args.get('make', '').strip()
    model = request.args.get('model', '').strip()
    year = request.args.get('year', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)  # Limit max per_page
    
    # Validate pagination parameters
    if page < 1:
        return jsonify({"message": "Page must be greater than 0"}), 400
    if per_page < 1:
        return jsonify({"message": "Per page must be greater than 0"}), 400

    try:
        # Build query with filters
        query = Car.query
        
        if make:
            query = query.filter(Car.make.ilike(f"%{make}%"))
        if model:
            query = query.filter(Car.model.ilike(f"%{model}%"))
        if year:
            # Validate year range
            if year < 2012 or year > 2022:
                return jsonify({"message": "Year must be between 2012 and 2022"}), 400
            query = query.filter_by(year=year)

        # Apply pagination
        paginated = query.paginate(
            page=page, 
            per_page=per_page,
            error_out=False
        )
        
        # Prepare response
        response = {
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page,
            "per_page": per_page,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev,
            "cars": cars_schema.dump(paginated.items)
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"message": f"Search failed: {str(e)}"}), 500


@app.route('/cars/stats', methods=['GET'])
@jwt_required()
def get_car_stats():
    """
    Get statistics about the car database
    """
    try:
        total_cars = Car.query.count()
        unique_makes = db.session.query(Car.make).distinct().count()
        unique_models = db.session.query(Car.model).distinct().count()
        year_range = db.session.query(
            db.func.min(Car.year).label('min_year'),
            db.func.max(Car.year).label('max_year')
        ).first()
        
        return jsonify({
            "total_cars": total_cars,
            "unique_makes": unique_makes,
            "unique_models": unique_models,
            "year_range": {
                "min": year_range.min_year,
                "max": year_range.max_year
            }
        }), 200
    except Exception as e:
        return jsonify({"message": f"Failed to get stats: {str(e)}"}), 500


# ---------------------- Health Check ---------------------- #
@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "database": "connected"
    }), 200


# ---------------------- Error Handlers ---------------------- #
@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"message": "Internal server error"}), 500


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"message": "Token has expired"}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"message": "Invalid token"}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"message": "Authorization token required"}), 401


def create_directories():
    """Create necessary directories for Celery filesystem broker"""
    directories = [
        './celery_data/out',
        './celery_data/processed',
        './celery_results'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("Created necessary directories for Celery filesystem broker")


if __name__ == '__main__':
    with app.app_context():
        # Create directories for Celery
        create_directories()
        from app.models.user_model import User
        from app.models.car_model import Car
        # Create database tables
        db.create_all()
        print("Database tables created")
        
        # Initial sync (optional - comment out if you want only scheduled sync)
        print("Starting initial car data sync...")
        try:
            from app.celery.celery_worker_sqlite import sync_car_data_function
            sync_car_data_function()
        except ImportError:
            try:
                from app.celery.celery_worker import sync_car_data_function
                sync_car_data_function()
            except ImportError:
                print("Warning: Could not perform initial sync - sync functions not available")
        
    app.run(debug=True, host='0.0.0.0', port=5000)