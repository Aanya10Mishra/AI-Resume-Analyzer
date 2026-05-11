"""
Authentication Routes
Features: Login, Signup, Password Reset, Profile Management
"""
from flask import Blueprint, request, jsonify
from models.database import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import secrets
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# In-memory token storage (use Redis or database for production)
password_reset_tokens = {}

def _is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def _is_strong_password(password):
    """Check if password meets security requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain number"
    return True, "Password is strong"

def _generate_reset_token():
    """Generate a secure reset token"""
    return secrets.token_urlsafe(32)

# ==================== SIGNUP ====================

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    User signup endpoint
    
    Body:
    {
        "email": "user@example.com",
        "password": "SecurePass123",
        "full_name": "John Doe",
        "role": "student"  # 'student', 'employee', 'hr'
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ['email', 'password', 'full_name', 'role']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        full_name = data['full_name'].strip()
        role = data['role'].lower()
        
        # Validate email format
        if not _is_valid_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_strong, message = _is_strong_password(password)
        if not is_strong:
            return jsonify({'error': message}), 400
        
        # Validate role
        if not User.validate_role(role):
            return jsonify({'error': 'Invalid role'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        password_hash = generate_password_hash(password)
        new_user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"✅ New user signup: {email} (Role: {role})")
        
        return jsonify({
            'message': 'Signup successful',
            'user': new_user.to_dict(),
            'status': 'success'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Signup error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== LOGIN ====================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    
    Body:
    {
        "email": "user@example.com",
        "password": "SecurePass123"
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ User login: {email}")
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== PASSWORD RESET ====================

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Request password reset token
    
    Body:
    {
        "email": "user@example.com"
    }
    
    Returns:
    - Reset token (in production, send via email)
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        
        email = data['email'].lower().strip()
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if email exists (security best practice)
            # But for development, we can indicate
            return jsonify({
                'message': 'If email exists, a reset token has been sent',
                'status': 'success'
            }), 200
        
        # Generate reset token
        reset_token = _generate_reset_token()
        token_expiry = datetime.utcnow() + timedelta(hours=1)  # Valid for 1 hour
        
        # Store token (in production, use database)
        password_reset_tokens[reset_token] = {
            'user_id': user.id,
            'email': user.email,
            'expiry': token_expiry
        }
        
        logger.info(f"✅ Password reset token generated for: {email}")
        
        return jsonify({
            'message': 'Password reset token sent',
            'reset_token': reset_token,  # In production, send via email
            'token_expiry': token_expiry.isoformat(),
            'instructions': 'Use this token to reset your password within 1 hour',
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Forgot password error: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password using token
    
    Body:
    {
        "reset_token": "generated_token",
        "new_password": "NewSecurePass456"
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('reset_token') or not data.get('new_password'):
            return jsonify({'error': 'Reset token and new password required'}), 400
        
        reset_token = data['reset_token']
        new_password = data['new_password']
        
        # Validate token
        if reset_token not in password_reset_tokens:
            return jsonify({'error': 'Invalid or expired reset token'}), 400
        
        token_data = password_reset_tokens[reset_token]
        
        # Check if token expired
        if datetime.utcnow() > token_data['expiry']:
            del password_reset_tokens[reset_token]
            return jsonify({'error': 'Reset token has expired'}), 400
        
        # Validate new password
        is_strong, message = _is_strong_password(new_password)
        if not is_strong:
            return jsonify({'error': message}), 400
        
        # Get user and update password
        user = User.query.get(token_data['user_id'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        # Delete token
        del password_reset_tokens[reset_token]
        
        logger.info(f"✅ Password reset successful for: {user.email}")
        
        return jsonify({
            'message': 'Password reset successfully',
            'status': 'success'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Reset password error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== CHANGE PASSWORD ====================

@auth_bp.route('/change-password/<int:user_id>', methods=['POST'])
def change_password(user_id):
    """
    Change password for logged-in user
    
    Body:
    {
        "current_password": "OldPass123",
        "new_password": "NewSecurePass456"
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current and new password required'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Get user
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if not check_password_hash(user.password_hash, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_strong, message = _is_strong_password(new_password)
        if not is_strong:
            return jsonify({'error': message}), 400
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        logger.info(f"✅ Password changed for user: {user.email}")
        
        return jsonify({
            'message': 'Password changed successfully',
            'status': 'success'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Change password error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== USER PROFILE ====================

@auth_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile information"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logger.error(f"❌ Get user error: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update user profile
    
    Body:
    {
        "full_name": "Updated Name",
        "experience_level": "senior",
        "company_name": "Tech Corp"
    }
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name'].strip()
        if 'experience_level' in data:
            user.experience_level = data['experience_level']
        if 'company_name' in data:
            user.company_name = data['company_name']
        if 'department' in data:
            user.department = data['department']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ User profile updated: {user.email}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Update user error: {e}")
        return jsonify({'error': str(e)}), 500
