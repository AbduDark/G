# -*- coding: utf-8 -*-
"""
Authentication service for user management
"""

import logging
from datetime import datetime
from typing import Optional
import bcrypt

from config.database import get_db_session
from models.user import User, Role
from models.audit import AuditLog

class AuthService:
    """Service for authentication and user management"""
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        session = get_db_session()
        try:
            user = session.query(User).filter_by(email=email, active=True).first()
            
            if not user:
                return None
                
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Update last login
                user.update_last_login()
                session.commit()
                return user
            else:
                return None
                
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return None
        finally:
            session.close()
            
    def create_user(self, user_data: dict, created_by_id: int) -> Optional[int]:
        """Create new user"""
        session = get_db_session()
        try:
            # Check for duplicate email
            existing_user = session.query(User).filter_by(email=user_data['email']).first()
            if existing_user:
                raise ValueError("البريد الإلكتروني موجود مسبقاً")
                
            # Hash password
            password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
            
            # Create user
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                password_hash=password_hash.decode('utf-8'),
                role_id=user_data['role_id'],
                active=user_data.get('active', True),
                created_at=datetime.now()
            )
            
            session.add(user)
            session.commit()
            
            # Log action
            AuditLog.log_action(
                session, created_by_id, "create", "users",
                record_id=user.id, details=f"Created user: {user.name} ({user.email})"
            )
            session.commit()
            
            return user.id
            
        except Exception as e:
            session.rollback()
            logging.error(f"Create user error: {e}")
            raise
        finally:
            session.close()
            
    def update_user(self, user_id: int, user_data: dict, updated_by_id: int) -> bool:
        """Update existing user"""
        session = get_db_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                raise ValueError("المستخدم غير موجود")
                
            # Check for duplicate email (excluding current user)
            if 'email' in user_data:
                existing_user = session.query(User).filter(
                    User.email == user_data['email'],
                    User.id != user_id
                ).first()
                if existing_user:
                    raise ValueError("البريد الإلكتروني موجود مسبقاً")
                    
            # Update fields
            if 'name' in user_data:
                user.name = user_data['name']
            if 'email' in user_data:
                user.email = user_data['email']
            if 'role_id' in user_data:
                user.role_id = user_data['role_id']
            if 'active' in user_data:
                user.active = user_data['active']
                
            # Update password if provided
            if 'password' in user_data and user_data['password']:
                password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
                user.password_hash = password_hash.decode('utf-8')
                
            session.commit()
            
            # Log action
            AuditLog.log_action(
                session, updated_by_id, "update", "users",
                record_id=user.id, details=f"Updated user: {user.name} ({user.email})"
            )
            session.commit()
            
            return True
            
        except Exception as e:
            session.rollback()
            logging.error(f"Update user error: {e}")
            raise
        finally:
            session.close()
            
    def reset_user_password(self, user_id: int, new_password: str, reset_by_id: int) -> bool:
        """Reset user password"""
        session = get_db_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                raise ValueError("المستخدم غير موجود")
                
            # Hash new password
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            user.password_hash = password_hash.decode('utf-8')
            
            session.commit()
            
            # Log action
            AuditLog.log_action(
                session, reset_by_id, "update", "users",
                record_id=user.id, details=f"Password reset for user: {user.name}"
            )
            session.commit()
            
            return True
            
        except Exception as e:
            session.rollback()
            logging.error(f"Reset password error: {e}")
            raise
        finally:
            session.close()
            
    def delete_user(self, user_id: int, deleted_by_id: int) -> bool:
        """Delete user (soft delete by deactivating)"""
        session = get_db_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                raise ValueError("المستخدم غير موجود")
                
            # Deactivate instead of hard delete
            user.active = False
            session.commit()
            
            # Log action
            AuditLog.log_action(
                session, deleted_by_id, "delete", "users",
                record_id=user.id, details=f"Deactivated user: {user.name}"
            )
            session.commit()
            
            return True
            
        except Exception as e:
            session.rollback()
            logging.error(f"Delete user error: {e}")
            raise
        finally:
            session.close()
            
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        session = get_db_session()
        try:
            return session.query(User).get(user_id)
        finally:
            session.close()
            
    def get_all_users(self) -> list:
        """Get all users"""
        session = get_db_session()
        try:
            return session.query(User).join(Role).all()
        finally:
            session.close()
            
    def get_active_users(self) -> list:
        """Get all active users"""
        session = get_db_session()
        try:
            return session.query(User).filter_by(active=True).join(Role).all()
        finally:
            session.close()
            
    def create_role(self, role_data: dict, created_by_id: int) -> Optional[int]:
        """Create new role"""
        session = get_db_session()
        try:
            # Check for duplicate name
            existing_role = session.query(Role).filter_by(name=role_data['name']).first()
            if existing_role:
                raise ValueError("اسم الدور موجود مسبقاً")
                
            role = Role(
                name=role_data['name'],
                permissions=role_data.get('permissions', {}),
                created_at=datetime.now()
            )
            
            session.add(role)
            session.commit()
            
            # Log action
            AuditLog.log_action(
                session, created_by_id, "create", "roles",
                record_id=role.id, details=f"Created role: {role.name}"
            )
            session.commit()
            
            return role.id
            
        except Exception as e:
            session.rollback()
            logging.error(f"Create role error: {e}")
            raise
        finally:
            session.close()
            
    def update_role(self, role_id: int, role_data: dict, updated_by_id: int) -> bool:
        """Update existing role"""
        session = get_db_session()
        try:
            role = session.query(Role).get(role_id)
            if not role:
                raise ValueError("الدور غير موجود")
                
            # Check for duplicate name (excluding current role)
            if 'name' in role_data:
                existing_role = session.query(Role).filter(
                    Role.name == role_data['name'],
                    Role.id != role_id
                ).first()
                if existing_role:
                    raise ValueError("اسم الدور موجود مسبقاً")
                    
            # Update fields
            if 'name' in role_data:
                role.name = role_data['name']
            if 'permissions' in role_data:
                role.permissions = role_data['permissions']
                
            session.commit()
            
            # Log action
            AuditLog.log_action(
                session, updated_by_id, "update", "roles",
                record_id=role.id, details=f"Updated role: {role.name}"
            )
            session.commit()
            
            return True
            
        except Exception as e:
            session.rollback()
            logging.error(f"Update role error: {e}")
            raise
        finally:
            session.close()
            
    def get_all_roles(self) -> list:
        """Get all roles"""
        session = get_db_session()
        try:
            return session.query(Role).all()
        finally:
            session.close()
