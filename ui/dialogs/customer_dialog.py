# -*- coding: utf-8 -*-
"""
Customer add/edit dialog
"""

import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLineEdit, QPushButton, QLabel, QTextEdit,
                            QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.user import User
from models.sales import Customer
from config.database import get_db_session
from utils.helpers import show_error, show_success
from utils.validators import validate_phone, validate_email

class CustomerDialog(QDialog):
    """Dialog for adding/editing customers"""
    
    def __init__(self, parent=None, user: User = None, customer_id: int = None):
        super().__init__(parent)
        self.current_user = user
        self.customer_id = customer_id
        self.customer = None
        
        self.setup_ui()
        
        if customer_id:
            self.load_customer()
            
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("إضافة عميل جديد" if not self.customer_id else "تعديل بيانات العميل")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Customer info group
        info_group = QGroupBox("معلومات العميل")
        info_layout = QFormLayout()
        
        # Customer name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم العميل الكامل")
        
        # Phone number
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الهاتف")
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("البريد الإلكتروني (اختياري)")
        
        # Address
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        self.address_input.setPlaceholderText("العنوان (اختياري)")
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("ملاحظات إضافية (اختياري)")
        
        info_layout.addRow("اسم العميل *:", self.name_input)
        info_layout.addRow("رقم الهاتف *:", self.phone_input)
        info_layout.addRow("البريد الإلكتروني:", self.email_input)
        info_layout.addRow("العنوان:", self.address_input)
        info_layout.addRow("ملاحظات:", self.notes_input)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Statistics group (for existing customers)
        if self.customer_id:
            self.stats_group = QGroupBox("إحصائيات العميل")
            stats_layout = QFormLayout()
            
            self.total_purchases_label = QLabel("0")
            self.total_amount_label = QLabel("0.00 ج.م")
            self.last_purchase_label = QLabel("لا توجد مشتريات")
            
            stats_layout.addRow("إجمالي المشتريات:", self.total_purchases_label)
            stats_layout.addRow("إجمالي المبلغ:", self.total_amount_label)
            stats_layout.addRow("آخر شراء:", self.last_purchase_label)
            
            self.stats_group.setLayout(stats_layout)
            layout.addWidget(self.stats_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("حفظ")
        self.save_and_new_btn = QPushButton("حفظ وإضافة جديد")
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
        if not self.customer_id:  # Only show for new customers
            buttons_layout.addWidget(self.save_and_new_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        # Connect signals
        self.save_btn.clicked.connect(self.save_customer)
        if not self.customer_id:
            self.save_and_new_btn.clicked.connect(self.save_and_new_customer)
        self.cancel_btn.clicked.connect(self.reject)
        
    def load_customer(self):
        """Load customer data for editing"""
        session = get_db_session()
        try:
            customer = session.query(Customer).get(self.customer_id)
            if not customer:
                show_error(self, "العميل غير موجود")
                self.reject()
                return
                
            self.customer = customer
            
            # Populate form fields
            self.name_input.setText(customer.name)
            self.phone_input.setText(customer.phone or "")
            self.email_input.setText(customer.email or "")
            self.address_input.setPlainText(customer.address or "")
            self.notes_input.setPlainText(customer.notes or "")
            
            # Load statistics
            if hasattr(self, 'stats_group'):
                self.load_customer_statistics()
                
        finally:
            session.close()
            
    def load_customer_statistics(self):
        """Load customer purchase statistics"""
        session = get_db_session()
        try:
            from models.sales import Sale
            from sqlalchemy import func
            
            # Get purchase statistics
            stats = session.query(
                func.count(Sale.id).label('total_purchases'),
                func.sum(Sale.total).label('total_amount'),
                func.max(Sale.created_at).label('last_purchase')
            ).filter(Sale.customer_id == self.customer_id).first()
            
            if stats:
                self.total_purchases_label.setText(str(stats.total_purchases or 0))
                self.total_amount_label.setText(f"{stats.total_amount or 0:.2f} ج.م")
                
                if stats.last_purchase:
                    self.last_purchase_label.setText(stats.last_purchase.strftime("%Y-%m-%d"))
                else:
                    self.last_purchase_label.setText("لا توجد مشتريات")
                    
        finally:
            session.close()
            
    def validate_form(self):
        """Validate form data"""
        # Required fields
        if not self.name_input.text().strip():
            show_error(self, "يرجى إدخال اسم العميل")
            self.name_input.setFocus()
            return False
            
        if not self.phone_input.text().strip():
            show_error(self, "يرجى إدخال رقم الهاتف")
            self.phone_input.setFocus()
            return False
            
        # Validate phone number
        phone = self.phone_input.text().strip()
        if not validate_phone(phone):
            show_error(self, "رقم الهاتف غير صالح")
            self.phone_input.setFocus()
            return False
            
        # Validate email if provided
        email = self.email_input.text().strip()
        if email and not validate_email(email):
            show_error(self, "البريد الإلكتروني غير صالح")
            self.email_input.setFocus()
            return False
            
        return True
        
    def check_duplicate_phone(self, phone: str):
        """Check for duplicate phone number"""
        session = get_db_session()
        try:
            existing_customer = session.query(Customer).filter_by(phone=phone).first()
            
            if existing_customer and existing_customer.id != self.customer_id:
                reply = QMessageBox.question(
                    self, "رقم هاتف مكرر",
                    f"رقم الهاتف '{phone}' مرتبط بالعميل '{existing_customer.name}' مسبقاً.\n"
                    "هل تريد المتابعة؟"
                )
                return reply == QMessageBox.StandardButton.Yes
                
            return True
            
        finally:
            session.close()
            
    def save_customer(self):
        """Save customer data"""
        if not self.validate_form():
            return False
            
        phone = self.phone_input.text().strip()
        if not self.check_duplicate_phone(phone):
            return False
            
        session = get_db_session()
        try:
            if self.customer_id:
                # Update existing customer
                customer = session.query(Customer).get(self.customer_id)
                if not customer:
                    show_error(self, "العميل غير موجود")
                    return False
            else:
                # Create new customer
                customer = Customer()
                
            # Update customer data
            customer.name = self.name_input.text().strip()
            customer.phone = phone
            customer.email = self.email_input.text().strip() or None
            customer.address = self.address_input.toPlainText().strip() or None
            customer.notes = self.notes_input.toPlainText().strip() or None
            
            if not self.customer_id:
                session.add(customer)
                
            session.commit()
            
            # Log the action
            from models.audit import AuditLog
            action = "create" if not self.customer_id else "update"
            AuditLog.log_action(
                session, self.current_user.id, action, "customers",
                record_id=customer.id,
                details=f"Customer: {customer.name} ({customer.phone})"
            )
            session.commit()
            
            self.accept()
            return True
            
        except Exception as e:
            session.rollback()
            logging.error(f"Customer save error: {e}")
            show_error(self, f"فشل في حفظ بيانات العميل:\n{str(e)}")
            return False
        finally:
            session.close()
            
    def save_and_new_customer(self):
        """Save current customer and create new one"""
        if self.save_customer():
            # Clear form for new customer
            self.name_input.clear()
            self.phone_input.clear()
            self.email_input.clear()
            self.address_input.clear()
            self.notes_input.clear()
            
            # Focus on name field
            self.name_input.setFocus()
