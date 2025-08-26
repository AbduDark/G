# -*- coding: utf-8 -*-
"""
Login window for Al-Hussiny Mobile Shop POS System
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QFrame, QSpacerItem, 
                            QSizePolicy, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPalette
import logging

from config import Config

logger = logging.getLogger(__name__)

class LoginWindow(QWidget):
    """Login window for user authentication"""
    
    # Signals
    login_successful = pyqtSignal(dict)  # Emits user data
    
    def __init__(self, db_manager):
        super().__init__()
        
        self.db_manager = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.setup_ui()
        self.setup_connections()
        self.center_on_screen()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("تسجيل الدخول - محل الحسيني")
        self.setFixedSize(400, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Spacer at top
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Logo/Title section
        self.setup_header(main_layout)
        
        # Login form
        self.setup_form(main_layout)
        
        # Login button
        self.setup_buttons(main_layout)
        
        # Spacer at bottom
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Default credentials info
        self.setup_info(main_layout)
        
    def setup_header(self, layout):
        """Setup header with logo and title"""
        # Shop name
        title_label = QLabel(Config.SHOP_NAME)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        # Subtitle
        subtitle_label = QLabel("نظام إدارة المبيعات والمخزون")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 20px;")
        
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
    
    def setup_form(self, layout):
        """Setup login form"""
        # Form frame
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        
        # Email field
        email_label = QLabel("البريد الإلكتروني:")
        email_label.setStyleSheet("font-weight: bold; color: #495057;")
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("أدخل البريد الإلكتروني")
        self.email_edit.setText(Config.DEFAULT_ADMIN_EMAIL)  # Pre-fill for convenience
        self.email_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                font-size: 11pt;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        
        # Password field
        password_label = QLabel("كلمة المرور:")
        password_label.setStyleSheet("font-weight: bold; color: #495057;")
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("أدخل كلمة المرور")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setText(Config.DEFAULT_ADMIN_PASSWORD)  # Pre-fill for convenience
        self.password_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                font-size: 11pt;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        
        # Add to form layout
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_edit)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_edit)
        
        layout.addWidget(form_frame)
    
    def setup_buttons(self, layout):
        """Setup login button"""
        self.login_button = QPushButton("تسجيل الدخول")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 6px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        layout.addWidget(self.login_button)
    
    def setup_info(self, layout):
        """Setup default credentials info"""
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("بيانات المدير الافتراضي:")
        info_title.setStyleSheet("font-weight: bold; font-size: 10pt;")
        
        info_email = QLabel(f"البريد: {Config.DEFAULT_ADMIN_EMAIL}")
        info_password = QLabel(f"كلمة المرور: {Config.DEFAULT_ADMIN_PASSWORD}")
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_email)
        info_layout.addWidget(info_password)
        
        layout.addWidget(info_frame)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.login_button.clicked.connect(self.login)
        self.email_edit.returnPressed.connect(self.login)
        self.password_edit.returnPressed.connect(self.login)
    
    def login(self):
        """Handle login attempt"""
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        
        # Validate input
        if not email:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال البريد الإلكتروني")
            self.email_edit.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال كلمة المرور")
            self.password_edit.setFocus()
            return
        
        # Disable login button during authentication
        self.login_button.setEnabled(False)
        self.login_button.setText("جاري التحقق...")
        
        try:
            # Authenticate user
            user_data = self.db_manager.authenticate_user(email, password)
            
            if user_data:
                # Successful login
                self.logger.info(f"تسجيل دخول ناجح: {email}")
                self.login_successful.emit(user_data)
            else:
                # Failed login
                self.logger.warning(f"فشل تسجيل الدخول: {email}")
                QMessageBox.critical(
                    self, 
                    "فشل تسجيل الدخول", 
                    "البريد الإلكتروني أو كلمة المرور غير صحيحة"
                )
                self.password_edit.clear()
                self.password_edit.setFocus()
                
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل الدخول: {e}")
            QMessageBox.critical(
                self, 
                "خطأ", 
                f"حدث خطأ أثناء تسجيل الدخول:\n{str(e)}"
            )
        
        finally:
            # Re-enable login button
            self.login_button.setEnabled(True)
            self.login_button.setText("تسجيل الدخول")
    
    def center_on_screen(self):
        """Center window on screen"""
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        window = self.frameGeometry()
        window.moveCenter(screen.center())
        self.move(window.topLeft())
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)
