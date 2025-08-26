import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtCore import Qt, QTimer, QTranslator, QLocale
from PyQt6.QtGui import QPixmap, QFont, QFontDatabase

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from database import DatabaseManager
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from styles.dark_theme import DarkTheme
from styles.light_theme import LightTheme
from utils.arabic_utils import setup_arabic_locale

class AlHussinyApp(QApplication):
    """Main application class"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Set application properties
        self.setApplicationName("محل الحسيني")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Al-Hussiny Mobile Shop")
        self.setOrganizationDomain("alhussiny.local")
        
        # Setup logging
        self.setup_logging()
        
        # Setup Arabic support
        self.setup_arabic_support()
        
        # Initialize database
        self.db_manager = DatabaseManager()
        self.init_database()
        
        # Setup theme
        self.setup_theme()
        
        # Initialize windows
        self.login_window = None
        self.main_window = None
        
        # Show splash screen
        self.show_splash_screen()

    def setup_logging(self):
        """Setup application logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'alhussiny.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("تم بدء تشغيل نظام محل الحسيني")

    def setup_arabic_support(self):
        """Setup Arabic language and RTL support"""
        try:
            # Setup Arabic locale
            setup_arabic_locale()
            
            # Load Arabic fonts
            font_path = project_root / "resources" / "fonts" / "NotoKufiArabic-Regular.ttf"
            if font_path.exists():
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        arabic_font = QFont(font_families[0], 11)
                        self.setFont(arabic_font)
                        self.logger.info("تم تحميل الخط العربي بنجاح")
            
            # Set layout direction to RTL
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            
        except Exception as e:
            self.logger.error(f"خطأ في إعداد الدعم العربي: {e}")

    def init_database(self):
        """Initialize database connection and schema"""
        try:
            if not self.db_manager.initialize():
                QMessageBox.critical(
                    None,
                    "خطأ في قاعدة البيانات",
                    "فشل في الاتصال بقاعدة البيانات"
                )
                sys.exit(1)
            
            self.logger.info("تم تهيئة قاعدة البيانات بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
            QMessageBox.critical(
                None,
                "خطأ في قاعدة البيانات",
                f"فشل في تهيئة قاعدة البيانات:\n{str(e)}"
            )
            sys.exit(1)

    def setup_theme(self):
        """Setup application theme"""
        try:
            # Load theme from config or default to light
            theme_name = getattr(Config, 'DEFAULT_THEME', 'light')
            
            if theme_name == 'dark':
                theme = DarkTheme()
            else:
                theme = LightTheme()
            
            self.setStyleSheet(theme.get_stylesheet())
            self.logger.info(f"تم تطبيق المظهر: {theme_name}")
            
        except Exception as e:
            self.logger.error(f"خطأ في تطبيق المظهر: {e}")

    def show_splash_screen(self):
        """Show splash screen during initialization"""
        try:
            # Create splash screen
            splash_pixmap = QPixmap(400, 300)
            splash_pixmap.fill(Qt.GlobalColor.white)
            
            self.splash = QSplashScreen(splash_pixmap)
            self.splash.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint | 
                Qt.WindowType.FramelessWindowHint
            )
            
            # Show splash screen
            self.splash.show()
            self.splash.showMessage(
                "محل الحسيني للهواتف المحمولة\nجاري التحميل...",
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom,
                Qt.GlobalColor.black
            )
            
            # Close splash screen after 2 seconds
            QTimer.singleShot(2000, self.init_login_window)
            
        except Exception as e:
            self.logger.error(f"خطأ في عرض شاشة البداية: {e}")
            # If splash fails, go directly to login
            self.init_login_window()

    def init_login_window(self):
        """Initialize and show login window"""
        try:
            # Close splash screen
            if hasattr(self, 'splash'):
                self.splash.close()
            
            # Create and show login window
            self.login_window = LoginWindow(self.db_manager)
            self.login_window.login_successful.connect(self.on_login_successful)
            self.login_window.show()
            
            self.logger.info("تم عرض نافذة تسجيل الدخول")
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء نافذة تسجيل الدخول: {e}")
            QMessageBox.critical(
                None,
                "خطأ في التطبيق",
                f"فشل في تشغيل التطبيق:\n{str(e)}"
            )
            sys.exit(1)

    def on_login_successful(self, user_data):
        """Handle successful login"""
        try:
            # Close login window
            if self.login_window:
                self.login_window.close()
                self.login_window = None
            
            # Create and show main window
            self.main_window = MainWindow(self.db_manager, user_data)
            self.main_window.logout_requested.connect(self.on_logout)
            self.main_window.show()
            
            self.logger.info(f"تم تسجيل دخول المستخدم: {user_data['name']}")
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء النافذة الرئيسية: {e}")
            QMessageBox.critical(
                None,
                "خطأ في التطبيق",
                f"فشل في إنشاء النافذة الرئيسية:\n{str(e)}"
            )

    def on_logout(self):
        """Handle user logout"""
        try:
            # Close main window
            if self.main_window:
                self.main_window.close()
                self.main_window = None
            
            # Show login window again
            self.init_login_window()
            
            self.logger.info("تم تسجيل خروج المستخدم")
            
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل الخروج: {e}")

def main():
    """Main application entry point"""
    try:
        # Create application
        app = AlHussinyApp(sys.argv)
        
        # Handle application exit
        def cleanup():
            logging.getLogger(__name__).info("تم إغلاق نظام محل الحسيني")
        
        app.aboutToQuit.connect(cleanup)
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        logging.error(f"خطأ فادح في التطبيق: {e}")
        if 'app' in locals():
            QMessageBox.critical(
                None,
                "خطأ فادح",
                f"حدث خطأ فادح في التطبيق:\n{str(e)}"
            )
        sys.exit(1)

if __name__ == "__main__":
    main()
