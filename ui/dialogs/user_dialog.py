# -*- coding: utf-8 -*-
"""
User add/edit dialog
"""

import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLineEdit, QComboBox, QPushButton, QLabel, QGroupBox,
                            QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import bcrypt

from models.user import User, Role
from config.database import get_db_session
from utils.helpers import show_error, show_success
from utils.validators import validate_email, validate_password

class UserDialog(QDialog):
    """Dialog for adding/editing users"""
    
    def __init__(self, parent=None, current_user: User = None, user_id: int = None):
        super().__init__(parent)
        self.current_user = current_user
        self.user_id = user_id
        self.user = None
        self.roles = []
        
        self.setup_ui()
        self.load_data()
        
        if user_id:
            self.load_user()
            
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("إضافة مستخدم جديد" if not self.user_id else "تعديل المستخدم")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout()
        
        # User info group
        info_group = QGroupBox("معلومات المستخدم")
        info_layout = QFormLayout()
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("الاسم الكامل للمستخدم")
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("البريد الإلكتروني")
        
        # Role
        self.role_combo = QComboBox()
        
        # Password (only for new users or when changing)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("كلمة المرور")
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("تأكيد كلمة المرور")
        
        # Change password checkbox (for existing users)
        if self.user_id:
            self.change_password_checkbox = QCheckBox("تغيير كلمة المرور")
            self.change_password_checkbox.toggled.connect(self.toggle_password_fields)
            info_layout.addRow("", self.change_password_checkbox)
            
        # Active status
        self.active_checkbox = QCheckBox("مستخدم نشط")
        self.active_checkbox.setChecked(True)
        
        info_layout.addRow("الاسم *:", self.name_input)
        info_layout.addRow("البريد الإلكتروني *:", self.email_input)
        info_layout.addRow("الدور *:", self.role_combo)
        info_layout.addRow("كلمة المرور *:", self.password_input)
        info_layout.addRow("تأكيد كلمة المرور *:", self.confirm_password_input)
        info_layout.addRow("", self.active_checkbox)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Password requirements
        password_group = QGroupBox("متطلبات كلمة المرور")
        password_layout = QVBoxLayout()
        
        requirements = [
            "• يجب أن تحتوي على 8 أحرف على الأقل",
            "• يجب أن تحتوي على حرف كبير واحد على الأقل",
            "• يجب أن تحتوي على حرف صغير واحد على الأقل",
            "• يجب أن تحتوي على رقم واحد على الأقل"
        ]
        
        for req in requirements:
            req_label = QLabel(req)
            req_label.setStyleSheet("color: #6c757d; font-size: 11px;")
            password_layout.addWidget(req_label)
            
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("حفظ")
        self.cancel_btn = QPushButton("إلغاء")
        
        # Style save button
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        # Connect signals
        self.save_btn.clicked.connect(self.save_user)
        self.cancel_btn.clicked.connect(self.reject)
        
        # Set initial password field state
        if self.user_id:
            self.toggle_password_fields(False)
            
    def load_data(self):
        """Load roles data"""
        session = get_db_session()
        try:
            roles = session.query(Role).all()
            self.roles = roles
            
            self.role_combo.clear()
            for role in roles:
                self.role_combo.addItem(role.name, role.id)
                
        finally:
            session.close()
            
    def load_user(self):
        """Load user data for editing"""
        session = get_db_session()
        try:
            user = session.query(User).get(self.user_id)
            if not user:
                show_error(self, "المستخدم غير موجود")
                self.reject()
                return
                
            self.user = user
            
            # Populate form fields
            self.name_input.setText(user.name)
            self.email_input.setText(user.email)
            self.active_checkbox.setChecked(user.active)
            
            # Set role
            if user.role_id:
                for i in range(self.role_combo.count()):
                    if self.role_combo.itemData(i) == user.role_id:
                        self.role_combo.setCurrentIndex(i)
                        break
                        
        finally:
            session.close()
            
    def toggle_password_fields(self, enabled: bool):
        """Toggle password field visibility"""
        self.password_input.setEnabled(enabled)
        self.confirm_password_input.setEnabled(enabled)
        
        if not enabled:
            self.password_input.clear()
            self.confirm_password_input.clear()
            
    def validate_form(self):
        """Validate form data"""
        # Required fields
        if not self.name_input.text().strip():
            show_error(self, "يرجى إدخال اسم المستخدم")
            self.name_input.setFocus()
            return False
            
        if not self.email_input.text().strip():
            show_error(self, "يرجى إدخال البريد الإلكتروني")
            self.email_input.setFocus()
            return False
            
        if self.role_combo.currentData() is None:
            show_error(self, "يرجى اختيار دور المستخدم")
            self.role_combo.setFocus()
            return False
            
        # Validate email
        email = self.email_input.text().strip()
        if not validate_email(email):
            show_error(self, "البريد الإلكتروني غير صالح")
            self.email_input.setFocus()
            return False
            
        # Password validation (for new users or when changing password)
        password_required = not self.user_id or (hasattr(self, 'change_password_checkbox') and self.change_password_checkbox.isChecked())
        
        if password_required:
            password = self.password_input.text()
            confirm_password = self.confirm_password_input.text()
            
            if not password:
                show_error(self, "يرجى إدخال كلمة المرور")
                self.password_input.setFocus()
                return False
                
            if password != confirm_password:
                show_error(self, "كلمات المرور غير متطابقة")
                self.confirm_password_input.setFocus()
                return False
                
            if not validate_password(password):
                show_error(self, "كلمة المرور لا تلبي المتطلبات المطلوبة")
                self.password_input.setFocus()
                return False
                
        return True
        
    def check_duplicate_email(self, email: str):
        """Check for duplicate email"""
        session = get_db_session()
        try:
            existing_user = session.query(User).filter_by(email=email).first()
            
            if existing_user and existing_user.id != self.user_id:
                show_error(self, f"البريد الإلكتروني '{email}' مستخدم مسبقاً")
                return False
                
            return True
            
        finally:
            session.close()
            
    def save_user(self):
        """Save user data"""
        if not self.validate_form():
            return
            
        email = self.email_input.text().strip()
        if not self.check_duplicate_email(email):
            return
            
        session = get_db_session()
        try:
            if self.user_id:
                # Update existing user
                user = session.query(User).get(self.user_id)
                if not user:
                    show_error(self, "المستخدم غير موجود")
                    return
            else:
                # Create new user
                user = User()
                
            # Update user data
            user.name = self.name_input.text().strip()
            user.email = email
            user.role_id = self.role_combo.currentData()
            user.active = self.active_checkbox.isChecked()
            
            # Update password if needed
            password_changed = False
            if not self.user_id or (hasattr(self, 'change_password_checkbox') and self.change_password_checkbox.isChecked()):
                password = self.password_input.text()
                if password:
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    user.password_hash = password_hash.decode('utf-8')
                    password_changed = True
                    
            if not self.user_id:
                session.add(user)
                
            session.commit()
            
            # Log the action
            from models.audit import AuditLog
            action = "create" if not self.user_id else "update"
            details = f"User: {user.name} ({user.email})"
            if password_changed:
                details += " - Password changed"
                
            AuditLog.log_action(
                session, self.current_user.id, action, "users",
                record_id=user.id, details=details
            )
            session.commit()
            
            self.accept()
            
        except Exception as e:
            session.rollback()
            logging.error(f"User save error: {e}")
            show_error(self, f"فشل في حفظ بيانات المستخدم:\n{str(e)}")
        finally:
            session.close()
