from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Transfer(Base):
    """Balance transfers and cash transactions"""
    __tablename__ = "transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    transfer_type = Column(String(50), nullable=False)  # فودافون كاش، اتصالات كاش، etc.
    amount = Column(Float, nullable=False)
    from_account = Column(String(100))
    to_account = Column(String(100), nullable=False)
    reference_no = Column(String(100))  # Transaction reference number
    note = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=func.now())
    status = Column(String(20), default="completed")
    
    # Relationships
    user = relationship("User", back_populates="transfers")
