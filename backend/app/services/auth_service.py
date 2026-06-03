"""
Authentication service for business logic
"""

from app.models.user import User


class AuthService:
    """Service class for authentication operations"""
    
    def authenticate(self, username, password):
        """
        Authenticate user with username and password
        
        Args:
            username (str): Username or email
            password (str): User password
            
        Returns:
            dict: Authentication result with success status and user data
        """
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return {
                'success': False,
                'message': 'Invalid username or password',
                'user': None
            }
        
        if not user.is_active:
            return {
                'success': False,
                'message': 'Account is deactivated',
                'user': None
            }
        
        if not user.check_password(password):
            return {
                'success': False,
                'message': 'Invalid username or password',
                'user': None
            }
        
        return {
            'success': True,
            'message': 'Authentication successful',
            'user': user
        }
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    def get_user_by_email(self, email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()
    
    def get_user_by_username(self, username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()
