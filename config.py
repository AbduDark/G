# -*- coding: utf-8 -*-
"""
Configuration settings for Al-Hussiny Mobile Shop POS System
"""

import os
from pathlib import Path

class Config:
    """Application configuration class"""
    
    # Application settings
    APP_NAME = "محل الحسيني للهواتف المحمولة"
    APP_VERSION = "1.0.0"
    APP_AUTHOR = "Al-Hussiny Mobile Shop"
    
    # Database settings
    BASE_DIR = Path(__file__).parent
    DB_PATH = BASE_DIR / "hussiny.db"
    DB_BACKUP_DIR = BASE_DIR / "backups"
    DB_MAX_BACKUPS = 10
    
    # Shop information (editable through settings)
    SHOP_NAME = "محل الحسيني للهواتف المحمولة"
    SHOP_ADDRESS = "العنوان يتم تحديده من الإعدادات"
    SHOP_PHONE = "رقم الهاتف يتم تحديده من الإعدادات"
    SHOP_EMAIL = "البريد الإلكتروني يتم تحديده من الإعدادات"
    SHOP_LOGO_PATH = ""
    
    # Default admin credentials
    DEFAULT_ADMIN_EMAIL = "alhussiny@admin.com"
    DEFAULT_ADMIN_PASSWORD = "admin@1234"
    DEFAULT_ADMIN_NAME = "مدير النظام"
    
    # Theme settings
    DEFAULT_THEME = "light"  # light or dark
    AVAILABLE_THEMES = ["light", "dark"]
    
    # Window settings
    MAIN_WINDOW_MIN_SIZE = (1366, 768)
    DIALOG_DEFAULT_SIZE = (800, 600)
    
    # Mobile accessories categories
    DEFAULT_CATEGORIES = [
        'سماعات اذن', 'سماعات', 'شاحن', 'ماوس', 'ميكات', 'ليدر', 
        'اوتو جي', 'جراب', 'وصلة مايكرو', 'وصلة تايب', 'اكسسوار', 
        'ستاند', 'سكرينه', 'ايربودز', 'كمبيوتر', 'باور بنك', 'اخري'
    ]
    
    # User roles and permissions
    DEFAULT_ROLES = {
        'Admin': {
            'name_ar': 'مدير',
            'permissions': ['all']
        },
        'Manager': {
            'name_ar': 'مدير فرع',
            'permissions': ['sales', 'inventory', 'reports', 'repairs']
        },
        'Cashier': {
            'name_ar': 'كاشير',
            'permissions': ['sales', 'returns']
        },
        'Technician': {
            'name_ar': 'فني',
            'permissions': ['repairs', 'inventory_view']
        },
        'Viewer': {
            'name_ar': 'مراقب',
            'permissions': ['view_only']
        }
    }
    
    # Repair statuses
    REPAIR_STATUSES = [
        'قيد الفحص',
        'قيد الانتظار',
        'تم الإصلاح',
        'غير قابل للإصلاح',
        'في انتظار قطع الغيار',
        'تم التسليم'
    ]
    
    # Transfer types for mobile credit
    TRANSFER_TYPES = [
        'فودافون كاش',
        'اتصالات كاش', 
        'اورانج كاش',
        'اكسس كاش',
        'كرت فكّ',
        'تحويل نقدي',
        'أخرى'
    ]
    
    # Tax settings
    DEFAULT_TAX_RATE = 0.14  # 14% VAT
    CURRENCY_SYMBOL = "ج.م"  # Egyptian Pound
    
    # Printer settings
    RECEIPT_PRINTER_NAME = ""  # Default system printer
    RECEIPT_WIDTH = 58  # mm for thermal printers
    A4_PRINTER_NAME = ""  # Default system printer
    
    # Backup settings
    AUTO_BACKUP_ENABLED = True
    AUTO_BACKUP_INTERVAL = 24  # hours
    BACKUP_COMPRESSION = True
    
    # Search settings
    SEARCH_MIN_CHARS = 2
    SEARCH_MAX_RESULTS = 50
    
    # Pagination settings
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Invoice settings
    INVOICE_PREFIX = "INV"
    REPAIR_TICKET_PREFIX = "REP"
    
    # Fonts
    ARABIC_FONT_FAMILY = "Noto Kufi Arabic"
    ARABIC_FONT_SIZE = 11
    ENGLISH_FONT_FAMILY = "Arial"
    ENGLISH_FONT_SIZE = 10
    
    # File paths
    FONTS_DIR = BASE_DIR / "resources" / "fonts"
    ICONS_DIR = BASE_DIR / "resources" / "icons"
    TEMPLATES_DIR = BASE_DIR / "templates"
    LOGS_DIR = BASE_DIR / "logs"
    EXPORTS_DIR = BASE_DIR / "exports"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.DB_BACKUP_DIR,
            cls.LOGS_DIR,
            cls.EXPORTS_DIR,
            cls.FONTS_DIR,
            cls.ICONS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_db_url(cls):
        """Get database URL for SQLAlchemy"""
        return f"sqlite:///{cls.DB_PATH}"
    
    @classmethod
    def load_from_database(cls, db_manager):
        """Load configuration from database settings table"""
        try:
            # This would load settings from a settings table in the database
            # For now, we'll use default values
            pass
        except Exception:
            # If no settings table exists or error occurs, use defaults
            pass
    
    @classmethod
    def save_to_database(cls, db_manager, settings_dict):
        """Save configuration to database settings table"""
        try:
            # This would save settings to a settings table in the database
            # Implementation would depend on the settings table structure
            pass
        except Exception:
            # Handle save errors gracefully
            pass

# Create directories on module import
Config.ensure_directories()
