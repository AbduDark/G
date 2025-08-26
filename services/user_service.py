from datetime import datetime
from sqlalchemy.orm import sessionmaker
from config.database import SessionLocal
from models.user import User, Role
from utils.logger import get_logger

class UserService:
    """Service for user management operations"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def create_user(self, user_data, created_by_id):
        """Create new user"""
        db = SessionLocal()
        try:
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                password=user_data['password'],  # Will be hashed by the model
                role_id=user_data['role_id'],
                is_active=user_data.get('is_active', True),
                created_by=created_by_id
            )
            db.add(user)
            db.commit()
            
            self.logger.info(f"User created: {user.email}")
            return user
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating user: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_all_users(self):
        """Get all users"""
        db = SessionLocal()
        try:
            users = db.query(User).order_by(User.created_at.desc()).all()
            return users
        except Exception as e:
            self.logger.error(f"Error fetching users: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
        except Exception as e:
            self.logger.error(f"Error fetching user {user_id}: {str(e)}")
            return None
        finally:
            db.close()
    
    def get_user_by_email(self, email):
        """Get user by email"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            return user
        except Exception as e:
            self.logger.error(f"Error fetching user by email {email}: {str(e)}")
            return None
        finally:
            db.close()
    
    def update_user(self, user_id, update_data):
        """Update user"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            db.commit()
            self.logger.info(f"User updated: {user_id}")
            return user
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating user {user_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def delete_user(self, user_id):
        """Delete user"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            db.delete(user)
            db.commit()
            self.logger.info(f"User deleted: {user_id}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error deleting user {user_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def change_password(self, user_id, new_password):
        """Change user password"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            user.password = new_password  # Will be hashed by the model
            db.commit()
            self.logger.info(f"Password changed for user: {user_id}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error changing password for user {user_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def toggle_user_status(self, user_id):
        """Toggle user active status"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            user.is_active = not user.is_active
            db.commit()
            self.logger.info(f"User status toggled: {user_id} - Active: {user.is_active}")
            return user
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error toggling user status {user_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_all_roles(self):
        """Get all roles"""
        db = SessionLocal()
        try:
            roles = db.query(Role).all()
            return roles
        except Exception as e:
            self.logger.error(f"Error fetching roles: {str(e)}")
            return []
        finally:
            db.close()
    
    def create_role(self, role_data):
        """Create new role"""
        db = SessionLocal()
        try:
            role = Role(
                name=role_data['name'],
                name_ar=role_data['name_ar'],
                permissions=role_data.get('permissions', '{}')
            )
            db.add(role)
            db.commit()
            
            self.logger.info(f"Role created: {role.name}")
            return role
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating role: {str(e)}")
            raise e
        finally:
            db.close()