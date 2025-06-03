from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from models import db, User
from schemas.schemas import UserSchema
import datetime

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

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "User already exists"}), 409

    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(username=data['username'], password=hashed_pw)

    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Registration failed"}), 500


@auth_bp.route('/login', methods=['POST'])
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

    return jsonify({"message": "Invalid credentials"}), 401
