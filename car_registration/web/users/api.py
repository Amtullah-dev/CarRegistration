from flask import Blueprint, request, jsonify, session as flask_session
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from car_registration.tasks.celery_app import get_db_session
from car_registration.models.user_model import User
from car_registration.web.users.schemas import UserSchema
import datetime
import logging
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from config import Config
from sqlalchemy import create_engine
from flask import jsonify
from car_registration.web.users.validation import validate_json
from car_registration.web.users.schemas import RegisterSchema, LoginSchema, RegisterOutputSchema
from flask_apispec import use_kwargs, marshal_with as output


auth_bp = Blueprint('auth_bp', __name__)
bcrypt = Bcrypt()
user_schema = UserSchema()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['POST'])
@validate_json(RegisterSchema)
@output(RegisterOutputSchema, code=201)
def register(data):
    """
    Register a new user
    Expected JSON: {"username": "string", "password": "string"}
    """
    data = request.get_json()

    if not data:
        return {"message": "No data provided"}, 400

    errors = user_schema.validate(data)
    if errors:
        return {errors}, 400

    with get_db_session() as db_session:
        existing_user = db_session.query(User).filter_by(username=data['username']).first()
        if existing_user:
            return {"message": "User exists"}, 409

        hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user = User(username=data['username'], password=hashed_pw)

        db_session.add(user)

    return {"message": "User registered successfully"}, 201

@auth_bp.route('/login', methods=['POST'])
@validate_json(LoginSchema)
def login(data):
    """
    Login user and store session
    Expected JSON: {"username": "string", "password": "string"}
    """
    # data = request.get_json()
    username = data['username']
    password = data['password']

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Username and password required"}), 400

    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(username=data['username']).first()

        if user and bcrypt.check_password_hash(user.password, data['password']):
            token = create_access_token(
            identity=user.username,
            expires_delta=datetime.timedelta(hours=24)
        )
            flask_session['username'] = user.username
            flask_session['logged_in'] = True
            flask_session['login_time'] = datetime.datetime.utcnow().isoformat()

            return jsonify({
                "message": "Login successful",
                "access-token": token,
                "username": user.username
            }), 200

    return jsonify({"message": "Invalid credentials"}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout user by clearing session
    """
    flask_session.clear()
    return jsonify({"message": "Logged out successfully"}), 200
