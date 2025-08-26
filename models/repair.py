from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Repair(Base):
    """Repair service tracking"""
    __tablename__ = "repairs"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_no = Column(String(50), nullable=False, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    device_model = Column(String(100), nullable=False)
    problem_desc = Column(Text, nullable=False)
    status = Column(String(50), default="قيد الفحص")  # قيد الفحص، قيد الانتظار، تم الإصلاح، غير قابل للإصلاح
    entry_date = Column(DateTime, default=func.now())
    exit_date = Column(DateTime)
    parts_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    notes = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    customer = relationship("Customer", back_populates="repairs")
    user = relationship("User", back_populates="repairs")
