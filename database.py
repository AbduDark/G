# -*- coding: utf-8 -*-
"""
Database manager for Al-Hussiny Mobile Shop POS System
"""

import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from config import Config
from models import Base, User, Role, Category, Supplier, Settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and operations manager"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self.session = None
    
    def initialize(self):
        """Initialize database connection and create tables if needed"""
        try:
            # Create database engine
            db_url = Config.get_db_url()
            self.engine = create_engine(
                db_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True
            )
            
            # Create session factory
            self.Session = sessionmaker(bind=self.engine)
            
            # Create all tables
            Base.metadata.create_all(self.engine)
            
            # Initialize default data if database is empty
            self._initialize_default_data()
            
            logger.info("تم تهيئة قاعدة البيانات بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
            return False
    
    def get_session(self):
        """Get a new database session"""
        if self.Session is None:
            raise RuntimeError("Database not initialized")
        return self.Session()
    
    def _initialize_default_data(self):
        """Initialize default data if database is empty"""
        session = self.get_session()
        try:
            # Check if any users exist
            if session.query(User).count() == 0:
                logger.info("إنشاء البيانات الافتراضية...")
                
                # Create default roles
                self._create_default_roles(session)
                
                # Create default admin user
                self._create_default_admin(session)
                
                # Create default categories
                self._create_default_categories(session)
                
                # Create default supplier
                self._create_default_supplier(session)
                
                # Create default settings
                self._create_default_settings(session)
                
                session.commit()
                logger.info("تم إنشاء البيانات الافتراضية بنجاح")
                
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في إنشاء البيانات الافتراضية: {e}")
            raise
        finally:
            session.close()
    
    def _create_default_roles(self, session):
        """Create default user roles"""
        for role_name, role_data in Config.DEFAULT_ROLES.items():
            role = Role(
                name=role_name,
                name_ar=role_data['name_ar'],
                permissions=role_data['permissions']
            )
            session.add(role)
        logger.info("تم إنشاء الأدوار الافتراضية")
    
    def _create_default_admin(self, session):
        """Create default admin user"""
        admin_role = session.query(Role).filter_by(name='Admin').first()
        
        admin_user = User(
            email=Config.DEFAULT_ADMIN_EMAIL,
            name=Config.DEFAULT_ADMIN_NAME,
            role_id=admin_role.id
        )
        admin_user.set_password(Config.DEFAULT_ADMIN_PASSWORD)
        
        session.add(admin_user)
        logger.info(f"تم إنشاء المستخدم الافتراضي: {Config.DEFAULT_ADMIN_EMAIL}")
    
    def _create_default_categories(self, session):
        """Create default product categories"""
        for category_name in Config.DEFAULT_CATEGORIES:
            category = Category(name_ar=category_name)
            session.add(category)
        logger.info("تم إنشاء الفئات الافتراضية")
    
    def _create_default_supplier(self, session):
        """Create default supplier"""
        supplier = Supplier(
            name='المورد الافتراضي',
            phone='',
            address='العنوان يتم تحديده لاحقاً'
        )
        session.add(supplier)
        logger.info("تم إنشاء المورد الافتراضي")
    
    def _create_default_settings(self, session):
        """Create default application settings"""
        default_settings = [
            ('shop_name', Config.SHOP_NAME, 'اسم المحل'),
            ('shop_address', Config.SHOP_ADDRESS, 'عنوان المحل'),
            ('shop_phone', Config.SHOP_PHONE, 'هاتف المحل'),
            ('shop_email', Config.SHOP_EMAIL, 'بريد المحل الإلكتروني'),
            ('tax_rate', str(Config.DEFAULT_TAX_RATE), 'معدل الضريبة'),
            ('currency_symbol', Config.CURRENCY_SYMBOL, 'رمز العملة'),
            ('theme', Config.DEFAULT_THEME, 'مظهر التطبيق'),
            ('auto_backup', str(Config.AUTO_BACKUP_ENABLED), 'النسخ الاحتياطي التلقائي'),
            ('backup_interval', str(Config.AUTO_BACKUP_INTERVAL), 'فترة النسخ الاحتياطي (ساعات)'),
            ('invoice_prefix', Config.INVOICE_PREFIX, 'بادئة رقم الفاتورة'),
            ('repair_prefix', Config.REPAIR_TICKET_PREFIX, 'بادئة رقم تذكرة الصيانة')
        ]
        
        for key, value, description in default_settings:
            setting = Settings(key=key, value=value, description=description)
            session.add(setting)
        
        logger.info("تم إنشاء الإعدادات الافتراضية")
    
    def authenticate_user(self, email, password):
        """Authenticate user with email and password"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(email=email, active=True).first()
            
            if user and user.check_password(password):
                # Update last login
                user.last_login = datetime.utcnow()
                session.commit()
                
                # Return user data
                user_data = user.to_dict()
                user_data['permissions'] = user.role.permissions
                
                logger.info(f"تم تسجيل دخول المستخدم: {email}")
                return user_data
            else:
                logger.warning(f"فشل في تسجيل دخول المستخدم: {email}")
                return None
                
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في تسجيل الدخول: {e}")
            return None
        finally:
            session.close()
    
    def get_setting(self, key, default=None):
        """Get application setting value"""
        session = self.get_session()
        try:
            setting = session.query(Settings).filter_by(key=key).first()
            return setting.value if setting else default
        except Exception as e:
            logger.error(f"خطأ في قراءة الإعداد {key}: {e}")
            return default
        finally:
            session.close()
    
    def set_setting(self, key, value, description=None):
        """Set application setting value"""
        session = self.get_session()
        try:
            setting = session.query(Settings).filter_by(key=key).first()
            
            if setting:
                setting.value = value
                if description:
                    setting.description = description
            else:
                setting = Settings(key=key, value=value, description=description)
                session.add(setting)
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في حفظ الإعداد {key}: {e}")
            return False
        finally:
            session.close()
    
    def backup_database(self, backup_path=None):
        """Create database backup"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = Config.DB_BACKUP_DIR / f'hussiny_backup_{timestamp}.db'
            
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # For SQLite, we can simply copy the file
            import shutil
            shutil.copy2(Config.DB_PATH, backup_path)
            
            # Record backup in database
            session = self.get_session()
            try:
                from models import Backup
                backup_record = Backup(
                    file_path=str(backup_path),
                    size=backup_path.stat().st_size,
                    created_by=1  # Default to admin user, should be current user
                )
                session.add(backup_record)
                session.commit()
            except Exception as e:
                logger.error(f"خطأ في تسجيل النسخة الاحتياطية: {e}")
            finally:
                session.close()
            
            logger.info(f"تم إنشاء نسخة احتياطية: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            return None
    
    def restore_database(self, backup_path):
        """Restore database from backup"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"ملف النسخة الاحتياطية غير موجود: {backup_path}")
            
            # Close current connections
            if self.engine:
                self.engine.dispose()
            
            # Backup current database before restore
            current_backup = self.backup_database()
            if current_backup:
                logger.info(f"تم إنشاء نسخة احتياطية من قاعدة البيانات الحالية: {current_backup}")
            
            # Restore from backup
            import shutil
            shutil.copy2(backup_path, Config.DB_PATH)
            
            # Reinitialize database connection
            self.initialize()
            
            logger.info(f"تم استعادة قاعدة البيانات من: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في استعادة قاعدة البيانات: {e}")
            return False
    
    def cleanup_old_backups(self, max_backups=None):
        """Remove old backup files"""
        if max_backups is None:
            max_backups = Config.DB_MAX_BACKUPS
        
        try:
            import glob
            backup_pattern = str(Config.DB_BACKUP_DIR / 'hussiny_backup_*.db')
            backup_files = glob.glob(backup_pattern)
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: Path(x).stat().st_ctime, reverse=True)
            
            # Remove old backups
            for old_backup in backup_files[max_backups:]:
                try:
                    Path(old_backup).unlink()
                    logger.info(f"تم حذف النسخة الاحتياطية القديمة: {old_backup}")
                except Exception as e:
                    logger.error(f"خطأ في حذف النسخة الاحتياطية {old_backup}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تنظيف النسخ الاحتياطية: {e}")
            return False
    
    def get_database_stats(self):
        """Get database statistics"""
        session = self.get_session()
        try:
            from models import Product, Sale, Repair, Transfer
            
            stats = {
                'users': session.query(User).count(),
                'products': session.query(Product).filter_by(active=True).count(),
                'sales': session.query(Sale).count(),
                'repairs': session.query(Repair).count(),
                'transfers': session.query(Transfer).count(),
                'database_size': self._get_database_size()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"خطأ في قراءة إحصائيات قاعدة البيانات: {e}")
            return {}
        finally:
            session.close()
    
    def _get_database_size(self):
        """Get database file size in bytes"""
        try:
            return Config.DB_PATH.stat().st_size
        except Exception:
            return 0
    
    def vacuum_database(self):
        """Optimize database by running VACUUM command"""
        try:
            with self.engine.connect() as connection:
                connection.execute(text('VACUUM'))
            logger.info("تم تحسين قاعدة البيانات")
            return True
        except Exception as e:
            logger.error(f"خطأ في تحسين قاعدة البيانات: {e}")
            return False
    
    def check_integrity(self):
        """Check database integrity"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text('PRAGMA integrity_check')).fetchall()
                
                if result and result[0][0] == 'ok':
                    logger.info("فحص سلامة قاعدة البيانات: مطابق")
                    return True, "فحص سلامة قاعدة البيانات مطابق"
                else:
                    error_msg = f"مشاكل في سلامة قاعدة البيانات: {result}"
                    logger.error(error_msg)
                    return False, error_msg
                    
        except Exception as e:
            error_msg = f"خطأ في فحص سلامة قاعدة البيانات: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def close(self):
        """Close database connections"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("تم إغلاق اتصال قاعدة البيانات")
        except Exception as e:
            logger.error(f"خطأ في إغلاق قاعدة البيانات: {e}")
