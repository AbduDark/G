from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Role(Base):
    """User roles and permissions"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    permissions_json = Column(Text)  # JSON string of permissions
    
    # Relationships
    users = relationship("User", back_populates="role")

class User(Base):
    """System users"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)
    active = Column(Boolean, default=True)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
    sales = relationship("Sale", back_populates="user")
    repairs = relationship("Repair", back_populates="user")
    transfers = relationship("Transfer", back_populates="user")
    stock_movements = relationship("StockMovement", back_populates="user")
