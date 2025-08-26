# -*- coding: utf-8 -*-
"""
Repair service models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean

from config.database import Base
from sqlalchemy.orm import relationship

class Repair(Base):
    """Repair service model"""
    __tablename__ = "repairs"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_no = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    device_model = Column(String(200), nullable=False)
    device_brand = Column(String(100), nullable=True)
    device_color = Column(String(50), nullable=True)
    device_imei = Column(String(50), nullable=True)
    problem_desc = Column(Text, nullable=False)
    diagnosis = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    parts_used = Column(Text, nullable=True)  # JSON string of parts and quantities
    status = Column(String(30), nullable=False, default="received")  
    # Status options: received, diagnosed, waiting_parts, in_progress, completed, delivered, cancelled
    priority = Column(String(20), nullable=False, default="normal")  # low, normal, high, urgent
    
    # Dates
    entry_date = Column(DateTime, default=datetime.now, index=True)
    promised_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    delivered_date = Column(DateTime, nullable=True)
    
    # Costs
    parts_cost = Column(Float, nullable=False, default=0.0)
    labor_cost = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    
    # Additional info
    technician_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    received_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    delivered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    warranty_days = Column(Integer, nullable=False, default=30)
    is_warranty_void = Column(Boolean, default=False)
    customer_notified = Column(Boolean, default=False)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    customer = relationship("Customer", back_populates="repairs")
    technician = relationship("User", foreign_keys=[technician_id])
    received_by_user = relationship("User", foreign_keys=[received_by])
    delivered_by_user = relationship("User", foreign_keys=[delivered_by])
    
    def calculate_total(self):
        """Calculate total repair cost"""
        self.total_cost = self.parts_cost + self.labor_cost
    
    @property
    def is_completed(self) -> bool:
        """Check if repair is completed"""
        return self.status == "completed"
    
    @property
    def is_overdue(self) -> bool:
        """Check if repair is overdue"""
        if self.promised_date and self.status not in ["completed", "delivered", "cancelled"]:
            return datetime.now() > self.promised_date
        return False
    
    @property
    def days_in_service(self) -> int:
        """Calculate days since entry"""
        return (datetime.now() - self.entry_date).days
    
    def update_status(self, new_status: str, user_id: int = None):
        """Update repair status with timestamp"""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        
        # Update specific date fields based on status
        if new_status == "completed" and old_status != "completed":
            self.completed_date = datetime.now()
        elif new_status == "delivered" and old_status != "delivered":
            self.delivered_date = datetime.now()
            if user_id:
                self.delivered_by = user_id
    
    def __repr__(self):
        return f"<Repair(ticket_no='{self.ticket_no}', device='{self.device_model}', status='{self.status}')>"
