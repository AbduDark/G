# -*- coding: utf-8 -*-
"""
Sales and customer models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from config.database import Base

class Customer(Base):
    """Customer model"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=True, index=True)
    address = Column(Text, nullable=True)
    email = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    sales = relationship("Sale", back_populates="customer")
    repairs = relationship("Repair", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(name='{self.name}', phone='{self.phone}')>"

class Sale(Base):
    """Sales invoice model"""
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    subtotal = Column(Float, nullable=False, default=0.0)
    tax_rate = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    discount_rate = Column(Float, nullable=False, default=0.0)
    discount_amount = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    paid = Column(Float, nullable=False, default=0.0)
    change_amount = Column(Float, nullable=False, default=0.0)
    payment_method = Column(String(20), nullable=False, default="cash")  # cash, card, credit
    status = Column(String(20), nullable=False, default="completed")  # completed, cancelled, returned
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="sales")
    user = relationship("User")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    returns = relationship("Return", back_populates="sale")
    
    def calculate_totals(self):
        """Calculate sale totals from items"""
        self.subtotal = sum(item.line_total for item in self.items)
        
        # Calculate discount
        if self.discount_rate > 0:
            self.discount_amount = self.subtotal * (self.discount_rate / 100)
        
        # Calculate tax on discounted amount
        taxable_amount = self.subtotal - self.discount_amount
        if self.tax_rate > 0:
            self.tax_amount = taxable_amount * (self.tax_rate / 100)
        
        # Calculate total
        self.total = taxable_amount + self.tax_amount
        
        # Calculate change
        self.change_amount = max(0, self.paid - self.total)
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost of items sold"""
        return sum(item.product.cost_price * item.quantity for item in self.items if item.product)
    
    @property
    def profit(self) -> float:
        """Calculate profit from this sale"""
        return self.total - self.total_cost
    
    def __repr__(self):
        return f"<Sale(invoice_no='{self.invoice_no}', total={self.total})>"

class SaleItem(Base):
    """Sale item model"""
    __tablename__ = "sale_items"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    
    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
    
    def calculate_line_total(self):
        """Calculate line total"""
        self.line_total = self.quantity * self.unit_price
    
    def __repr__(self):
        return f"<SaleItem(sale_id={self.sale_id}, product_id={self.product_id}, qty={self.quantity})>"

class Return(Base):
    """Product return model"""
    __tablename__ = "returns"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(String(200), nullable=False)
    refund_amount = Column(Float, nullable=False, default=0.0)
    approved = Column(Boolean, default=False)
    date = Column(DateTime, default=datetime.now, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    sale = relationship("Sale", back_populates="returns")
    product = relationship("Product")
    user = relationship("User")
    
    def __repr__(self):
        return f"<Return(sale_id={self.sale_id}, product_id={self.product_id}, qty={self.quantity})>"
