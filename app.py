import logging
import os

from flask import Flask, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from config import Config
from models.database import db
from schemas.schemas import ma

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
ma.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Initialize Celery
try:
    from tasks.celery.celery_app import celery

    celery.conf.update(
        task_routes={
            'tasks.celery.celery_app.sync_car_data_task': {
                'queue': 'car_sync'
            }
        }
    )

    app.extensions['celery'] = celery
    logger.info("Celery initialized successfully")

except Exception as e:
    logger.error(f"Celery initialization failed: {e}")
    app.extensions['celery'] = None

# Register route blueprints
from tasks.car_registration_tasks import register_routes

register_routes(app)


# JWT error handlers
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
    """Create necessary directories for Celery filesystem broker."""
    directories = [
        './celery_data/out',
        './celery_data/processed',
        './celery_results',
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    logger.info("Created necessary directories for Celery broker")


if __name__ == '__main__':
    with app.app_context():
        create_directories()
        db.create_all()

        try:
            from tasks.celery.celery_app import sync_car_data_function
            logger.info("Starting initial car data sync...")
            result = sync_car_data_function()
            logger.info(f"Initial sync result: {result}")
        except ImportError:
            logger.warning("Could not import sync function from celery_app")
        except Exception as e:
            logger.warning(f"Initial sync failed: {e}")

    app.run(debug=True, host='0.0.0.0', port=5000)
