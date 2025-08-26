# -*- coding: utf-8 -*-
"""
Base window class for Al-Hussiny Mobile Shop POS System
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFrame, QMessageBox, QStatusBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
import logging

logger = logging.getLogger(__name__)

class BaseWindow(QMainWindow):
    """Base window class with common functionality"""
    
    # Signals
    window_closing = pyqtSignal()
    
    def __init__(self, db_manager, user_data=None, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.user_data = user_data
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Window properties
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setup_window()
        self.setup_ui()
        self.setup_statusbar()
        
    def setup_window(self):
        """Setup basic window properties"""
        # Set minimum size
        self.setMinimumSize(800, 600)
        
        # Set window flags
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
    
    def setup_ui(self):
        """Setup user interface - to be overridden by subclasses"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Header
        self.setup_header()
        
        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.main_layout.addWidget(self.content_widget)
    
    def setup_header(self):
        """Setup window header with title and user info"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_frame.setMaximumHeight(60)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Window title
        self.title_label = QLabel("نافذة أساسية")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # User info
        if self.user_data:
            user_label = QLabel(f"المستخدم: {self.user_data['name']}")
            user_font = QFont()
            user_font.setPointSize(10)
            user_label.setFont(user_font)
            header_layout.addWidget(user_label)
        
        self.main_layout.addWidget(header_frame)
    
    def setup_statusbar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("جاهز")
    
    def set_title(self, title):
        """Set window and header title"""
        self.setWindowTitle(title)
        if hasattr(self, 'title_label'):
            self.title_label.setText(title)
    
    def show_message(self, message, message_type="info"):
        """Show message to user"""
        if message_type == "error":
            QMessageBox.critical(self, "خطأ", message)
        elif message_type == "warning":
            QMessageBox.warning(self, "تحذير", message)
        elif message_type == "success":
            QMessageBox.information(self, "نجح", message)
        else:
            QMessageBox.information(self, "معلومات", message)
    
    def show_question(self, question, title="تأكيد"):
        """Show yes/no question dialog"""
        reply = QMessageBox.question(
            self, title, question,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def update_status(self, message):
        """Update status bar message"""
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage(message)
    
    def center_on_screen(self):
        """Center window on screen"""
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        window = self.frameGeometry()
        window.moveCenter(screen.center())
        self.move(window.topLeft())
    
    def has_permission(self, permission):
        """Check if current user has permission"""
        if not self.user_data:
            return False
        
        permissions = self.user_data.get('permissions', [])
        return 'all' in permissions or permission in permissions
    
    def require_permission(self, permission, action_name="هذا الإجراء"):
        """Check permission and show error if not allowed"""
        if not self.has_permission(permission):
            self.show_message(
                f"ليس لديك صلاحية لتنفيذ {action_name}",
                "error"
            )
            return False
        return True
    
    def log_action(self, action, details=None):
        """Log user action for audit trail"""
        try:
            if self.user_data and self.db_manager:
                session = self.db_manager.get_session()
                try:
                    from models import AuditLog
                    
                    audit_log = AuditLog(
                        user_id=self.user_data['id'],
                        action=action,
                        details=details
                    )
                    session.add(audit_log)
                    session.commit()
                    
                except Exception as e:
                    session.rollback()
                    self.logger.error(f"خطأ في تسجيل الحدث: {e}")
                finally:
                    session.close()
                    
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل الحدث: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.window_closing.emit()
        event.accept()
    
    def refresh_data(self):
        """Refresh window data - to be overridden by subclasses"""
        pass
    
    def apply_style(self, style_sheet):
        """Apply custom stylesheet"""
        self.setStyleSheet(style_sheet)

class BaseDialog(BaseWindow):
    """Base dialog class"""
    
    def __init__(self, db_manager, user_data=None, parent=None):
        super().__init__(db_manager, user_data, parent)
        
        # Make it a dialog
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint
        )
    
    def setup_buttons(self):
        """Setup dialog buttons"""
        button_layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # OK button
        self.ok_button = QPushButton("موافق")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        button_layout.addStretch()
        
        # Add to main layout
        if hasattr(self, 'main_layout'):
            self.main_layout.addLayout(button_layout)
    
    def accept(self):
        """Handle dialog acceptance"""
        if self.validate_input():
            self.save_data()
            super().accept()
    
    def reject(self):
        """Handle dialog rejection"""
        super().reject()
    
    def validate_input(self):
        """Validate input data - to be overridden by subclasses"""
        return True
    
    def save_data(self):
        """Save dialog data - to be overridden by subclasses"""
        pass
