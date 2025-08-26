# -*- coding: utf-8 -*-
"""
User and role models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import json

from config.database import Base

class Role(Base):
    """User role model"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    permissions_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    @hybrid_property
    def permissions(self):
        """Get permissions as dictionary"""
        try:
            return json.loads(self.permissions_json)
        except:
            return {}
    
    @permissions.setter
    def permissions(self, value):
        """Set permissions from dictionary"""
        self.permissions_json = json.dumps(value, ensure_ascii=False)
    
    def has_permission(self, module: str, action: str) -> bool:
        """Check if role has specific permission"""
        perms = self.permissions
        if module in perms:
            return action in perms[module]
        return False
    
    def __repr__(self):
        return f"<Role(name='{self.name}')>"

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    
    def has_permission(self, module: str, action: str) -> bool:
        """Check if user has specific permission"""
        if not self.active:
            return False
        return self.role.has_permission(module, action) if self.role else False
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now()
    
    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.name}')>"
