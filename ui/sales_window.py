from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                            QFormLayout, QDialog, QMessageBox, QGroupBox,
                            QHeaderView, QAbstractItemView, QTextEdit, QSplitter)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from datetime import datetime

from services.sales_service import SalesService
from services.inventory_service import InventoryService
from ui.styles import get_stylesheet
from utils.pdf_generator import PDFGenerator

class SalesWindow(QMainWindow):
    """Sales and invoicing window"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.sales_service = SalesService()
        self.inventory_service = InventoryService()
        self.pdf_generator = PDFGenerator()
        
        self.cart_items = []
        self.current_customer = None
        
        self.setup_ui()
        self.apply_styles()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("نظام المبيعات والفواتير")
        self.setMinimumSize(1400, 800)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create splitter for two-panel layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Product selection
        left_panel = self.create_product_panel()
        
        # Right panel - Cart and checkout
        right_panel = self.create_cart_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([800, 600])
        
        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
    
    def create_product_panel(self):
        """Create product selection panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("اختيار المنتجات")
        title_label.setFont(QFont("Noto Sans Arabic", 16, QFont.Weight.Bold))
        title_label.setObjectName("title-label")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Search section
        search_group = QGroupBox("البحث في المنتجات")
        search_layout = QHBoxLayout()
        
        search_label = QLabel("بحث:")
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("ابحث بالاسم أو الكود أو الباركود...")
        self.product_search.textChanged.connect(self.filter_products)
        
        category_label = QLabel("الفئة:")
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self.filter_products)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.product_search)
        search_layout.addWidget(category_label)
        search_layout.addWidget(self.category_filter)
        
        search_group.setLayout(search_layout)
        
        # Products table
        self.products_table = QTableWidget()
        self.setup_products_table()
        
        # Add to cart button
        self.add_to_cart_btn = QPushButton("إضافة للسلة")
        self.add_to_cart_btn.clicked.connect(self.add_to_cart)
        self.add_to_cart_btn.setEnabled(False)
        
        layout.addLayout(header_layout)
        layout.addWidget(search_group)
        layout.addWidget(self.products_table)
        layout.addWidget(self.add_to_cart_btn)
        
        panel.setLayout(layout)
        
        # Connect table selection
        self.products_table.selectionModel().selectionChanged.connect(self.on_product_selection)
        
        return panel
    
    def create_cart_panel(self):
        """Create shopping cart panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("سلة المشتريات والدفع")
        title_label.setFont(QFont("Noto Sans Arabic", 16, QFont.Weight.Bold))
        title_label.setObjectName("title-label")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Customer selection
        customer_group = QGroupBox("بيانات العميل")
        customer_layout = QHBoxLayout()
        
        customer_label = QLabel("العميل:")
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(200)
        
        add_customer_btn = QPushButton("عميل جديد")
        add_customer_btn.clicked.connect(self.add_new_customer)
        
        customer_layout.addWidget(customer_label)
        customer_layout.addWidget(self.customer_combo)
        customer_layout.addWidget(add_customer_btn)
        customer_layout.addStretch()
        
        customer_group.setLayout(customer_layout)
        
        # Cart items table
        cart_label = QLabel("عناصر الفاتورة:")
        cart_label.setFont(QFont("Noto Sans Arabic", 12, QFont.Weight.Bold))
        
        self.cart_table = QTableWidget()
        self.setup_cart_table()
        
        # Cart actions
        cart_actions = QHBoxLayout()
        self.remove_item_btn = QPushButton("إزالة العنصر")
        self.remove_item_btn.clicked.connect(self.remove_from_cart)
        self.remove_item_btn.setEnabled(False)
        
        self.clear_cart_btn = QPushButton("مسح السلة")
        self.clear_cart_btn.clicked.connect(self.clear_cart)
        
        cart_actions.addWidget(self.remove_item_btn)
        cart_actions.addWidget(self.clear_cart_btn)
        cart_actions.addStretch()
        
        # Invoice totals
        totals_group = QGroupBox("إجمالي الفاتورة")
        totals_layout = QFormLayout()
        
        self.subtotal_label = QLabel("0.00 جنيه")
        self.tax_input = QDoubleSpinBox()
        self.tax_input.setDecimals(2)
        self.tax_input.setMaximum(99.99)
        self.tax_input.setValue(14.0)
        self.tax_input.valueChanged.connect(self.calculate_totals)
        
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setDecimals(2)
        self.discount_input.setMaximum(999999.99)
        self.discount_input.valueChanged.connect(self.calculate_totals)
        
        self.total_label = QLabel("0.00 جنيه")
        self.total_label.setFont(QFont("Noto Sans Arabic", 14, QFont.Weight.Bold))
        
        self.paid_input = QDoubleSpinBox()
        self.paid_input.setDecimals(2)
        self.paid_input.setMaximum(999999.99)
        self.paid_input.valueChanged.connect(self.calculate_change)
        
        self.change_label = QLabel("0.00 جنيه")
        
        totals_layout.addRow("المجموع الفرعي:", self.subtotal_label)
        totals_layout.addRow("الضريبة (%):", self.tax_input)
        totals_layout.addRow("الخصم:", self.discount_input)
        totals_layout.addRow("الإجمالي:", self.total_label)
        totals_layout.addRow("المدفوع:", self.paid_input)
        totals_layout.addRow("الباقي:", self.change_label)
        
        totals_group.setLayout(totals_layout)
        
        # Payment and actions
        payment_actions = QHBoxLayout()
        
        self.save_invoice_btn = QPushButton("حفظ الفاتورة")
        self.save_invoice_btn.clicked.connect(self.save_invoice)
        self.save_invoice_btn.setEnabled(False)
        
        self.print_invoice_btn = QPushButton("طباعة")
        self.print_invoice_btn.clicked.connect(self.print_invoice)
        self.print_invoice_btn.setEnabled(False)
        
        self.new_sale_btn = QPushButton("فاتورة جديدة")
        self.new_sale_btn.clicked.connect(self.new_sale)
        
        payment_actions.addWidget(self.save_invoice_btn)
        payment_actions.addWidget(self.print_invoice_btn)
        payment_actions.addWidget(self.new_sale_btn)
        
        # Add all to layout
        layout.addLayout(header_layout)
        layout.addWidget(customer_group)
        layout.addWidget(cart_label)
        layout.addWidget(self.cart_table)
        layout.addLayout(cart_actions)
        layout.addWidget(totals_group)
        layout.addLayout(payment_actions)
        
        panel.setLayout(layout)
        
        # Connect cart table selection
        self.cart_table.selectionModel().selectionChanged.connect(self.on_cart_selection)
        
        return panel
    
    def setup_products_table(self):
        """Setup products table"""
        headers = ["الكود", "اسم المنتج", "الفئة", "السعر", "المتاح"]
        
        self.products_table.setColumnCount(len(headers))
        self.products_table.setHorizontalHeaderLabels(headers)
        
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_table.setAlternatingRowColors(True)
        
        # Resize columns
        header = self.products_table.horizontalHeader()
        header.setStretchLastSection(True)
    
    def setup_cart_table(self):
        """Setup cart table"""
        headers = ["المنتج", "الكمية", "سعر الوحدة", "الإجمالي"]
        
        self.cart_table.setColumnCount(len(headers))
        self.cart_table.setHorizontalHeaderLabels(headers)
        
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Resize columns
        header = self.cart_table.horizontalHeader()
        header.setStretchLastSection(True)
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(get_stylesheet("light"))
    
    def load_data(self):
        """Load products and customers data"""
        try:
            # Load categories
            categories = self.inventory_service.get_categories()
            self.category_filter.clear()
            self.category_filter.addItem("الكل")
            for category in categories:
                self.category_filter.addItem(category.name_ar)
            
            # Load products
            self.load_products()
            
            # Load customers
            self.load_customers()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {str(e)}")
    
    def load_products(self):
        """Load products into table"""
        try:
            products = self.inventory_service.get_products()
            
            # Filter only available products
            available_products = [p for p in products if p.quantity > 0]
            
            self.products_table.setRowCount(len(available_products))
            
            for row, product in enumerate(available_products):
                items = [
                    product.sku,
                    product.name_ar,
                    product.category.name_ar if product.category else "",
                    f"{product.sale_price:.2f}",
                    str(product.quantity)
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    item.setData(Qt.ItemDataRole.UserRole, product.id)
                    self.products_table.setItem(row, col, item)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل المنتجات: {str(e)}")
    
    def load_customers(self):
        """Load customers into combo box"""
        try:
            customers = self.sales_service.get_customers()
            self.customer_combo.clear()
            self.customer_combo.addItem("عميل نقدي", None)
            
            for customer in customers:
                self.customer_combo.addItem(customer.name, customer.id)
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل العملاء: {str(e)}")
    
    def filter_products(self):
        """Filter products based on search criteria"""
        search_text = self.product_search.text().lower()
        category = self.category_filter.currentText()
        
        for row in range(self.products_table.rowCount()):
            show_row = True
            
            if search_text:
                product_name = self.products_table.item(row, 1).text().lower()
                product_sku = self.products_table.item(row, 0).text().lower()
                if search_text not in product_name and search_text not in product_sku:
                    show_row = False
            
            if category != "الكل" and show_row:
                product_category = self.products_table.item(row, 2).text()
                if category != product_category:
                    show_row = False
            
            self.products_table.setRowHidden(row, not show_row)
    
    def on_product_selection(self):
        """Handle product table selection"""
        selected_rows = self.products_table.selectionModel().selectedRows()
        self.add_to_cart_btn.setEnabled(len(selected_rows) > 0)
    
    def on_cart_selection(self):
        """Handle cart table selection"""
        selected_rows = self.cart_table.selectionModel().selectedRows()
        self.remove_item_btn.setEnabled(len(selected_rows) > 0)
    
    def add_to_cart(self):
        """Add selected product to cart"""
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        product_id = self.products_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        # Get product details
        product = self.inventory_service.get_product_by_id(product_id)
        if not product:
            return
        
        # Show quantity dialog
        dialog = QuantityDialog(self, product)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            quantity = dialog.get_quantity()
            
            # Check if item already in cart
            existing_item = None
            for item in self.cart_items:
                if item['product_id'] == product_id:
                    existing_item = item
                    break
            
            if existing_item:
                # Update quantity
                new_quantity = existing_item['quantity'] + quantity
                if new_quantity > product.quantity:
                    QMessageBox.warning(self, "تحذير", "الكمية المطلوبة أكبر من المتاح")
                    return
                existing_item['quantity'] = new_quantity
                existing_item['line_total'] = existing_item['quantity'] * existing_item['unit_price']
            else:
                # Add new item
                cart_item = {
                    'product_id': product_id,
                    'product_name': product.name_ar,
                    'quantity': quantity,
                    'unit_price': product.sale_price,
                    'line_total': quantity * product.sale_price
                }
                self.cart_items.append(cart_item)
            
            self.update_cart_display()
            self.calculate_totals()
    
    def remove_from_cart(self):
        """Remove selected item from cart"""
        selected_rows = self.cart_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if 0 <= row < len(self.cart_items):
            del self.cart_items[row]
            self.update_cart_display()
            self.calculate_totals()
    
    def clear_cart(self):
        """Clear all items from cart"""
        if self.cart_items:
            reply = QMessageBox.question(
                self, 'تأكيد', 'هل أنت متأكد من مسح جميع عناصر السلة؟',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.cart_items.clear()
                self.update_cart_display()
                self.calculate_totals()
    
    def update_cart_display(self):
        """Update cart table display"""
        self.cart_table.setRowCount(len(self.cart_items))
        
        for row, item in enumerate(self.cart_items):
            items = [
                item['product_name'],
                str(item['quantity']),
                f"{item['unit_price']:.2f}",
                f"{item['line_total']:.2f}"
            ]
            
            for col, item_text in enumerate(items):
                table_item = QTableWidgetItem(str(item_text))
                self.cart_table.setItem(row, col, table_item)
        
        # Enable/disable save button
        self.save_invoice_btn.setEnabled(len(self.cart_items) > 0)
    
    def calculate_totals(self):
        """Calculate invoice totals"""
        if not self.cart_items:
            self.subtotal_label.setText("0.00 جنيه")
            self.total_label.setText("0.00 جنيه")
            return
        
        subtotal = sum(item['line_total'] for item in self.cart_items)
        tax_rate = self.tax_input.value() / 100
        discount = self.discount_input.value()
        
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount - discount
        
        self.subtotal_label.setText(f"{subtotal:.2f} جنيه")
        self.total_label.setText(f"{total:.2f} جنيه")
        
        self.calculate_change()
    
    def calculate_change(self):
        """Calculate change amount"""
        total_text = self.total_label.text().replace(" جنيه", "")
        try:
            total = float(total_text)
            paid = self.paid_input.value()
            change = paid - total
            self.change_label.setText(f"{change:.2f} جنيه")
        except:
            self.change_label.setText("0.00 جنيه")
    
    def add_new_customer(self):
        """Add new customer"""
        dialog = CustomerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_customers()
    
    def save_invoice(self):
        """Save the invoice"""
        try:
            if not self.cart_items:
                QMessageBox.warning(self, "تحذير", "لا توجد عناصر في الفاتورة")
                return
            
            # Prepare sale data
            subtotal = sum(item['line_total'] for item in self.cart_items)
            tax_rate = self.tax_input.value() / 100
            discount = self.discount_input.value()
            tax_amount = subtotal * tax_rate
            total = subtotal + tax_amount - discount
            paid = self.paid_input.value()
            
            if paid < total:
                QMessageBox.warning(self, "تحذير", "المبلغ المدفوع أقل من الإجمالي")
                return
            
            sale_data = {
                'customer_id': self.customer_combo.currentData(),
                'subtotal': subtotal,
                'tax': tax_amount,
                'discount': discount,
                'total': total,
                'paid': paid,
                'change': paid - total,
                'items': self.cart_items
            }
            
            # Create sale
            sale = self.sales_service.create_sale(sale_data, self.current_user.id)
            
            QMessageBox.information(self, "نجح", f"تم حفظ الفاتورة رقم: {sale.invoice_no}")
            
            # Enable print button
            self.current_sale = sale
            self.print_invoice_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حفظ الفاتورة: {str(e)}")
    
    def print_invoice(self):
        """Print the invoice"""
        if hasattr(self, 'current_sale') and self.current_sale:
            try:
                pdf_file = self.pdf_generator.generate_invoice_pdf(self.current_sale)
                QMessageBox.information(self, "نجح", f"تم إنشاء ملف PDF: {pdf_file}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في طباعة الفاتورة: {str(e)}")
    
    def new_sale(self):
        """Start new sale"""
        if self.cart_items:
            reply = QMessageBox.question(
                self, 'فاتورة جديدة', 
                'هل تريد إنشاء فاتورة جديدة؟ سيتم مسح البيانات الحالية.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Reset all fields
        self.cart_items.clear()
        self.update_cart_display()
        self.customer_combo.setCurrentIndex(0)
        self.tax_input.setValue(14.0)
        self.discount_input.setValue(0)
        self.paid_input.setValue(0)
        self.calculate_totals()
        
        self.save_invoice_btn.setEnabled(False)
        self.print_invoice_btn.setEnabled(False)
        
        if hasattr(self, 'current_sale'):
            delattr(self, 'current_sale')

class QuantityDialog(QDialog):
    """Dialog for entering item quantity"""
    
    def __init__(self, parent, product):
        super().__init__(parent)
        self.product = product
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("تحديد الكمية")
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout()
        
        # Product info
        info_label = QLabel(f"المنتج: {self.product.name_ar}\nالمتاح: {self.product.quantity}")
        info_label.setFont(QFont("Noto Sans Arabic", 11, QFont.Weight.Bold))
        
        # Quantity input
        form_layout = QFormLayout()
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(self.product.quantity)
        self.quantity_input.setValue(1)
        
        form_layout.addRow("الكمية:", self.quantity_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("موافق")
        ok_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("إلغاء")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addWidget(info_label)
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_quantity(self):
        """Get selected quantity"""
        return self.quantity_input.value()

class CustomerDialog(QDialog):
    """Dialog for adding new customer"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.sales_service = SalesService()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("إضافة عميل جديد")
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Form
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QTextEdit()
        self.notes_input = QTextEdit()
        
        form_layout.addRow("الاسم:", self.name_input)
        form_layout.addRow("رقم الهاتف:", self.phone_input)
        form_layout.addRow("العنوان:", self.address_input)
        form_layout.addRow("ملاحظات:", self.notes_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("حفظ")
        save_button.clicked.connect(self.save_customer)
        
        cancel_button = QPushButton("إلغاء")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def save_customer(self):
        """Save customer data"""
        try:
            if not self.name_input.text().strip():
                QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم العميل")
                return
            
            customer_data = {
                'name': self.name_input.text().strip(),
                'phone': self.phone_input.text().strip() or None,
                'address': self.address_input.toPlainText().strip() or None,
                'notes': self.notes_input.toPlainText().strip() or None
            }
            
            self.sales_service.create_customer(customer_data)
            QMessageBox.information(self, "نجح", "تم إضافة العميل بنجاح")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حفظ العميل: {str(e)}")
