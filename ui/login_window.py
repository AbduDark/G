import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from services.auth_service import AuthService
from ui.main_window import MainWindow
from ui.styles import get_stylesheet

class LoginWindow(QWidget):
    """Login window for user authentication"""
    
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.main_window = None
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("نظام إدارة محل الحسيني - تسجيل الدخول")
        self.setFixedSize(400, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Center the window
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo/Title section
        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title_label = QLabel("نظام إدارة محل الحسيني")
        title_label.setObjectName("title-label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Noto Sans Arabic", 20, QFont.Weight.Bold)
        title_label.setFont(title_font)
        
        subtitle_label = QLabel("نظام متكامل لإدارة المبيعات والمخزون")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont("Noto Sans Arabic", 12)
        subtitle_label.setFont(subtitle_font)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addSpacing(20)
        
        # Login form frame
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Shape.Box)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(30, 30, 30, 30)
        
        # Email field
        email_label = QLabel("البريد الإلكتروني:")
        email_label.setFont(QFont("Noto Sans Arabic", 11, QFont.Weight.Bold))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ادخل البريد الإلكتروني")
        self.email_input.setText("alhussiny@admin.com")  # Default for demo
        
        # Password field  
        password_label = QLabel("كلمة المرور:")
        password_label.setFont(QFont("Noto Sans Arabic", 11, QFont.Weight.Bold))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("ادخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setText("admin@1234")  # Default for demo
        
        # Login button
        self.login_button = QPushButton("تسجيل الدخول")
        self.login_button.setFont(QFont("Noto Sans Arabic", 12, QFont.Weight.Bold))
        self.login_button.clicked.connect(self.handle_login)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setObjectName("error-label")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        
        # Add widgets to form layout
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.login_button)
        form_layout.addWidget(self.error_label)
        
        # Add everything to main layout
        main_layout.addLayout(title_layout)
        main_layout.addWidget(form_frame)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # Connect Enter key to login
        self.password_input.returnPressed.connect(self.handle_login)
        self.email_input.returnPressed.connect(self.handle_login)
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(get_stylesheet("light"))
    
    def handle_login(self):
        """Handle login button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            self.show_error("يرجى إدخال البريد الإلكتروني وكلمة المرور")
            return
        
        try:
            user = self.auth_service.authenticate(email, password)
            if user:
                # Login successful
                self.hide()
                self.main_window = MainWindow(user)
                self.main_window.show()
                
                # Connect to main window closed signal
                self.main_window.closed.connect(self.show)
            else:
                self.show_error("البريد الإلكتروني أو كلمة المرور غير صحيحة")
        
        except Exception as e:
            self.show_error(f"خطأ في تسجيل الدخول: {str(e)}")
    
    def show_error(self, message):
        """Show error message"""
        self.error_label.setText(message)
        self.error_label.show()
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, 
            'تأكيد الخروج',
            'هل أنت متأكد من الخروج من النظام؟',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
            sys.exit()
        else:
            event.ignore()
