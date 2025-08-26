# -*- coding: utf-8 -*-
"""
Product and inventory models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum

from config.database import Base

class MovementType(enum.Enum):
    """Stock movement types"""
    PURCHASE = "purchase"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"

class Category(Base):
    """Product category model"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name_ar = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(name_ar='{self.name_ar}')>"

class Supplier(Base):
    """Supplier model"""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    email = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    products = relationship("Product", back_populates="supplier")
    
    def __repr__(self):
        return f"<Supplier(name='{self.name}')>"

class Product(Base):
    """Product model"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(200), nullable=False, index=True)
    description_ar = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    cost_price = Column(Float, nullable=False, default=0.0)
    sale_price = Column(Float, nullable=False, default=0.0)
    quantity = Column(Integer, nullable=False, default=0)
    min_quantity = Column(Integer, nullable=False, default=5)
    barcode = Column(String(100), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    active = Column(String(10), default="active")  # active, inactive, discontinued
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")
    
    @property
    def is_low_stock(self) -> bool:
        """Check if product is low in stock"""
        return self.quantity <= self.min_quantity
    
    @property
    def profit_margin(self) -> float:
        """Calculate profit margin percentage"""
        if self.cost_price > 0:
            return ((self.sale_price - self.cost_price) / self.cost_price) * 100
        return 0.0
    
    def update_quantity(self, change: int, movement_type: MovementType, 
                       reference_id: int = None, user_id: int = None, note: str = None):
        """Update product quantity and create stock movement record"""
        old_quantity = self.quantity
        self.quantity += change
        self.updated_at = datetime.now()
        
        # Create stock movement record
        movement = StockMovement(
            product_id=self.id,
            change_qty=change,
            old_quantity=old_quantity,
            new_quantity=self.quantity,
            type=movement_type,
            reference_id=reference_id,
            user_id=user_id,
            note=note,
            date=datetime.now()
        )
        return movement
    
    def __repr__(self):
        return f"<Product(sku='{self.sku}', name_ar='{self.name_ar}')>"

class StockMovement(Base):
    """Stock movement tracking model"""
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    change_qty = Column(Integer, nullable=False)
    old_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)
    type = Column(Enum(MovementType), nullable=False)
    reference_id = Column(Integer, nullable=True)  # Sale ID, Purchase ID, etc.
    date = Column(DateTime, default=datetime.now, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(Text, nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="stock_movements")
    user = relationship("User")
    
    def __repr__(self):
        return f"<StockMovement(product_id={self.product_id}, change={self.change_qty}, type={self.type.value})>"
