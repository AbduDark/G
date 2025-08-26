from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json
import bcrypt

Base = declarative_base()

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    active = Column(Boolean, default=True)
    
    # Relationships
    role = relationship('Role', back_populates='users')
    sales = relationship('Sale', back_populates='user')
    repairs = relationship('Repair', back_populates='user')
    transfers = relationship('Transfer', back_populates='user')
    stock_movements = relationship('StockMovement', back_populates='user')
    audit_logs = relationship('AuditLog', back_populates='user')
    backups = relationship('Backup', back_populates='user')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role.name_ar if self.role else '',
            'active': self.active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'

class Role(Base):
    """Role model for user permissions"""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    name_ar = Column(String(50), nullable=False)
    permissions_json = Column(Text, nullable=False)
    
    # Relationships
    users = relationship('User', back_populates='role')
    
    @property
    def permissions(self):
        """Get permissions as list"""
        return json.loads(self.permissions_json)
    
    @permissions.setter
    def permissions(self, value):
        """Set permissions from list"""
        self.permissions_json = json.dumps(value)
    
    def has_permission(self, permission):
        """Check if role has specific permission"""
        return 'all' in self.permissions or permission in self.permissions
    
    def __repr__(self):
        return f'<Role {self.name}>'

class Category(Base):
    """Product category model"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name_ar = Column(String(100), unique=True, nullable=False)
    
    # Relationships
    products = relationship('Product', back_populates='category')
    
    def __repr__(self):
        return f'<Category {self.name_ar}>'

class Supplier(Base):
    """Supplier model"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    email = Column(String(120))
    
    # Relationships
    products = relationship('Product', back_populates='supplier')
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

class Product(Base):
    """Product model"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(200), nullable=False, index=True)
    description_ar = Column(Text)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    cost_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    min_quantity = Column(Integer, nullable=False, default=5)
    barcode = Column(String(50), index=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    
    # Relationships
    category = relationship('Category', back_populates='products')
    supplier = relationship('Supplier', back_populates='products')
    sale_items = relationship('SaleItem', back_populates='product')
    stock_movements = relationship('StockMovement', back_populates='product')
    returns = relationship('Return', back_populates='product')
    
    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        return self.quantity <= self.min_quantity
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price > 0:
            return ((self.sale_price - self.cost_price) / self.cost_price) * 100
        return 0
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'sku': self.sku,
            'name_ar': self.name_ar,
            'description_ar': self.description_ar,
            'category': self.category.name_ar if self.category else '',
            'cost_price': float(self.cost_price),
            'sale_price': float(self.sale_price),
            'quantity': self.quantity,
            'min_quantity': self.min_quantity,
            'barcode': self.barcode,
            'is_low_stock': self.is_low_stock,
            'profit_margin': self.profit_margin
        }
    
    def __repr__(self):
        return f'<Product {self.name_ar}>'

class Customer(Base):
    """Customer model"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), index=True)
    address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = relationship('Sale', back_populates='customer')
    repairs = relationship('Repair', back_populates='customer')
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class Sale(Base):
    """Sale transaction model"""
    __tablename__ = 'sales'
    
    id = Column(Integer, primary_key=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    total = Column(Float, nullable=False)
    tax = Column(Float, default=0)
    discount = Column(Float, default=0)
    paid = Column(Float, nullable=False)
    change = Column(Float, default=0)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='completed')
    notes = Column(Text)
    
    # Relationships
    customer = relationship('Customer', back_populates='sales')
    user = relationship('User', back_populates='sales')
    sale_items = relationship('SaleItem', back_populates='sale', cascade='all, delete-orphan')
    returns = relationship('Return', back_populates='sale')
    
    @property
    def subtotal(self):
        """Calculate subtotal from items"""
        return sum(item.line_total for item in self.sale_items)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'invoice_no': self.invoice_no,
            'customer_name': self.customer.name if self.customer else '',
            'total': float(self.total),
            'tax': float(self.tax),
            'discount': float(self.discount),
            'paid': float(self.paid),
            'change': float(self.change),
            'user_name': self.user.name,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'items_count': len(self.sale_items)
        }
    
    def __repr__(self):
        return f'<Sale {self.invoice_no}>'

