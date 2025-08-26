import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator, QLocale
from PyQt6.QtGui import QFont

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database import init_database
from ui.login_window import LoginWindow
from utils.logger import setup_logger

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Setup application properties
    app.setApplicationName("نظام إدارة محل الحسيني")
    app.setApplicationDisplayName("الحسيني - نظام إدارة المحل")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("الحسيني")
    
    # Setup RTL layout for Arabic
    app.setLayoutDirection(app.layoutDirection().RightToLeft)
    
    # Setup Arabic font
    font = QFont("Noto Sans Arabic", 10)
    app.setFont(font)
    
    # Setup logger
    logger = setup_logger()
    logger.info("بدء تشغيل النظام")
    
    try:
        # Initialize database
        init_database()
        logger.info("تم تهيئة قاعدة البيانات بنجاح")
        
        # Show login window
        login_window = LoginWindow()
        login_window.show()
        
        return app.exec()
        
    except Exception as e:
        logger.error(f"خطأ في تشغيل النظام: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
