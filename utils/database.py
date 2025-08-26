import os
from werkzeug.security import generate_password_hash
from datetime import datetime
import json
from config import Config

def init_database(app, db):
    """Initialize database with schema and default data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Import models after db is initialized
        from models import User, Role, Category, Supplier
        
        # Check if database is empty (first run)
        if User.query.count() == 0:
            print("Initializing database with default data...")
            
            # Create default roles
            create_default_roles(db)
            
            # Create default admin user
            create_default_admin(db)
            
            # Create default categories
            create_default_categories(db)
            
            # Create default supplier
            create_default_supplier(db)
            
            print("Database initialization completed!")

def create_default_roles(db):
    """Create default user roles"""
    from models import Role
    
    for role_name, role_data in Config.DEFAULT_ROLES.items():
        role = Role(
            name=role_name,
            name_ar=role_data['name'],
            permissions=role_data['permissions']
        )
        db.session.add(role)
    
    db.session.commit()
    print("Default roles created")

def create_default_admin(db):
    """Create default admin user"""
    from models import User, Role
    
    admin_role = Role.query.filter_by(name='Admin').first()
    
    admin_user = User(
        email='alhussiny@admin.com',
        password_hash=generate_password_hash('admin@1234'),
        name='مدير النظام',
        role_id=admin_role.id,
        created_at=datetime.utcnow()
    )
    
    db.session.add(admin_user)
    db.session.commit()
    print("Default admin user created: alhussiny@admin.com / admin@1234")

def create_default_categories(db):
    """Create default product categories"""
    from models import Category
    
    for category_name in Config.DEFAULT_CATEGORIES:
        category = Category(name_ar=category_name)
        db.session.add(category)
    
    db.session.commit()
    print("Default categories created")

def create_default_supplier(db):
    """Create default supplier"""
    from models import Supplier
    
    supplier = Supplier(
        name='المورد الافتراضي',
        phone='',
        address='العنوان يتم تحديده لاحقاً'
    )
    
    db.session.add(supplier)
    db.session.commit()
    print("Default supplier created")

def backup_database(app, backup_path=None):
    """Create database backup"""
    with app.app_context():
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(Config.BACKUP_FOLDER, f'hussiny_backup_{timestamp}.db')
        
        # Ensure backup directory exists
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Copy database file
        import shutil
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        shutil.copy2(db_path, backup_path)
        
        return backup_path

def restore_database(app, backup_path):
    """Restore database from backup"""
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Backup current database before restore
        current_backup = backup_database(app, f"{db_path}.pre_restore_backup")
        
        # Restore from backup
        import shutil
        shutil.copy2(backup_path, db_path)
        
        return True

def cleanup_old_backups(max_backups=10):
    """Remove old backup files keeping only the most recent ones"""
    import glob
    
    backup_pattern = os.path.join(Config.BACKUP_FOLDER, 'hussiny_backup_*.db')
    backup_files = glob.glob(backup_pattern)
    
    # Sort by creation time (newest first)
    backup_files.sort(key=os.path.getctime, reverse=True)
    
    # Remove old backups
    for old_backup in backup_files[max_backups:]:
        try:
            os.remove(old_backup)
            print(f"Removed old backup: {old_backup}")
        except OSError as e:
            print(f"Error removing backup {old_backup}: {e}")

def get_database_stats(app):
    """Get database statistics"""
    with app.app_context():
        from models import User, Product, Sale, Repair, Transfer
        
        stats = {
            'users': User.query.count(),
            'products': Product.query.filter_by(active=True).count(),
            'sales': Sale.query.count(),
            'repairs': Repair.query.count(),
            'transfers': Transfer.query.count(),
            'database_size': get_database_size(app)
        }
        
        return stats

def get_database_size(app):
    """Get database file size in bytes"""
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    try:
        return os.path.getsize(db_path)
    except OSError:
        return 0

def vacuum_database(app):
    """Optimize database by running VACUUM command"""
    with app.app_context():
        from models import db
        db.session.execute('VACUUM')
        db.session.commit()
        print("Database vacuum completed")

def check_database_integrity(app):
    """Check database integrity"""
    with app.app_context():
        from models import db
        result = db.session.execute('PRAGMA integrity_check').fetchall()
        
        if result and result[0][0] == 'ok':
            return True, "Database integrity check passed"
        else:
            return False, f"Database integrity issues found: {result}"
