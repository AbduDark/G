import bcrypt
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from config.database import SessionLocal
from models.user import User
from utils.logger import get_logger

class AuthService:
    """Authentication service for user login/logout"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def authenticate(self, email, password):
        """Authenticate user with email and password"""
        db = SessionLocal()
        try:
            # Find user by email
            user = db.query(User).filter(User.email == email, User.active == True).first()
            
            if not user:
                self.logger.warning(f"Login attempt with non-existent email: {email}")
                return None
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                self.logger.warning(f"Failed login attempt for user: {email}")
                return None
            
            # Update last login time
            user.last_login = datetime.now()
            db.commit()
            
            self.logger.info(f"Successful login for user: {email}")
            return user
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            db.rollback()
            raise e
        finally:
            db.close()
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed_password):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
