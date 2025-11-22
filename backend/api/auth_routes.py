"""
Authentication API endpoints.

Provides JWT-based authentication for the application.
For development purposes, uses simple in-memory user storage.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import jwt
import hashlib
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# In-memory user storage (for development only)
# In production, use a proper database
USERS = {
    'demo': {
        'password': hashlib.sha256('demo123'.encode()).hexdigest(),
        'email': 'demo@example.com',
        'name': 'Demo User'
    },
    'admin': {
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),
        'email': 'admin@example.com',
        'name': 'Admin User'
    }
}

SECRET_KEY = 'jwt-secret-key-change-in-production'


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token.
    
    Request Body:
        username: User's username
        password: User's password
        
    Returns:
        JSON with JWT token and user info
    """
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data['username']
        password = data['password']
        
        # Hash the provided password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Check if user exists and password matches
        if username not in USERS or USERS[username]['password'] != password_hash:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Generate JWT token
        token_payload = {
            'username': username,
            'email': USERS[username]['email'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': {
                'username': username,
                'email': USERS[username]['email'],
                'name': USERS[username]['name']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Request Body:
        username: Desired username
        password: User's password
        email: User's email
        name: User's full name
        
    Returns:
        JSON with success message
    """
    try:
        data = request.get_json()
        
        required_fields = ['username', 'password', 'email', 'name']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'All fields are required'}), 400
        
        username = data['username']
        
        # Check if user already exists
        if username in USERS:
            return jsonify({'error': 'Username already exists'}), 409
        
        # Hash password and store user
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        USERS[username] = {
            'password': password_hash,
            'email': data['email'],
            'name': data['name']
        }
        
        return jsonify({'message': 'User registered successfully'}), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """
    Verify JWT token validity.
    
    Headers:
        Authorization: Bearer <token>
        
    Returns:
        JSON with token validity and user info
    """
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify and decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        return jsonify({
            'valid': True,
            'user': {
                'username': payload['username'],
                'email': payload['email']
            }
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
