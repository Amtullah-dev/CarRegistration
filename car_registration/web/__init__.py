# tasks/car-registration-tasks/__init__.py
from car_registration.web.users.api import auth_bp
from car_registration.web.cars.api import car_bp

def register_routes(app):
    """Register all route blueprints with the Flask app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(car_bp)
    