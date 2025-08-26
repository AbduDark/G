# -*- coding: utf-8 -*-
"""
Product add/edit dialog
"""

import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox,
                            QTextEdit, QPushButton, QLabel, QMessageBox,
                            QCheckBox, QGroupBox, QTabWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.user import User
from models.product import Product, Category, Supplier
from config.database import get_db_session
from utils.helpers import show_error, show_success
from utils.validators import validate_sku, validate_price

class ProductDialog(QDialog):
    """Dialog for adding/editing products"""
    
    def __init__(self, parent=None, user: User = None, product_id: int = None):
        super().__init__(parent)
        self.current_user = user
        self.product_id = product_id
        self.product = None
        self.categories = []
        self.suppliers = []
        
        self.setup_ui()
        self.load_data()
        
        if product_id:
            self.load_product()
            
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("إضافة منتج جديد" if not self.product_id else "تعديل المنتج")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Basic info tab
        basic_tab = self.create_basic_info_tab()
        tab_widget.addTab(basic_tab, "المعلومات الأساسية")
        
        # Pricing tab
        pricing_tab = self.create_pricing_tab()
        tab_widget.addTab(pricing_tab, "الأسعار والمخزون")
        
        # Additional info tab
        additional_tab = self.create_additional_info_tab()
        tab_widget.addTab(additional_tab, "معلومات إضافية")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("حفظ")
        self.save_and_new_btn = QPushButton("حفظ وإضافة جديد")
        self.cancel_btn = QPushButton("إلغاء")
        
        # Style buttons
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
        if not self.product_id:  # Only show for new products
            buttons_layout.addWidget(self.save_and_new_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        # Connect signals
        self.save_btn.clicked.connect(self.save_product)
        self.save_and_new_btn.clicked.connect(self.save_and_new_product)
        self.cancel_btn.clicked.connect(self.reject)
        
    def create_basic_info_tab(self):
        """Create basic information tab"""
        tab = QGroupBox()
        layout = QFormLayout()
        
        # SKU
        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("كود المنتج الفريد")
        
        # Product name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم المنتج باللغة العربية")
        
        # Category
        self.category_combo = QComboBox()
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("وصف المنتج (اختياري)")
        
        # Barcode
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("الباركود (اختياري)")
        
        # Active status
        self.active_checkbox = QCheckBox("منتج نشط")
        self.active_checkbox.setChecked(True)
        
        layout.addRow("كود المنتج (SKU) *:", self.sku_input)
        layout.addRow("اسم المنتج *:", self.name_input)
        layout.addRow("الفئة *:", self.category_combo)
        layout.addRow("الوصف:", self.description_input)
        layout.addRow("الباركود:", self.barcode_input)
        layout.addRow("", self.active_checkbox)
        
        tab.setLayout(layout)
        return tab
        
    def create_pricing_tab(self):
        """Create pricing and inventory tab"""
        tab = QGroupBox()
        layout = QFormLayout()
        
        # Cost price
        self.cost_price_input = QDoubleSpinBox()
        self.cost_price_input.setMaximum(999999.99)
        self.cost_price_input.setDecimals(2)
        self.cost_price_input.setSuffix(" ج.م")
        
        # Sale price
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setMaximum(999999.99)
        self.sale_price_input.setDecimals(2)
        self.sale_price_input.setSuffix(" ج.م")
        
        # Profit margin (calculated)
        self.profit_margin_label = QLabel("0.00%")
        self.profit_margin_label.setStyleSheet("font-weight: bold; color: #28a745;")
        
        # Current quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(999999)
        
        # Minimum quantity
        self.min_quantity_input = QSpinBox()
        self.min_quantity_input.setMaximum(999999)
        self.min_quantity_input.setValue(5)  # Default minimum
        
        layout.addRow("سعر الشراء *:", self.cost_price_input)
        layout.addRow("سعر البيع *:", self.sale_price_input)
        layout.addRow("هامش الربح:", self.profit_margin_label)
        layout.addRow("الكمية الحالية:", self.quantity_input)
        layout.addRow("الحد الأدنى للكمية:", self.min_quantity_input)
        
        # Connect price change signals
        self.cost_price_input.valueChanged.connect(self.calculate_profit_margin)
        self.sale_price_input.valueChanged.connect(self.calculate_profit_margin)
        
        tab.setLayout(layout)
        return tab
        
    def create_additional_info_tab(self):
        """Create additional information tab"""
        tab = QGroupBox()
        layout = QFormLayout()
        
        # Supplier
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("لا يوجد مورد", None)
        
        # Unit of measure
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["قطعة", "كيلو", "متر", "لتر", "صندوق", "عبوة"])
        
        # Location
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("موقع المنتج في المخزن")
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setPlaceholderText("ملاحظات إضافية")
        
        layout.addRow("المورد:", self.supplier_combo)
        layout.addRow("وحدة القياس:", self.unit_combo)
        layout.addRow("الموقع:", self.location_input)
        layout.addRow("ملاحظات:", self.notes_input)
        
        tab.setLayout(layout)
        return tab
        
    def load_data(self):
        """Load categories and suppliers"""
        session = get_db_session()
        try:
            # Load categories
            categories = session.query(Category).all()
            self.categories = categories
            
            self.category_combo.clear()
            for category in categories:
                self.category_combo.addItem(category.name_ar, category.id)
                
            # Load suppliers
            suppliers = session.query(Supplier).all()
            self.suppliers = suppliers
            
            for supplier in suppliers:
                self.supplier_combo.addItem(supplier.name, supplier.id)
                
        finally:
            session.close()
            
    def load_product(self):
        """Load product data for editing"""
        session = get_db_session()
        try:
            product = session.query(Product).get(self.product_id)
            if not product:
                show_error(self, "المنتج غير موجود")
                self.reject()
                return
                
            self.product = product
            
            # Populate form fields
            self.sku_input.setText(product.sku)
            self.name_input.setText(product.name_ar)
            self.description_input.setPlainText(product.description_ar or "")
            self.barcode_input.setText(product.barcode or "")
            self.cost_price_input.setValue(product.cost_price)
            self.sale_price_input.setValue(product.sale_price)
            self.quantity_input.setValue(product.quantity)
            self.min_quantity_input.setValue(product.min_quantity)
            self.active_checkbox.setChecked(product.active == "active")
            
            # Set category
            if product.category_id:
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == product.category_id:
                        self.category_combo.setCurrentIndex(i)
                        break
                        
            # Set supplier
            if product.supplier_id:
                for i in range(self.supplier_combo.count()):
                    if self.supplier_combo.itemData(i) == product.supplier_id:
                        self.supplier_combo.setCurrentIndex(i)
                        break
                        
            # Calculate profit margin
            self.calculate_profit_margin()
            
        finally:
            session.close()
            
    def calculate_profit_margin(self):
        """Calculate and display profit margin"""
        cost_price = self.cost_price_input.value()
        sale_price = self.sale_price_input.value()
        
        if cost_price > 0:
            margin = ((sale_price - cost_price) / cost_price) * 100
            self.profit_margin_label.setText(f"{margin:.2f}%")
            
            # Color code the margin
            if margin > 20:
                self.profit_margin_label.setStyleSheet("font-weight: bold; color: #28a745;")
            elif margin > 10:
                self.profit_margin_label.setStyleSheet("font-weight: bold; color: #ffc107;")
            else:
                self.profit_margin_label.setStyleSheet("font-weight: bold; color: #dc3545;")
        else:
            self.profit_margin_label.setText("0.00%")
            self.profit_margin_label.setStyleSheet("font-weight: bold; color: #6c757d;")
            
    def validate_form(self):
        """Validate form data"""
        # Required fields
        if not self.sku_input.text().strip():
            show_error(self, "يرجى إدخال كود المنتج (SKU)")
            self.sku_input.setFocus()
            return False
            
        if not self.name_input.text().strip():
            show_error(self, "يرجى إدخال اسم المنتج")
            self.name_input.setFocus()
            return False
            
        if self.category_combo.currentData() is None:
            show_error(self, "يرجى اختيار فئة المنتج")
            self.category_combo.setFocus()
            return False
            
        # Validate SKU format
        sku = self.sku_input.text().strip()
        if not validate_sku(sku):
            show_error(self, "كود المنتج غير صالح. يجب أن يحتوي على أحرف وأرقام فقط")
            self.sku_input.setFocus()
            return False
            
        # Validate prices
        cost_price = self.cost_price_input.value()
        sale_price = self.sale_price_input.value()
        
        if not validate_price(cost_price):
            show_error(self, "سعر الشراء غير صالح")
            self.cost_price_input.setFocus()
            return False
            
        if not validate_price(sale_price):
            show_error(self, "سعر البيع غير صالح")
            self.sale_price_input.setFocus()
            return False
            
        if sale_price < cost_price:
            reply = QMessageBox.question(
                self, "تحذير",
                "سعر البيع أقل من سعر الشراء. هل تريد المتابعة؟"
            )
            if reply != QMessageBox.StandardButton.Yes:
                return False
                
        return True
        
    def save_product(self):
        """Save product data"""
        if not self.validate_form():
            return
            
        session = get_db_session()
        try:
            # Check for duplicate SKU
            sku = self.sku_input.text().strip()
            existing_product = session.query(Product).filter_by(sku=sku).first()
            
            if existing_product and existing_product.id != self.product_id:
                show_error(self, f"كود المنتج '{sku}' موجود مسبقاً")
                return
                
            if self.product_id:
                # Update existing product
                product = session.query(Product).get(self.product_id)
                if not product:
                    show_error(self, "المنتج غير موجود")
                    return
            else:
                # Create new product
                product = Product()
                
            # Update product data
            product.sku = sku
            product.name_ar = self.name_input.text().strip()
            product.description_ar = self.description_input.toPlainText().strip() or None
            product.category_id = self.category_combo.currentData()
            product.cost_price = self.cost_price_input.value()
            product.sale_price = self.sale_price_input.value()
            product.quantity = self.quantity_input.value()
            product.min_quantity = self.min_quantity_input.value()
            product.barcode = self.barcode_input.text().strip() or None
            product.supplier_id = self.supplier_combo.currentData()
            product.active = "active" if self.active_checkbox.isChecked() else "inactive"
            
            if not self.product_id:
                session.add(product)
                
            session.commit()
            
            # Log the action
            from models.audit import AuditLog
            action = "create" if not self.product_id else "update"
            AuditLog.log_action(
                session, self.current_user.id, action, "products",
                record_id=product.id,
                details=f"Product: {product.name_ar} ({product.sku})"
            )
            session.commit()
            
            self.accept()
            
        except Exception as e:
            session.rollback()
            logging.error(f"Product save error: {e}")
            show_error(self, f"فشل في حفظ المنتج:\n{str(e)}")
        finally:
            session.close()
            
    def save_and_new_product(self):
        """Save current product and create new one"""
        if self.save_product():
            # Clear form for new product
            self.sku_input.clear()
            self.name_input.clear()
            self.description_input.clear()
            self.barcode_input.clear()
            self.cost_price_input.setValue(0)
            self.sale_price_input.setValue(0)
            self.quantity_input.setValue(0)
            self.min_quantity_input.setValue(5)
            self.active_checkbox.setChecked(True)
            
            # Focus on SKU field
            self.sku_input.setFocus()
