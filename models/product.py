from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Category(Base):
    """Product categories"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name_ar = Column(String(100), nullable=False)
    
    # Relationships
    products = relationship("Product", back_populates="category")

class Supplier(Base):
    """Product suppliers"""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    
    # Relationships
    products = relationship("Product", back_populates="supplier")

class Product(Base):
    """Products/inventory items"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), nullable=False, unique=True, index=True)
    name_ar = Column(String(200), nullable=False)
    description_ar = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"))
    cost_price = Column(Float, default=0.0)
    sale_price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)
    min_quantity = Column(Integer, default=5)
    barcode = Column(String(50), index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    created_at = Column(DateTime, default=func.now())
    active = Column(Boolean, default=True)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")

class StockMovement(Base):
    """Stock movement tracking"""
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    change_qty = Column(Integer, nullable=False)  # Positive for increase, negative for decrease
    movement_type = Column(String(20), nullable=False)  # purchase, sale, return, adjustment, transfer
    reference_id = Column(String(50))  # Reference to sale, purchase, etc.
    date = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    note = Column(Text)
    
    # Relationships
    product = relationship("Product", back_populates="stock_movements")
    user = relationship("User", back_populates="stock_movements")
