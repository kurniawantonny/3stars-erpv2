"""
Authentication routes - Login, Logout, Token refresh
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime
from app import db
from app.models.user import User, AuditLog
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    auth_service = AuthService()
    result = auth_service.authenticate(data['username'], data['password'])
    
    if not result['success']:
        return jsonify({'error': result['message']}), 401
    
    user = result['user']
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    # Update last login
    user.last_login = datetime.utcnow()
    user.save()
    
    # Log audit
    audit_log = AuditLog(
        user_id=user.id,
        action='LOGIN',
        module='auth',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    audit_log.save()
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout endpoint
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    responses:
      200:
        description: Logout successful
    """
    current_user_id = get_jwt_identity()
    
    # Log audit
    audit_log = AuditLog(
        user_id=current_user_id,
        action='LOGOUT',
        module='auth',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    audit_log.save()
    
    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    responses:
      200:
        description: New access token
    """
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    
    return jsonify({'access_token': new_access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user info
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    responses:
      200:
        description: User information
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: passwords
        required: true
        schema:
          type: object
          properties:
            old_password:
              type: string
            new_password:
              type: string
    responses:
      200:
        description: Password changed successfully
      400:
        description: Invalid old password
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': 'Old password and new password are required'}), 400
    
    user = User.query.get(current_user_id)
    
    if not user.check_password(data['old_password']):
        return jsonify({'error': 'Invalid old password'}), 400
    
    user.set_password(data['new_password'])
    user.save()
    
    return jsonify({'message': 'Password changed successfully'}), 200
