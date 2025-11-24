"""
Authentication API endpoints.

Provides JWT-based authentication for the application with database integration.
Uses bcrypt for password hashing and flask-jwt-extended for token management.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timezone, timedelta
import logging

from backend.db import session_scope
from backend.models import User

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token.
    
    Request Body:
        username: User's username or email
        password: User's password
        
    Returns:
        JSON with access token, refresh token, and user info
    """
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data['username']
        password = data['password']
        
        with session_scope() as session:
            # Find user by username or email
            user = session.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user or not user.check_password(password):
                return jsonify({'error': 'Invalid username or password'}), 401
            
            if not user.is_active:
                return jsonify({'error': 'Account is inactive'}), 403
            
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            session.commit()
            
            # Create JWT tokens
            identity = str(user.id)
            access_token = create_access_token(
                identity=identity,
                additional_claims={'username': user.username, 'email': user.email}
            )
            refresh_token = create_refresh_token(identity=identity)
            
            return jsonify({
                'token': access_token,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict(include_timestamps=False)
            }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Request Body:
        username: Desired username (required)
        password: User's password (required)
        email: User's email (required)
        full_name: User's full name (optional)
        
    Returns:
        JSON with success message and user info
    """
    try:
        data = request.get_json()
        
        required_fields = ['username', 'password', 'email']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Username, password, and email are required'}), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        full_name = data.get('full_name', data.get('name', ''))
        
        with session_scope() as session:
            # Check if username already exists
            if session.query(User).filter_by(username=username).first():
                return jsonify({'error': 'Username already exists'}), 409
            
            # Check if email already exists
            if session.query(User).filter_by(email=email).first():
                return jsonify({'error': 'Email already exists'}), 409
            
            # Create new user
            user = User(
                username=username,
                email=email,
                full_name=full_name
            )
            user.set_password(password)
            
            session.add(user)
            session.commit()
            
            return jsonify({
                'message': 'User registered successfully',
                'user': user.to_dict(include_timestamps=False)
            }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verify JWT token validity and return user info.
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        JSON with token validity and user info
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        
        with session_scope() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not user.is_active:
                return jsonify({'error': 'Account is inactive'}), 403
            
            return jsonify({
                'valid': True,
                'user': user.to_dict(include_timestamps=False)
            }), 200
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token.
    
    Headers:
        Authorization: Bearer <refresh_token>
        
    Returns:
        JSON with new access token
    """
    try:
        user_id = get_jwt_identity()
        
        with session_scope() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user or not user.is_active:
                return jsonify({'error': 'Invalid user'}), 401
            
            # Create new access token
            access_token = create_access_token(
                identity=user_id,
                additional_claims={'username': user.username, 'email': user.email}
            )
            
            return jsonify({
                'access_token': access_token,
                'token': access_token
            }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user information.
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        JSON with user info
    """
    try:
        user_id = get_jwt_identity()
        
        with session_scope() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({
                'user': user.to_dict(include_timestamps=True)
            }), 200
        
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
