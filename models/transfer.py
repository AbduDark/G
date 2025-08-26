# -*- coding: utf-8 -*-
"""
Balance transfer models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text

from config.database import Base
from sqlalchemy.orm import relationship

class Transfer(Base):
    """Balance transfer model for mobile credit and cash services"""
    __tablename__ = "transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    # Types: vodafone_cash, etisalat_cash, orange_cash, aman_cash, 
    #        card_charge, money_transfer, other
    
    service_name = Column(String(100), nullable=False)  # Detailed service name in Arabic
    amount = Column(Float, nullable=False)
    commission = Column(Float, nullable=False, default=0.0)
    net_amount = Column(Float, nullable=False)  # amount - commission
    
    # Customer information
    customer_name = Column(String(100), nullable=True)
    customer_phone = Column(String(20), nullable=False, index=True)
    recipient_phone = Column(String(20), nullable=True)  # For transfers
    recipient_name = Column(String(100), nullable=True)
    
    # Reference numbers
    reference_no = Column(String(100), nullable=True)  # Service provider reference
    operator_ref = Column(String(100), nullable=True)  # Operator reference number
    
    # Status and verification
    status = Column(String(20), nullable=False, default="completed")  
    # Status: pending, completed, failed, cancelled
    verified = Column(String(10), default="no")  # yes, no, pending
    verification_code = Column(String(50), nullable=True)
    
    # Financial details
    cost_price = Column(Float, nullable=False, default=0.0)  # Our cost
    profit = Column(Float, nullable=False, default=0.0)
    
    # Processing info
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    processed_at = Column(DateTime, default=datetime.now, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("User")
    
    def calculate_profit(self):
        """Calculate profit from transfer"""
        self.net_amount = self.amount - self.commission
        self.profit = self.net_amount - self.cost_price
    
    def complete_transaction(self):
        """Mark transaction as completed"""
        if self.status == "pending":
            self.status = "completed"
            self.completed_at = datetime.now()
    
    @property
    def is_profitable(self) -> bool:
        """Check if transaction is profitable"""
        return self.profit > 0
    
    @property
    def service_type_ar(self) -> str:
        """Get Arabic service type name"""
        type_mapping = {
            "vodafone_cash": "فودافون كاش",
            "etisalat_cash": "اتصالات كاش",
            "orange_cash": "اورانج كاش",
            "aman_cash": "امان كاش",
            "card_charge": "شحن كروت",
            "money_transfer": "تحويل أموال",
            "other": "أخرى"
        }
        return type_mapping.get(self.type, self.type)
    
    def __repr__(self):
        return f"<Transfer(transaction_id='{self.transaction_id}', type='{self.type}', amount={self.amount})>"
