# -*- coding: utf-8 -*-
"""
Inventory management window for Al-Hussiny Mobile Shop POS System
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox,
                            QDoubleSpinBox, QTextEdit, QTableWidget, QTableWidgetItem,
                            QHeaderView, QAbstractItemView, QMessageBox, QDialog,
                            QFormLayout, QDialogButtonBox, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import logging

from .base_window import BaseWindow
from .widgets.data_table import DataTableWidget
from .dialogs.product_dialog import ProductDialog

logger = logging.getLogger(__name__)

class InventoryWindow(BaseWindow):
    """Inventory management window"""
    
    def __init__(self, db_manager, user_data):
        super().__init__(db_manager, user_data)
        self.setup_inventory()
        self.refresh_data()
    
    def setup_inventory(self):
        """Setup inventory interface"""
        self.set_title("إدارة المخزون - محل الحسيني")
        self.setMinimumSize(1200, 800)
        
        # Main layout
        main_layout = QVBoxLayout(self.content_widget)
        
        # Toolbar
        self.setup_toolbar(main_layout)
        
        # Filters
        self.setup_filters(main_layout)
        
        # Products table
        self.setup_products_table(main_layout)
        
        # Statistics panel
        self.setup_statistics_panel(main_layout)
    
    def setup_toolbar(self, layout):
        """Setup toolbar with action buttons"""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_frame.setMaximumHeight(60)
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        
        # Add product button
        if self.has_permission("inventory"):
            self.add_product_btn = QPushButton("إضافة منتج جديد")
            self.add_product_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            self.add_product_btn.clicked.connect(self.add_product)
            toolbar_layout.addWidget(self.add_product_btn)
        
        # Edit product button
        if self.has_permission("inventory"):
            self.edit_product_btn = QPushButton("تعديل المنتج")
            self.edit_product_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            self.edit_product_btn.clicked.connect(self.edit_product)
            self.edit_product_btn.setEnabled(False)
            toolbar_layout.addWidget(self.edit_product_btn)
        
        # Delete product button
        if self.has_permission("inventory"):
            self.delete_product_btn = QPushButton("حذف المنتج")
            self.delete_product_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            self.delete_product_btn.clicked.connect(self.delete_product)
            self.delete_product_btn.setEnabled(False)
            toolbar_layout.addWidget(self.delete_product_btn)
        
        toolbar_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("تحديث")
        self.refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(toolbar_frame)
    
    def setup_filters(self, layout):
        """Setup filter controls"""
        filters_frame = QFrame()
        filters_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        filters_frame.setMaximumHeight(80)
        
        filters_layout = QHBoxLayout(filters_frame)
        
        # Search box
        search_label = QLabel("البحث:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("بحث بالاسم أو كود المنتج أو الباركود...")
        self.search_edit.textChanged.connect(self.filter_products)
        
        # Category filter
        category_label = QLabel("الفئة:")
        self.category_combo = QComboBox()
        self.category_combo.addItem("جميع الفئات", 0)
        self.category_combo.currentTextChanged.connect(self.filter_products)
        
        # Low stock filter
        self.low_stock_check = QCheckBox("المنتجات المنخفضة فقط")
        self.low_stock_check.stateChanged.connect(self.filter_products)
        
        filters_layout.addWidget(search_label)
        filters_layout.addWidget(self.search_edit)
        filters_layout.addWidget(category_label)
        filters_layout.addWidget(self.category_combo)
        filters_layout.addWidget(self.low_stock_check)
        filters_layout.addStretch()
        
        layout.addWidget(filters_frame)
    
    def setup_products_table(self, layout):
        """Setup products table"""
        self.products_table = DataTableWidget()
        self.products_table.setColumns([
            "كود المنتج", "اسم المنتج", "الفئة", "الكمية", 
            "الحد الأدنى", "سعر الشراء", "سعر البيع", "الربحية %", "الحالة"
        ])
        
        # Connect selection signal
        self.products_table.itemSelectionChanged.connect(self.on_product_selection_changed)
        self.products_table.itemDoubleClicked.connect(self.edit_product)
        
        layout.addWidget(self.products_table)
    
    def setup_statistics_panel(self, layout):
        """Setup statistics panel"""
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        stats_frame.setMaximumHeight(80)
        
        stats_layout = QHBoxLayout(stats_frame)
        
        # Statistics labels
        self.total_products_label = QLabel("إجمالي المنتجات: 0")
        self.low_stock_label = QLabel("منتجات منخفضة: 0")
        self.total_value_label = QLabel("قيمة المخزون: 0 ج.م")
        self.out_of_stock_label = QLabel("منتجات نفدت: 0")
        
        stats_layout.addWidget(self.total_products_label)
        stats_layout.addWidget(self.low_stock_label)
        stats_layout.addWidget(self.total_value_label)
        stats_layout.addWidget(self.out_of_stock_label)
        stats_layout.addStretch()
        
        layout.addWidget(stats_frame)
    
    def refresh_data(self):
        """Refresh inventory data"""
        try:
            session = self.db_manager.get_session()
            
            # Load categories
            self.load_categories(session)
            
            # Load products
            self.load_products(session)
            
            # Update statistics
            self.update_statistics(session)
            
            self.update_status("تم تحديث بيانات المخزون")
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث بيانات المخزون: {e}")
            self.show_message(f"خطأ في تحديث البيانات: {str(e)}", "error")
        finally:
            if 'session' in locals():
                session.close()
    
    def load_categories(self, session):
        """Load categories into combo box"""
        from models import Category
        
        # Clear existing items (except "all categories")
        while self.category_combo.count() > 1:
            self.category_combo.removeItem(1)
        
        # Load categories
        categories = session.query(Category).order_by(Category.name_ar).all()
        for category in categories:
            self.category_combo.addItem(category.name_ar, category.id)
    
    def load_products(self, session):
        """Load products into table"""
        from models import Product
        
        # Get filter values
        search_text = self.search_edit.text().strip()
        category_id = self.category_combo.currentData()
        low_stock_only = self.low_stock_check.isChecked()
        
        # Build query
        query = session.query(Product).filter_by(active=True)
        
        if search_text:
            query = query.filter(
                (Product.name_ar.contains(search_text)) |
                (Product.sku.contains(search_text)) |
                (Product.barcode.contains(search_text))
            )
        
        if category_id and category_id > 0:
            query = query.filter_by(category_id=category_id)
        
        if low_stock_only:
            query = query.filter(Product.quantity <= Product.min_quantity)
        
        # Get products
        products = query.order_by(Product.name_ar).all()
        
        # Populate table
        data = []
        for product in products:
            profit_margin = f"{product.profit_margin:.1f}%" if product.profit_margin else "0%"
            
            # Determine status
            if product.quantity == 0:
                status = "نفد"
            elif product.is_low_stock:
                status = "منخفض"
            else:
                status = "متوفر"
            
            data.append([
                product.sku,
                product.name_ar,
                product.category.name_ar if product.category else "",
                str(product.quantity),
                str(product.min_quantity),
                f"{product.cost_price:.2f}",
                f"{product.sale_price:.2f}",
                profit_margin,
                status
            ])
        
        self.products_table.setData(data)
        
        # Store products for reference
        self.current_products = products
    
    def update_statistics(self, session):
        """Update statistics panel"""
        from models import Product
        
        # Get all active products
        products = session.query(Product).filter_by(active=True).all()
        
        total_products = len(products)
        low_stock_count = sum(1 for p in products if p.is_low_stock)
        out_of_stock_count = sum(1 for p in products if p.quantity == 0)
        total_value = sum(p.quantity * p.sale_price for p in products)
        
        # Update labels
        self.total_products_label.setText(f"إجمالي المنتجات: {total_products}")
        self.low_stock_label.setText(f"منتجات منخفضة: {low_stock_count}")
        self.total_value_label.setText(f"قيمة المخزون: {total_value:.2f} ج.م")
        self.out_of_stock_label.setText(f"منتجات نفدت: {out_of_stock_count}")
    
    def filter_products(self):
        """Filter products based on current filter settings"""
        self.refresh_data()
    
    def on_product_selection_changed(self):
        """Handle product selection change"""
        selected_rows = self.products_table.get_selected_rows()
        has_selection = len(selected_rows) > 0
        
        if self.has_permission("inventory"):
            self.edit_product_btn.setEnabled(has_selection)
            self.delete_product_btn.setEnabled(has_selection)
    
    def add_product(self):
        """Add new product"""
        if not self.require_permission("inventory", "إضافة منتج جديد"):
            return
        
        dialog = ProductDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.log_action("add_product", "إضافة منتج جديد")
    
    def edit_product(self):
        """Edit selected product"""
        if not self.require_permission("inventory", "تعديل المنتج"):
            return
        
        selected_rows = self.products_table.get_selected_rows()
        if not selected_rows:
            self.show_message("يرجى اختيار منتج للتعديل", "warning")
            return
        
        # Get selected product
        row_index = selected_rows[0]
        if hasattr(self, 'current_products') and row_index < len(self.current_products):
            product = self.current_products[row_index]
            
            dialog = ProductDialog(self.db_manager, product, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh_data()
                self.log_action("edit_product", f"تعديل المنتج: {product.name_ar}")
    
    def delete_product(self):
        """Delete selected product"""
        if not self.require_permission("inventory", "حذف المنتج"):
            return
        
        selected_rows = self.products_table.get_selected_rows()
        if not selected_rows:
            self.show_message("يرجى اختيار منتج للحذف", "warning")
            return
        
        # Get selected product
        row_index = selected_rows[0]
        if hasattr(self, 'current_products') and row_index < len(self.current_products):
            product = self.current_products[row_index]
            
            if self.show_question(f"هل تريد حذف المنتج '{product.name_ar}'؟"):
                try:
                    session = self.db_manager.get_session()
                    
                    # Soft delete
                    product_obj = session.query(type(product)).get(product.id)
                    product_obj.active = False
                    session.commit()
                    
                    self.refresh_data()
                    self.log_action("delete_product", f"حذف المنتج: {product.name_ar}")
                    self.show_message("تم حذف المنتج بنجاح", "success")
                    
                except Exception as e:
                    session.rollback()
                    self.logger.error(f"خطأ في حذف المنتج: {e}")
                    self.show_message(f"خطأ في حذف المنتج: {str(e)}", "error")
                finally:
                    session.close()
