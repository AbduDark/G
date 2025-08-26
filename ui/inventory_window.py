from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                            QFormLayout, QDialog, QMessageBox, QGroupBox,
                            QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from services.inventory_service import InventoryService
from ui.styles import get_stylesheet

class InventoryWindow(QMainWindow):
    """Inventory management window"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.inventory_service = InventoryService()
        self.current_product = None
        
        self.setup_ui()
        self.apply_styles()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("إدارة المخزون")
        self.setMinimumSize(1000, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("إدارة المخزون")
        title_label.setFont(QFont("Noto Sans Arabic", 18, QFont.Weight.Bold))
        title_label.setObjectName("title-label")
        
        # Add product button
        self.add_button = QPushButton("إضافة منتج جديد")
        self.add_button.clicked.connect(self.add_product)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_button)
        
        # Search and filter section
        filter_group = QGroupBox("البحث والفلترة")
        filter_layout = QHBoxLayout()
        
        # Search box
        search_label = QLabel("بحث:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بالاسم، الكود، أو الباركود...")
        self.search_input.textChanged.connect(self.filter_products)
        
        # Category filter
        category_label = QLabel("الفئة:")
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self.filter_products)
        
        # Stock status filter
        stock_label = QLabel("حالة المخزون:")
        self.stock_filter = QComboBox()
        self.stock_filter.addItems(["الكل", "متوفر", "منخفض", "نفد"])
        self.stock_filter.currentTextChanged.connect(self.filter_products)
        
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(category_label)
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(stock_label)
        filter_layout.addWidget(self.stock_filter)
        filter_layout.addStretch()
        
        filter_group.setLayout(filter_layout)
        
        # Products table
        self.products_table = QTableWidget()
        self.setup_products_table()
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.edit_button = QPushButton("تعديل")
        self.edit_button.clicked.connect(self.edit_product)
        self.edit_button.setEnabled(False)
        
        self.delete_button = QPushButton("حذف")
        self.delete_button.clicked.connect(self.delete_product)
        self.delete_button.setEnabled(False)
        
        self.stock_button = QPushButton("حركة مخزون")
        self.stock_button.clicked.connect(self.stock_movement)
        self.stock_button.setEnabled(False)
        
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.stock_button)
        buttons_layout.addStretch()
        
        # Add layouts to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(filter_group)
        main_layout.addWidget(self.products_table)
        main_layout.addLayout(buttons_layout)
        
        central_widget.setLayout(main_layout)
        
        # Connect table selection
        self.products_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def setup_products_table(self):
        """Setup products table"""
        headers = ["الكود", "اسم المنتج", "الفئة", "سعر الشراء", "سعر البيع", 
                  "الكمية", "الحد الأدنى", "المزود", "حالة المخزون"]
        
        self.products_table.setColumnCount(len(headers))
        self.products_table.setHorizontalHeaderLabels(headers)
        
        # Set table properties
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSortingEnabled(True)
        
        # Resize columns
        header = self.products_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(get_stylesheet("light"))
    
    def load_data(self):
        """Load products and categories data"""
        try:
            # Load categories for filter
            categories = self.inventory_service.get_categories()
            self.category_filter.clear()
            self.category_filter.addItem("الكل")
            for category in categories:
                self.category_filter.addItem(category.name_ar)
            
            # Load products
            self.load_products()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {str(e)}")
    
    def load_products(self):
        """Load products into table"""
        try:
            products = self.inventory_service.get_products()
            
            self.products_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                # Determine stock status
                if product.quantity <= 0:
                    stock_status = "نفد"
                elif product.quantity <= product.min_quantity:
                    stock_status = "منخفض"
                else:
                    stock_status = "متوفر"
                
                # Populate table cells
                items = [
                    product.sku,
                    product.name_ar,
                    product.category.name_ar if product.category else "",
                    f"{product.cost_price:.2f}",
                    f"{product.sale_price:.2f}",
                    str(product.quantity),
                    str(product.min_quantity),
                    product.supplier.name if product.supplier else "",
                    stock_status
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    item.setData(Qt.ItemDataRole.UserRole, product.id)
                    
                    # Color coding for stock status
                    if col == 8:  # Stock status column
                        if stock_status == "نفد":
                            item.setBackground(Qt.GlobalColor.red)
                        elif stock_status == "منخفض":
                            item.setBackground(Qt.GlobalColor.yellow)
                    
                    self.products_table.setItem(row, col, item)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل المنتجات: {str(e)}")
    
    def filter_products(self):
        """Filter products based on search criteria"""
        search_text = self.search_input.text().lower()
        category = self.category_filter.currentText()
        stock_status = self.stock_filter.currentText()
        
        for row in range(self.products_table.rowCount()):
            show_row = True
            
            # Search filter
            if search_text:
                product_name = self.products_table.item(row, 1).text().lower()
                product_sku = self.products_table.item(row, 0).text().lower()
                if search_text not in product_name and search_text not in product_sku:
                    show_row = False
            
            # Category filter
            if category != "الكل" and show_row:
                product_category = self.products_table.item(row, 2).text()
                if category != product_category:
                    show_row = False
            
            # Stock status filter
            if stock_status != "الكل" and show_row:
                product_stock_status = self.products_table.item(row, 8).text()
                if stock_status != product_stock_status:
                    show_row = False
            
            self.products_table.setRowHidden(row, not show_row)
    
    def on_selection_changed(self):
        """Handle table selection change"""
        selected_rows = self.products_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.stock_button.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            product_id = self.products_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.current_product = self.inventory_service.get_product_by_id(product_id)
    
    def add_product(self):
        """Open dialog to add new product"""
        dialog = ProductDialog(self, self.inventory_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_products()
    
    def edit_product(self):
        """Open dialog to edit selected product"""
        if self.current_product:
            dialog = ProductDialog(self, self.inventory_service, self.current_product)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_products()
    
    def delete_product(self):
        """Delete selected product"""
        if not self.current_product:
            return
        
        reply = QMessageBox.question(
            self,
            'تأكيد الحذف',
            f'هل أنت متأكد من حذف المنتج "{self.current_product.name_ar}"؟',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.inventory_service.delete_product(self.current_product.id)
                QMessageBox.information(self, "نجح", "تم حذف المنتج بنجاح")
                self.load_products()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في حذف المنتج: {str(e)}")
    
    def stock_movement(self):
        """Open stock movement dialog"""
        if self.current_product:
            dialog = StockMovementDialog(self, self.inventory_service, self.current_product, self.current_user)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_products()

class ProductDialog(QDialog):
    """Dialog for adding/editing products"""
    
    def __init__(self, parent, inventory_service, product=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.product = product
        self.is_edit_mode = product is not None
        
        self.setup_ui()
        if self.is_edit_mode:
            self.load_product_data()
    
    def setup_ui(self):
        """Setup dialog UI"""
        title = "تعديل منتج" if self.is_edit_mode else "إضافة منتج جديد"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(500, 600)
        
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Product fields
        self.sku_input = QLineEdit()
        self.name_input = QLineEdit()
        self.description_input = QLineEdit()
        
        self.category_combo = QComboBox()
        self.supplier_combo = QComboBox()
        
        self.cost_price_input = QDoubleSpinBox()
        self.cost_price_input.setMaximum(999999.99)
        self.cost_price_input.setDecimals(2)
        
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setMaximum(999999.99)
        self.sale_price_input.setDecimals(2)
        
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(999999)
        
        self.min_quantity_input = QSpinBox()
        self.min_quantity_input.setMaximum(999999)
        self.min_quantity_input.setValue(5)
        
        self.barcode_input = QLineEdit()
        
        # Add fields to form
        form_layout.addRow("كود المنتج (SKU):", self.sku_input)
        form_layout.addRow("اسم المنتج:", self.name_input)
        form_layout.addRow("الوصف:", self.description_input)
        form_layout.addRow("الفئة:", self.category_combo)
        form_layout.addRow("المزود:", self.supplier_combo)
        form_layout.addRow("سعر الشراء:", self.cost_price_input)
        form_layout.addRow("سعر البيع:", self.sale_price_input)
        form_layout.addRow("الكمية:", self.quantity_input)
        form_layout.addRow("الحد الأدنى:", self.min_quantity_input)
        form_layout.addRow("الباركود:", self.barcode_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("حفظ")
        self.save_button.clicked.connect(self.save_product)
        
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Load categories and suppliers
        self.load_combos()
    
    def load_combos(self):
        """Load categories and suppliers into combo boxes"""
        try:
            # Load categories
            categories = self.inventory_service.get_categories()
            self.category_combo.clear()
            self.category_combo.addItem("اختر الفئة", None)
            for category in categories:
                self.category_combo.addItem(category.name_ar, category.id)
            
            # Load suppliers
            suppliers = self.inventory_service.get_suppliers()
            self.supplier_combo.clear()
            self.supplier_combo.addItem("اختر المزود", None)
            for supplier in suppliers:
                self.supplier_combo.addItem(supplier.name, supplier.id)
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {str(e)}")
    
    def load_product_data(self):
        """Load existing product data for editing"""
        if not self.product:
            return
        
        self.sku_input.setText(self.product.sku)
        self.name_input.setText(self.product.name_ar)
        self.description_input.setText(self.product.description_ar or "")
        self.cost_price_input.setValue(self.product.cost_price)
        self.sale_price_input.setValue(self.product.sale_price)
        self.quantity_input.setValue(self.product.quantity)
        self.min_quantity_input.setValue(self.product.min_quantity)
        self.barcode_input.setText(self.product.barcode or "")
        
        # Set category
        if self.product.category_id:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == self.product.category_id:
                    self.category_combo.setCurrentIndex(i)
                    break
        
        # Set supplier
        if self.product.supplier_id:
            for i in range(self.supplier_combo.count()):
                if self.supplier_combo.itemData(i) == self.product.supplier_id:
                    self.supplier_combo.setCurrentIndex(i)
                    break
    
    def save_product(self):
        """Save product data"""
        try:
            # Validate required fields
            if not self.sku_input.text().strip():
                QMessageBox.warning(self, "تحذير", "يرجى إدخال كود المنتج")
                return
            
            if not self.name_input.text().strip():
                QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم المنتج")
                return
            
            if self.sale_price_input.value() <= 0:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال سعر بيع صحيح")
                return
            
            # Prepare product data
            product_data = {
                'sku': self.sku_input.text().strip(),
                'name_ar': self.name_input.text().strip(),
                'description_ar': self.description_input.text().strip(),
                'category_id': self.category_combo.currentData(),
                'supplier_id': self.supplier_combo.currentData(),
                'cost_price': self.cost_price_input.value(),
                'sale_price': self.sale_price_input.value(),
                'quantity': self.quantity_input.value(),
                'min_quantity': self.min_quantity_input.value(),
                'barcode': self.barcode_input.text().strip() or None
            }
            
            # Save product
            if self.is_edit_mode:
                self.inventory_service.update_product(self.product.id, product_data)
                QMessageBox.information(self, "نجح", "تم تحديث المنتج بنجاح")
            else:
                self.inventory_service.create_product(product_data)
                QMessageBox.information(self, "نجح", "تم إضافة المنتج بنجاح")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حفظ المنتج: {str(e)}")

class StockMovementDialog(QDialog):
    """Dialog for stock movements"""
    
    def __init__(self, parent, inventory_service, product, current_user):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.product = product
        self.current_user = current_user
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"حركة مخزون - {self.product.name_ar}")
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Product info
        info_label = QLabel(f"المنتج: {self.product.name_ar}\nالكمية الحالية: {self.product.quantity}")
        info_label.setFont(QFont("Noto Sans Arabic", 11, QFont.Weight.Bold))
        
        # Form
        form_layout = QFormLayout()
        
        self.movement_type = QComboBox()
        self.movement_type.addItems(["شراء", "بيع", "تعديل", "تحويل", "مرتجع"])
        
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(-999999)
        self.quantity_input.setMaximum(999999)
        
        self.reference_input = QLineEdit()
        self.note_input = QLineEdit()
        
        form_layout.addRow("نوع الحركة:", self.movement_type)
        form_layout.addRow("الكمية:", self.quantity_input)
        form_layout.addRow("المرجع:", self.reference_input)
        form_layout.addRow("ملاحظة:", self.note_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("حفظ")
        save_button.clicked.connect(self.save_movement)
        
        cancel_button = QPushButton("إلغاء")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addWidget(info_label)
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def save_movement(self):
        """Save stock movement"""
        try:
            if self.quantity_input.value() == 0:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال كمية صحيحة")
                return
            
            movement_data = {
                'product_id': self.product.id,
                'change_qty': self.quantity_input.value(),
                'movement_type': self.movement_type.currentText(),
                'reference_id': self.reference_input.text().strip() or None,
                'note': self.note_input.text().strip() or None,
                'user_id': self.current_user.id
            }
            
            self.inventory_service.create_stock_movement(movement_data)
            QMessageBox.information(self, "نجح", "تم تسجيل حركة المخزون بنجاح")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تسجيل الحركة: {str(e)}")
