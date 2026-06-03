"""
Admin module routes - User management, Role management, System configuration
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User, Role, AuditLog
from app import db

admin_bp = Blueprint('admin', __name__)


# ==================== USER MANAGEMENT ====================

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    users = User.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'users': [user.to_dict() for user in users.items],
        'total': users.total,
        'pages': users.pages,
        'current_page': page
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get single user by ID"""
    user = User.query.get_or_404(user_id)
    return jsonify({'user': user.to_dict()}), 200


@admin_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Check if role exists
    role = Role.query.get(data['role_id'])
    if not role:
        return jsonify({'error': 'Role not found'}), 404
    
    # Create user
    user = User(
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data.get('phone'),
        role_id=data['role_id'],
        department=data.get('department'),
        is_superuser=data.get('is_superuser', False)
    )
    user.set_password(data['password'])
    user.save()
    
    # Audit log
    current_user_id = get_jwt_identity()
    audit_log = AuditLog(
        user_id=current_user_id,
        action='CREATE',
        module='admin',
        table_name='users',
        record_id=user.id,
        new_values=user.to_dict()
    )
    audit_log.save()
    
    return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update existing user"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    old_values = user.to_dict()
    
    # Update fields
    if 'username' in data:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        user.username = data['username']
    
    if 'email' in data:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        user.email = data['email']
    
    if 'first_name' in data:
        user.first_name = data['first_name']
    
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    if 'phone' in data:
        user.phone = data['phone']
    
    if 'role_id' in data:
        role = Role.query.get(data['role_id'])
        if not role:
            return jsonify({'error': 'Role not found'}), 404
        user.role_id = data['role_id']
    
    if 'department' in data:
        user.department = data['department']
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    if 'is_superuser' in data:
        user.is_superuser = data['is_superuser']
    
    if 'password' in data:
        user.set_password(data['password'])
    
    user.save()
    
    # Audit log
    current_user_id = get_jwt_identity()
    audit_log = AuditLog(
        user_id=current_user_id,
        action='UPDATE',
        module='admin',
        table_name='users',
        record_id=user.id,
        old_values=old_values,
        new_values=user.to_dict()
    )
    audit_log.save()
    
    return jsonify({'message': 'User updated successfully', 'user': user.to_dict()}), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete user (soft delete)"""
    user = User.query.get_or_404(user_id)
    
    old_values = user.to_dict()
    
    user.is_active = False
    user.save()
    
    # Audit log
    current_user_id = get_jwt_identity()
    audit_log = AuditLog(
        user_id=current_user_id,
        action='DELETE',
        module='admin',
        table_name='users',
        record_id=user.id,
        old_values=old_values
    )
    audit_log.save()
    
    return jsonify({'message': 'User deleted successfully'}), 200


# ==================== ROLE MANAGEMENT ====================

@admin_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """Get all roles"""
    roles = Role.query.filter_by(is_active=True).all()
    return jsonify({'roles': [role.to_dict() for role in roles]}), 200


@admin_bp.route('/roles/<int:role_id>', methods=['GET'])
@jwt_required()
def get_role(role_id):
    """Get single role by ID"""
    role = Role.query.get_or_404(role_id)
    return jsonify({'role': role.to_dict()}), 200


@admin_bp.route('/roles', methods=['POST'])
@jwt_required()
def create_role():
    """Create new role"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Role name is required'}), 400
    
    # Check if role already exists
    if Role.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Role already exists'}), 400
    
    role = Role(
        name=data['name'],
        description=data.get('description'),
        permissions=data.get('permissions', [])
    )
    role.save()
    
    # Audit log
    current_user_id = get_jwt_identity()
    audit_log = AuditLog(
        user_id=current_user_id,
        action='CREATE',
        module='admin',
        table_name='roles',
        record_id=role.id,
        new_values=role.to_dict()
    )
    audit_log.save()
    
    return jsonify({'message': 'Role created successfully', 'role': role.to_dict()}), 201


@admin_bp.route('/roles/<int:role_id>', methods=['PUT'])
@jwt_required()
def update_role(role_id):
    """Update existing role"""
    role = Role.query.get_or_404(role_id)
    data = request.get_json()
    
    old_values = role.to_dict()
    
    if 'name' in data:
        if Role.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Role already exists'}), 400
        role.name = data['name']
    
    if 'description' in data:
        role.description = data['description']
    
    if 'permissions' in data:
        role.permissions = data['permissions']
    
    role.save()
    
    # Audit log
    current_user_id = get_jwt_identity()
    audit_log = AuditLog(
        user_id=current_user_id,
        action='UPDATE',
        module='admin',
        table_name='roles',
        record_id=role.id,
        old_values=old_values,
        new_values=role.to_dict()
    )
    audit_log.save()
    
    return jsonify({'message': 'Role updated successfully', 'role': role.to_dict()}), 200


@admin_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@jwt_required()
def delete_role(role_id):
    """Delete role (soft delete)"""
    role = Role.query.get_or_404(role_id)
    
    old_values = role.to_dict()
    
    role.is_active = False
    role.save()
    
    # Audit log
    current_user_id = get_jwt_identity()
    audit_log = AuditLog(
        user_id=current_user_id,
        action='DELETE',
        module='admin',
        table_name='roles',
        record_id=role.id,
        old_values=old_values
    )
    audit_log.save()
    
    return jsonify({'message': 'Role deleted successfully'}), 200


# ==================== AUDIT LOGS ====================

@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """Get audit logs with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    user_id = request.args.get('user_id', type=int)
    module = request.args.get('module')
    action = request.args.get('action')
    
    query = AuditLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if module:
        query = query.filter_by(module=module)
    if action:
        query = query.filter_by(action=action)
    
    audit_logs = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'audit_logs': [log.to_dict() for log in audit_logs.items],
        'total': audit_logs.total,
        'pages': audit_logs.pages,
        'current_page': page
    }), 200
