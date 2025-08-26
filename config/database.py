# -*- coding: utf-8 -*-
"""
Database configuration and initialization
"""

import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import bcrypt

from config.settings import settings

# SQLAlchemy base class
Base = declarative_base()

class DatabaseManager:
    """Database manager for SQLite operations"""
    
    def __init__(self):
        self.db_path = settings.get_database_path()
        self.engine = None
        self.SessionLocal = None
        self.setup_database()
        
    def setup_database(self):
        """Setup database connection"""
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create SQLAlchemy engine
        database_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,
                "timeout": 30
            },
            echo=False  # Set to True for SQL debugging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logging.info(f"Database setup complete: {self.db_path}")
        
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
        
    def initialize_database(self):
        """Initialize database schema and default data"""
        try:
            # Import all models to register them with Base
            from models.user import User, Role
            from models.product import Product, Category, Supplier, StockMovement
            from models.sales import Sale, SaleItem, Customer, Return
            from models.repair import Repair
            from models.transfer import Transfer
            from models.audit import AuditLog, Backup
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logging.info("Database tables created successfully")
            
            # Create default data
            self.create_default_data()
            
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")
            raise
            
    def create_default_data(self):
        """Create default roles, admin user, and categories"""
        session = self.get_session()
        try:
            from models.user import User, Role
            from models.product import Category
            
            # Create default roles if they don't exist
            default_roles = [
                {"name": "Admin", "permissions": {
                    "users": ["create", "read", "update", "delete"],
                    "products": ["create", "read", "update", "delete"],
                    "sales": ["create", "read", "update", "delete"],
                    "repairs": ["create", "read", "update", "delete"],
                    "transfers": ["create", "read", "update", "delete"],
                    "reports": ["read"],
                    "settings": ["read", "update"],
                    "backup": ["create", "read"]
                }},
                {"name": "Manager", "permissions": {
                    "users": ["read"],
                    "products": ["create", "read", "update"],
                    "sales": ["create", "read", "update"],
                    "repairs": ["create", "read", "update"],
                    "transfers": ["create", "read", "update"],
                    "reports": ["read"],
                    "settings": ["read"],
                    "backup": ["read"]
                }},
                {"name": "Cashier", "permissions": {
                    "products": ["read"],
                    "sales": ["create", "read"],
                    "repairs": ["read"],
                    "transfers": ["create", "read"],
                    "reports": ["read"]
                }},
                {"name": "Technician", "permissions": {
                    "products": ["read"],
                    "repairs": ["create", "read", "update"],
                    "reports": ["read"]
                }},
                {"name": "Viewer", "permissions": {
                    "products": ["read"],
                    "sales": ["read"],
                    "repairs": ["read"],
                    "transfers": ["read"],
                    "reports": ["read"]
                }}
            ]
            
            for role_data in default_roles:
                existing_role = session.query(Role).filter_by(name=role_data["name"]).first()
                if not existing_role:
                    role = Role(
                        name=role_data["name"],
                        permissions=role_data["permissions"]
                    )
                    session.add(role)
            
            session.commit()
            
            # Create default admin user
            admin_role = session.query(Role).filter_by(name="Admin").first()
            existing_admin = session.query(User).filter_by(email="alhussiny@admin.com").first()
            
            if not existing_admin and admin_role:
                # Hash the default password
                password_hash = bcrypt.hashpw("admin@1234".encode('utf-8'), bcrypt.gensalt())
                
                admin_user = User(
                    email="alhussiny@admin.com",
                    password_hash=password_hash.decode('utf-8'),
                    name="مدير النظام",
                    role_id=admin_role.id,
                    active=True,
                    created_at=datetime.now()
                )
                session.add(admin_user)
                logging.info("Default admin user created")
            
            # Create default categories
            default_categories = [
                "سماعات اذن", "سماعات", "شاحن", "ماوس", "ميكات",
                "ليدر", "اوتو جي", "جراب", "وصلة مايكرو", "وصلة تايب",
                "اكسسوار", "ستاند", "سكرينه", "ايربودز", "كمبيوتر",
                "باور بنك", "اخري"
            ]
            
            for cat_name in default_categories:
                existing_cat = session.query(Category).filter_by(name_ar=cat_name).first()
                if not existing_cat:
                    category = Category(name_ar=cat_name)
                    session.add(category)
            
            session.commit()
            logging.info("Default data created successfully")
            
        except Exception as e:
            session.rollback()
            logging.error(f"Failed to create default data: {e}")
            raise
        finally:
            session.close()

# Global database manager instance
db_manager = DatabaseManager()

def get_db_session():
    """Get database session for dependency injection"""
    return db_manager.get_session()