class SaleItem(Base):
    """Sale item model"""
    __tablename__ = 'sale_items'
    
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    
    # Relationships
    sale = relationship('Sale', back_populates='sale_items')
    product = relationship('Product', back_populates='sale_items')
    
    def __repr__(self):
        return f'<SaleItem {self.product.name_ar if self.product else "Unknown"}>'

class Return(Base):
    """Product return model"""
    __tablename__ = 'returns'
    
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(String(200))
    refund_amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    sale = relationship('Sale', back_populates='returns')
    product = relationship('Product', back_populates='returns')
    user = relationship('User')
    
    def __repr__(self):
        return f'<Return {self.product.name_ar if self.product else "Unknown"}>'

class Repair(Base):
    """Repair service model"""
    __tablename__ = 'repairs'
    
    id = Column(Integer, primary_key=True)
    ticket_no = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    device_model = Column(String(200), nullable=False)
    problem_desc = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default='قيد الفحص')
    entry_date = Column(DateTime, default=datetime.utcnow)
    exit_date = Column(DateTime)
    parts_cost = Column(Float, default=0)
    labor_cost = Column(Float, default=0)
    total_cost = Column(Float, default=0)
    notes = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    customer = relationship('Customer', back_populates='repairs')
    user = relationship('User', back_populates='repairs')
    
    @property
    def is_completed(self):
        """Check if repair is completed"""
        return self.status in ['تم الإصلاح', 'غير قابل للإصلاح', 'تم التسليم']
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'ticket_no': self.ticket_no,
            'customer_name': self.customer.name if self.customer else '',
            'device_model': self.device_model,
            'problem_desc': self.problem_desc,
            'status': self.status,
            'entry_date': self.entry_date.isoformat(),
            'exit_date': self.exit_date.isoformat() if self.exit_date else None,
            'total_cost': float(self.total_cost),
            'is_completed': self.is_completed
        }
    
    def __repr__(self):
        return f'<Repair {self.ticket_no}>'

class Transfer(Base):
    """Balance transfer model"""
    __tablename__ = 'transfers'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    from_account = Column(String(100))
    to_account = Column(String(100), nullable=False)
    reference_id = Column(String(100))
    note = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='transfers')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'amount': float(self.amount),
            'from_account': self.from_account,
            'to_account': self.to_account,
            'reference_id': self.reference_id,
            'note': self.note,
            'user_name': self.user.name,
            'date': self.date.isoformat()
        }
    
    def __repr__(self):
        return f'<Transfer {self.type} - {self.amount}>'

class StockMovement(Base):
    """Stock movement tracking model"""
    __tablename__ = 'stock_movements'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    change_qty = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)  # purchase, sale, return, adjustment, transfer
    reference_id = Column(Integer)  # reference to sale_id, repair_id, etc.
    date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    note = Column(Text)
    
    # Relationships
    product = relationship('Product', back_populates='stock_movements')
    user = relationship('User', back_populates='stock_movements')
    
    def __repr__(self):
        return f'<StockMovement {self.type} - {self.change_qty}>'

class AuditLog(Base):
    """Audit log model"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action}>'

class Backup(Base):
    """Backup record model"""
    __tablename__ = 'backups'
    
    id = Column(Integer, primary_key=True)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    size = Column(Integer)  # File size in bytes
    
    # Relationships
    user = relationship('User', back_populates='backups')
    
    def __repr__(self):
        return f'<Backup {self.file_path}>'

class Settings(Base):
    """Application settings model"""
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(String(200))
    
    def __repr__(self):
        return f'<Settings {self.key}>'
