import os
from pathlib import Path
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
import bcrypt

# Database configuration - Use PostgreSQL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Always create these for backward compatibility
BASE_DIR = Path.home() / "AppData" / "Roaming" / "AlHussinyShop"
DB_PATH = BASE_DIR / "hussiny.db"
BASE_DIR.mkdir(parents=True, exist_ok=True)

if not DATABASE_URL:
    # Fallback to SQLite for local development
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLAlchemy setup
if DATABASE_URL.startswith("postgres"):
    engine = create_engine(DATABASE_URL, echo=False)
else:
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with schema and default data"""
    from models.user import User, Role
    from models.product import Product, Category, Supplier
    from models.sales import Sale, SaleItem, Customer
    from models.repair import Repair
    from models.transfer import Transfer
    from models.base import AuditLog, Backup
    
    # Create all tables with error handling for existing indexes
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except Exception as e:
        # If tables/indexes already exist, continue with data initialization
        print(f"Database schema already exists: {e}")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "alhussiny@admin.com").first()
        
        if not admin_user:
            # Create default roles
            admin_role = Role(
                name="Admin",
                permissions_json='{"all": true}'
            )
            manager_role = Role(
                name="Manager", 
                permissions_json='{"sales": true, "inventory": true, "reports": true}'
            )
            cashier_role = Role(
                name="Cashier",
                permissions_json='{"sales": true}'
            )
            technician_role = Role(
                name="Technician",
                permissions_json='{"repairs": true, "inventory": true}'
            )
            viewer_role = Role(
                name="Viewer",
                permissions_json='{"reports": true}'
            )
            
            db.add_all([admin_role, manager_role, cashier_role, technician_role, viewer_role])
            db.commit()
            
            # Create admin user
            hashed_password = bcrypt.hashpw("admin@1234".encode('utf-8'), bcrypt.gensalt())
            admin_user = User(
                email="alhussiny@admin.com",
                password_hash=hashed_password.decode('utf-8'),
                name="مدير النظام",
                role_id=admin_role.id,
                active=True
            )
            db.add(admin_user)
            
            # Create default categories
            categories = [
                "سماعات اذن", "سماعات", "شاحن", "ماوس", "ميكات", 
                "ليدر", "اوتو جي", "جراب", "وصلة مايكرو", "وصلة تايب",
                "اكسسوار", "ستاند", "سكرينه", "ايربودز", "كمبيوتر", "باور بنك", "اخري"
            ]
            
            for cat_name in categories:
                category = Category(name_ar=cat_name)
                db.add(category)
            
            db.commit()
            
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def execute_query(query, params=None):
    """Execute raw SQL query safely"""
    with engine.connect() as conn:
        if params:
            result = conn.execute(query, params)
        else:
            result = conn.execute(query)
        return result.fetchall()
