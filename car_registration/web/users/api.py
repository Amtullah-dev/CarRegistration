from flask import Blueprint, request, jsonify, session as flask_session
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from app import get_db_session
from car_registration.models.user_model import User
from car_registration.web.users.schemas import UserSchema
import datetime
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from config import Config
from sqlalchemy import create_engine

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()
user_schema = UserSchema()


@auth_bp.route('/register', methods=['POST'])
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

    with get_db_session() as db_session:
        existing_user = db_session.query(User).filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({"message": "User already exists"}), 409

        hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user = User(username=data['username'], password=hashed_pw)

        db_session.add(user)

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user and store session
    Expected JSON: {"username": "string", "password": "string"}
    """
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Username and password required"}), 400

    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(username=data['username']).first()

        if user and bcrypt.check_password_hash(user.password, data['password']):
            token = create_access_token(
            identity=user.username,
            expires_delta=datetime.timedelta(hours=24)
        )
            # Store user info in flask session
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
