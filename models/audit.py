# -*- coding: utf-8 -*-
"""
Audit and backup models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from config.database import Base

class AuditLog(Base):
    """Audit log model for tracking user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    module = Column(String(50), nullable=False, index=True)  # users, products, sales, etc.
    record_id = Column(Integer, nullable=True)  # ID of the affected record
    old_values = Column(Text, nullable=True)  # JSON string of old values
    new_values = Column(Text, nullable=True)  # JSON string of new values
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    details = Column(Text, nullable=True)  # Additional details
    
    # Relationships
    user = relationship("User")
    
    @classmethod
    def log_action(cls, session, user_id: int, action: str, module: str, 
                   record_id: int = None, old_values: dict = None, 
                   new_values: dict = None, details: str = None):
        """Helper method to create audit log entry"""
        import json
        
        audit_entry = cls(
            user_id=user_id,
            action=action,
            module=module,
            record_id=record_id,
            old_values=json.dumps(old_values, ensure_ascii=False) if old_values else None,
            new_values=json.dumps(new_values, ensure_ascii=False) if new_values else None,
            details=details,
            timestamp=datetime.now()
        )
        session.add(audit_entry)
        return audit_entry
    
    def __repr__(self):
        return f"<AuditLog(user_id={self.user_id}, action='{self.action}', module='{self.module}')>"

class Backup(Base):
    """Backup record model"""
    __tablename__ = "backups"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Float, nullable=False, default=0.0)  # Size in MB
    backup_type = Column(String(20), nullable=False, default="manual")  # manual, auto, scheduled
    status = Column(String(20), nullable=False, default="completed")  # pending, completed, failed
    
    # Metadata
    tables_count = Column(Integer, nullable=False, default=0)
    records_count = Column(Integer, nullable=False, default=0)
    compression = Column(String(20), nullable=True)  # zip, gzip, none
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Additional info
    description = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User")
    
    @property
    def file_size_formatted(self) -> str:
        """Get formatted file size"""
        if self.file_size < 1:
            return f"{self.file_size * 1024:.1f} KB"
        elif self.file_size < 1024:
            return f"{self.file_size:.1f} MB"
        else:
            return f"{self.file_size / 1024:.1f} GB"
    
    @property
    def is_successful(self) -> bool:
        """Check if backup was successful"""
        return self.status == "completed" and not self.error_message
    
    def mark_completed(self):
        """Mark backup as completed"""
        self.status = "completed"
        self.completed_at = datetime.now()
    
    def mark_failed(self, error_message: str):
        """Mark backup as failed"""
        self.status = "failed"
        self.error_message = error_message
        self.completed_at = datetime.now()
    
    def __repr__(self):
        return f"<Backup(filename='{self.filename}', type='{self.backup_type}', status='{self.status}')>"
