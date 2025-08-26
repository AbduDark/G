# -*- coding: utf-8 -*-
"""
Sales management window for Al-Hussiny Mobile Shop POS System
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox,
                            QDoubleSpinBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QAbstractItemView, QMessageBox, QDialog,
                            QFormLayout, QDialogButtonBox, QFrame, QTextEdit,
                            QDateEdit, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
import logging
from datetime import datetime

from .base_window import BaseWindow
from .widgets.data_table import DataTableWidget
from .dialogs.sale_dialog import SaleDialog

logger = logging.getLogger(__name__)

class SalesWindow(BaseWindow):
    """Sales management window"""
    
    def __init__(self, db_manager, user_data):
        super().__init__(db_manager, user_data)
        self.setup_sales()
        self.refresh_data()
    
    def setup_sales(self):
        """Setup sales interface"""
        self.set_title("إدارة المبيعات - محل الحسيني")
        self.setMinimumSize(1400, 900)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_layout.addWidget(splitter)
        
        # Left panel - Sales list
        self.setup_sales_panel(splitter)
        
        # Right panel - Quick sale
        if self.has_permission("sales"):
            self.setup_quick_sale_panel(splitter)
    
    def setup_sales_panel(self, splitter):
        """Setup sales list panel"""
        sales_widget = QWidget()
        sales_layout = QVBoxLayout(sales_widget)
        
        # Title
        title_label = QLabel("قائمة المبيعات")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        sales_layout.addWidget(title_label)
        
        # Toolbar
        self.setup_sales_toolbar(sales_layout)
        
        # Filters
        self.setup_sales_filters(sales_layout)
        
        # Sales table
        self.setup_sales_table(sales_layout)
        
        # Statistics
        self.setup_sales_statistics(sales_layout)
        
        splitter.addWidget(sales_widget)
    
    def setup_sales_toolbar(self, layout):
        """Setup sales toolbar"""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_frame.setMaximumHeight(60)
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        
        # New sale button
        if self.has_permission("sales"):
            self.new_sale_btn = QPushButton("مبيعة جديدة")
            self.new_sale_btn.setStyleSheet("""
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
            self.new_sale_btn.clicked.connect(self.new_sale)
            toolbar_layout.addWidget(self.new_sale_btn)
        
        # View sale button
        self.view_sale_btn = QPushButton("عرض الفاتورة")
        self.view_sale_btn.setStyleSheet("""
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
        self.view_sale_btn.clicked.connect(self.view_sale)
        self.view_sale_btn.setEnabled(False)
        toolbar_layout.addWidget(self.view_sale_btn)
        
        # Print invoice button
        self.print_invoice_btn = QPushButton("طباعة الفاتورة")
        self.print_invoice_btn.clicked.connect(self.print_invoice)
        self.print_invoice_btn.setEnabled(False)
        toolbar_layout.addWidget(self.print_invoice_btn)
        
        # Return button
        if self.has_permission("returns"):
            self.return_btn = QPushButton("إرجاع")
            self.return_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;
                    color: black;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e0a800;
                }
            """)
            self.return_btn.clicked.connect(self.process_return)
            self.return_btn.setEnabled(False)
            toolbar_layout.addWidget(self.return_btn)
        
        toolbar_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("تحديث")
        self.refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(toolbar_frame)
    
    def setup_sales_filters(self, layout):
        """Setup sales filters"""
        filters_frame = QFrame()
        filters_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        filters_frame.setMaximumHeight(100)
        
        filters_layout = QGridLayout(filters_frame)
        
        # Date range
        filters_layout.addWidget(QLabel("من تاريخ:"), 0, 0)
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.filter_sales)
        filters_layout.addWidget(self.date_from, 0, 1)
        
        filters_layout.addWidget(QLabel("إلى تاريخ:"), 0, 2)
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self.filter_sales)
        filters_layout.addWidget(self.date_to, 0, 3)
        
        # Search
        filters_layout.addWidget(QLabel("البحث:"), 1, 0)
        self.sales_search_edit = QLineEdit()
        self.sales_search_edit.setPlaceholderText("رقم الفاتورة أو اسم العميل...")
        self.sales_search_edit.textChanged.connect(self.filter_sales)
        filters_layout.addWidget(self.sales_search_edit, 1, 1, 1, 3)
        
        layout.addWidget(filters_frame)
    
    def setup_sales_table(self, layout):
        """Setup sales table"""
        self.sales_table = DataTableWidget()
        self.sales_table.setColumns([
            "رقم الفاتورة", "العميل", "التاريخ", "المبلغ", 
            "الضريبة", "الخصم", "المدفوع", "الباقي", "المستخدم"
        ])
        
        # Connect selection signal
        self.sales_table.itemSelectionChanged.connect(self.on_sale_selection_changed)
        self.sales_table.itemDoubleClicked.connect(self.view_sale)
        
        layout.addWidget(self.sales_table)
    
    def setup_sales_statistics(self, layout):
        """Setup sales statistics"""
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        stats_frame.setMaximumHeight(60)
        
        stats_layout = QHBoxLayout(stats_frame)
        
        self.total_sales_label = QLabel("إجمالي المبيعات: 0")
        self.total_amount_label = QLabel("إجمالي المبلغ: 0 ج.م")
        self.avg_sale_label = QLabel("متوسط المبيعة: 0 ج.م")
        
        stats_layout.addWidget(self.total_sales_label)
        stats_layout.addWidget(self.total_amount_label)
        stats_layout.addWidget(self.avg_sale_label)
        stats_layout.addStretch()
        
        layout.addWidget(stats_frame)
    
    def setup_quick_sale_panel(self, splitter):
        """Setup quick sale panel"""
        quick_sale_widget = QWidget()
        quick_sale_layout = QVBoxLayout(quick_sale_widget)
        
        # Title
        title_label = QLabel("مبيعة سريعة")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        quick_sale_layout.addWidget(title_label)
        
        # Product search
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        
        search_layout.addWidget(QLabel("بحث المنتج:"))
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("اسم المنتج أو الكود...")
        self.product_search.returnPressed.connect(self.search_product)
        search_layout.addWidget(self.product_search)
        
        search_btn = QPushButton("بحث")
        search_btn.clicked.connect(self.search_product)
        search_layout.addWidget(search_btn)
        
        quick_sale_layout.addWidget(search_frame)
        
        # Cart table
        cart_label = QLabel("عربة التسوق:")
        cart_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        quick_sale_layout.addWidget(cart_label)
        
        self.cart_table = DataTableWidget()
        self.cart_table.setColumns(["المنتج", "السعر", "الكمية", "المجموع"])
        quick_sale_layout.addWidget(self.cart_table)
        
        # Cart controls
        cart_controls_frame = QFrame()
        cart_controls_layout = QHBoxLayout(cart_controls_frame)
        
        add_to_cart_btn = QPushButton("إضافة للعربة")
        add_to_cart_btn.clicked.connect(self.add_to_cart)
        cart_controls_layout.addWidget(add_to_cart_btn)
        
        remove_from_cart_btn = QPushButton("إزالة من العربة")
        remove_from_cart_btn.clicked.connect(self.remove_from_cart)
        cart_controls_layout.addWidget(remove_from_cart_btn)
        
        cart_controls_layout.addStretch()
        
        quick_sale_layout.addWidget(cart_controls_frame)
        
        # Totals
        totals_frame = QFrame()
        totals_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        totals_layout = QFormLayout(totals_frame)
        
        self.subtotal_label = QLabel("0.00 ج.م")
        self.tax_label = QLabel("0.00 ج.م")
        self.discount_edit = QDoubleSpinBox()
        self.discount_edit.setMaximum(99999.99)
        self.discount_edit.valueChanged.connect(self.calculate_total)
        self.total_label = QLabel("0.00 ج.م")
        self.total_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        totals_layout.addRow("المجموع الفرعي:", self.subtotal_label)
        totals_layout.addRow("الضريبة:", self.tax_label)
        totals_layout.addRow("الخصم:", self.discount_edit)
        totals_layout.addRow("الإجمالي:", self.total_label)
        
        quick_sale_layout.addWidget(totals_frame)
        
        # Payment
        payment_frame = QFrame()
        payment_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        payment_layout = QFormLayout(payment_frame)
        
        self.customer_name_edit = QLineEdit()
        self.customer_phone_edit = QLineEdit()
        self.paid_amount_edit = QDoubleSpinBox()
        self.paid_amount_edit.setMaximum(99999.99)
        self.paid_amount_edit.valueChanged.connect(self.calculate_change)
        self.change_label = QLabel("0.00 ج.م")
        
        payment_layout.addRow("اسم العميل:", self.customer_name_edit)
        payment_layout.addRow("هاتف العميل:", self.customer_phone_edit)
        payment_layout.addRow("المبلغ المدفوع:", self.paid_amount_edit)
        payment_layout.addRow("الباقي:", self.change_label)
        
        quick_sale_layout.addWidget(payment_frame)
        
        # Complete sale button
        complete_sale_btn = QPushButton("إتمام المبيعة")
        complete_sale_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        complete_sale_btn.clicked.connect(self.complete_sale)
        quick_sale_layout.addWidget(complete_sale_btn)
        
        # Initialize cart
        self.cart_items = []
        
        splitter.addWidget(quick_sale_widget)
        
        # Set splitter proportions
        splitter.setSizes([800, 600])
    
    def refresh_data(self):
        """Refresh sales data"""
        try:
            session = self.db_manager.get_session()
            self.load_sales(session)
            self.update_sales_statistics(session)
            self.update_status("تم تحديث بيانات المبيعات")
        except Exception as e:
            self.logger.error(f"خطأ في تحديث بيانات المبيعات: {e}")
            self.show_message(f"خطأ في تحديث البيانات: {str(e)}", "error")
        finally:
            if 'session' in locals():
                session.close()
    
    def load_sales(self, session):
        """Load sales into table"""
        from models import Sale
        
        # Get filter values
        date_from = self.date_from.date().toPython()
        date_to = self.date_to.date().toPython()
        search_text = self.sales_search_edit.text().strip()
        
        # Build query
        query = session.query(Sale)
        
        # Date filter
        date_from_dt = datetime.combine(date_from, datetime.min.time())
        date_to_dt = datetime.combine(date_to, datetime.max.time())
        query = query.filter(Sale.created_at >= date_from_dt, Sale.created_at <= date_to_dt)
        
        # Search filter
        if search_text:
            query = query.filter(
                (Sale.invoice_no.contains(search_text)) |
                (Sale.customer.has(name=search_text))
            )
        
        # Get sales
        sales = query.order_by(Sale.created_at.desc()).all()
        
        # Populate table
        data = []
        for sale in sales:
            customer_name = sale.customer.name if sale.customer else "عميل نقدي"
            data.append([
                sale.invoice_no,
                customer_name,
                sale.created_at.strftime("%Y-%m-%d %H:%M"),
                f"{sale.total:.2f}",
                f"{sale.tax:.2f}",
                f"{sale.discount:.2f}",
                f"{sale.paid:.2f}",
                f"{sale.change:.2f}",
                sale.user.name if sale.user else ""
            ])
        
        self.sales_table.setData(data)
        self.current_sales = sales
    
    def update_sales_statistics(self, session):
        """Update sales statistics"""
        if hasattr(self, 'current_sales'):
            total_sales = len(self.current_sales)
            total_amount = sum(sale.total for sale in self.current_sales)
            avg_sale = total_amount / total_sales if total_sales > 0 else 0
            
            self.total_sales_label.setText(f"إجمالي المبيعات: {total_sales}")
            self.total_amount_label.setText(f"إجمالي المبلغ: {total_amount:.2f} ج.م")
            self.avg_sale_label.setText(f"متوسط المبيعة: {avg_sale:.2f} ج.م")
    
    def filter_sales(self):
        """Filter sales based on current settings"""
        self.refresh_data()
    
    def on_sale_selection_changed(self):
        """Handle sale selection change"""
        selected_rows = self.sales_table.get_selected_rows()
        has_selection = len(selected_rows) > 0
        
        self.view_sale_btn.setEnabled(has_selection)
        self.print_invoice_btn.setEnabled(has_selection)
        
        if self.has_permission("returns"):
            self.return_btn.setEnabled(has_selection)
    
    def new_sale(self):
        """Create new sale"""
        if not self.require_permission("sales", "إنشاء مبيعة جديدة"):
            return
        
        dialog = SaleDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.log_action("new_sale", "إنشاء مبيعة جديدة")
    
    def view_sale(self):
        """View selected sale"""
        selected_rows = self.sales_table.get_selected_rows()
        if not selected_rows:
            return
        
        row_index = selected_rows[0]
        if hasattr(self, 'current_sales') and row_index < len(self.current_sales):
            sale = self.current_sales[row_index]
            
            # Create sale details dialog
            dialog = SaleDetailsDialog(sale, parent=self)
            dialog.exec()
    
    def print_invoice(self):
        """Print selected invoice"""
        selected_rows = self.sales_table.get_selected_rows()
        if not selected_rows:
            return
        
        row_index = selected_rows[0]
        if hasattr(self, 'current_sales') and row_index < len(self.current_sales):
            sale = self.current_sales[row_index]
            
            try:
                from utils.pdf_generator import generate_invoice_pdf
                pdf_content = generate_invoice_pdf(sale)
                
                # Save and open PDF
                from pathlib import Path
                pdf_path = Path("temp_invoice.pdf")
                with open(pdf_path, "wb") as f:
                    f.write(pdf_content)
                
                # Open with default PDF viewer
                import os
                os.startfile(str(pdf_path))
                
                self.log_action("print_invoice", f"طباعة فاتورة: {sale.invoice_no}")
                
            except Exception as e:
                self.logger.error(f"خطأ في طباعة الفاتورة: {e}")
                self.show_message(f"خطأ في طباعة الفاتورة: {str(e)}", "error")
    
    def process_return(self):
        """Process return for selected sale"""
        if not self.require_permission("returns", "معالجة المرتجعات"):
            return
        
        # TODO: Implement return processing dialog
        self.show_message("معالجة المرتجعات ستكون متاحة قريباً", "info")
    
    def search_product(self):
        """Search for product in quick sale"""
        search_text = self.product_search.text().strip()
        if not search_text:
            return
        
        try:
            session = self.db_manager.get_session()
            from models import Product
            
            products = session.query(Product).filter(
                Product.active == True,
                (Product.name_ar.contains(search_text)) |
                (Product.sku.contains(search_text)) |
                (Product.barcode.contains(search_text))
            ).limit(10).all()
            
            if products:
                # Show product selection dialog
                from .dialogs.product_selection_dialog import ProductSelectionDialog
                dialog = ProductSelectionDialog(products, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    selected_product = dialog.get_selected_product()
                    if selected_product:
                        self.add_product_to_cart(selected_product)
            else:
                self.show_message("لم يتم العثور على منتجات", "info")
                
        except Exception as e:
            self.logger.error(f"خطأ في البحث عن المنتج: {e}")
            self.show_message(f"خطأ في البحث: {str(e)}", "error")
        finally:
            if 'session' in locals():
                session.close()
    
    def add_product_to_cart(self, product):
        """Add product to cart"""
        # Check if product already in cart
        for item in self.cart_items:
            if item['product_id'] == product.id:
                item['quantity'] += 1
                item['total'] = item['quantity'] * item['price']
                break
        else:
            # Add new item
            self.cart_items.append({
                'product_id': product.id,
                'name': product.name_ar,
                'price': float(product.sale_price),
                'quantity': 1,
                'total': float(product.sale_price)
            })
        
        self.update_cart_display()
        self.calculate_total()
    
    def add_to_cart(self):
        """Add selected product to cart"""
        # For now, just show message - would need product selection dialog
        self.show_message("استخدم البحث لإضافة المنتجات", "info")
    
    def remove_from_cart(self):
        """Remove selected item from cart"""
        selected_rows = self.cart_table.get_selected_rows()
        if selected_rows and self.cart_items:
            row_index = selected_rows[0]
            if row_index < len(self.cart_items):
                del self.cart_items[row_index]
                self.update_cart_display()
                self.calculate_total()
    
    def update_cart_display(self):
        """Update cart table display"""
        data = []
        for item in self.cart_items:
            data.append([
                item['name'],
                f"{item['price']:.2f}",
                str(item['quantity']),
                f"{item['total']:.2f}"
            ])
        
        self.cart_table.setData(data)
    
    def calculate_total(self):
        """Calculate and update totals"""
        if not self.cart_items:
            self.subtotal_label.setText("0.00 ج.م")
            self.tax_label.setText("0.00 ج.م")
            self.total_label.setText("0.00 ج.م")
            return
        
        subtotal = sum(item['total'] for item in self.cart_items)
        discount = self.discount_edit.value()
        
        # Calculate tax (14% VAT)
        taxable_amount = subtotal - discount
        tax = taxable_amount * 0.14
        
        total = taxable_amount + tax
        
        self.subtotal_label.setText(f"{subtotal:.2f} ج.م")
        self.tax_label.setText(f"{tax:.2f} ج.م")
        self.total_label.setText(f"{total:.2f} ج.م")
        
        self.calculate_change()
    
    def calculate_change(self):
        """Calculate change amount"""
        total_text = self.total_label.text().replace(" ج.م", "")
        try:
            total = float(total_text)
            paid = self.paid_amount_edit.value()
            change = paid - total
            self.change_label.setText(f"{change:.2f} ج.م")
        except:
            self.change_label.setText("0.00 ج.م")
    
    def complete_sale(self):
        """Complete the sale"""
        if not self.cart_items:
            self.show_message("لا توجد منتجات في العربة", "warning")
            return
        
        try:
            session = self.db_manager.get_session()
            
            # Create sale record
            from models import Sale, SaleItem, Customer, StockMovement
            
            # Get or create customer
            customer_id = None
            customer_name = self.customer_name_edit.text().strip()
            customer_phone = self.customer_phone_edit.text().strip()
            
            if customer_name:
                customer = None
                if customer_phone:
                    customer = session.query(Customer).filter_by(phone=customer_phone).first()
                
                if not customer:
                    customer = Customer(
                        name=customer_name,
                        phone=customer_phone
                    )
                    session.add(customer)
                    session.flush()
                
                customer_id = customer.id
            
            # Generate invoice number
            invoice_no = self.generate_invoice_number(session)
            
            # Calculate totals
            subtotal = sum(item['total'] for item in self.cart_items)
            discount = self.discount_edit.value()
            taxable_amount = subtotal - discount
            tax = taxable_amount * 0.14
            total = taxable_amount + tax
            paid = self.paid_amount_edit.value()
            change = paid - total
            
            # Create sale
            sale = Sale(
                invoice_no=invoice_no,
                customer_id=customer_id,
                total=total,
                tax=tax,
                discount=discount,
                paid=paid,
                change=change,
                user_id=self.user_data['id']
            )
            session.add(sale)
            session.flush()
            
            # Add sale items and update stock
            for item in self.cart_items:
                # Create sale item
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['price'],
                    line_total=item['total']
                )
                session.add(sale_item)
                
                # Update product stock
                from models import Product
                product = session.query(Product).get(item['product_id'])
                if product:
                    product.quantity -= item['quantity']
                    
                    # Create stock movement
                    movement = StockMovement(
                        product_id=product.id,
                        change_qty=-item['quantity'],
                        type='sale',
                        reference_id=sale.id,
                        user_id=self.user_data['id'],
                        note=f'بيع فاتورة رقم {invoice_no}'
                    )
                    session.add(movement)
            
            session.commit()
            
            # Clear cart
            self.cart_items = []
            self.update_cart_display()
            self.calculate_total()
            
            # Clear form
            self.customer_name_edit.clear()
            self.customer_phone_edit.clear()
            self.paid_amount_edit.setValue(0)
            self.discount_edit.setValue(0)
            
            # Refresh sales list
            self.refresh_data()
            
            self.show_message(f"تم إتمام المبيعة بنجاح\nرقم الفاتورة: {invoice_no}", "success")
            self.log_action("complete_sale", f"إتمام مبيعة: {invoice_no}")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"خطأ في إتمام المبيعة: {e}")
            self.show_message(f"خطأ في إتمام المبيعة: {str(e)}", "error")
        finally:
            session.close()
    
    def generate_invoice_number(self, session):
        """Generate unique invoice number"""
        from models import Sale
        from datetime import datetime
        
        today = datetime.now()
        prefix = f"INV{today.strftime('%Y%m%d')}"
        
        # Get last invoice number for today
        last_sale = session.query(Sale).filter(
            Sale.invoice_no.like(f"{prefix}%")
        ).order_by(Sale.id.desc()).first()
        
        if last_sale:
            # Extract sequence number and increment
            try:
                sequence = int(last_sale.invoice_no[-3:]) + 1
            except:
                sequence = 1
        else:
            sequence = 1
        
        return f"{prefix}{sequence:03d}"


class SaleDetailsDialog(QDialog):
    """Dialog for viewing sale details"""
    
    def __init__(self, sale, parent=None):
        super().__init__(parent)
        self.sale = sale
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"تفاصيل الفاتورة - {self.sale.invoice_no}")
        self.setMinimumSize(600, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(self)
        
        # Sale info
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        info_layout = QFormLayout(info_frame)
        
        info_layout.addRow("رقم الفاتورة:", QLabel(self.sale.invoice_no))
        info_layout.addRow("التاريخ:", QLabel(self.sale.created_at.strftime("%Y-%m-%d %H:%M")))
        
        customer_name = self.sale.customer.name if self.sale.customer else "عميل نقدي"
        info_layout.addRow("العميل:", QLabel(customer_name))
        
        info_layout.addRow("الكاشير:", QLabel(self.sale.user.name))
        
        layout.addWidget(info_frame)
        
        # Items table
        items_label = QLabel("عناصر الفاتورة:")
        items_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(items_label)
        
        items_table = DataTableWidget()
        items_table.setColumns(["المنتج", "السعر", "الكمية", "المجموع"])
        
        items_data = []
        for item in self.sale.sale_items:
            items_data.append([
                item.product.name_ar,
                f"{item.unit_price:.2f}",
                str(item.quantity),
                f"{item.line_total:.2f}"
            ])
        
        items_table.setData(items_data)
        layout.addWidget(items_table)
        
        # Totals
        totals_frame = QFrame()
        totals_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        totals_layout = QFormLayout(totals_frame)
        
        subtotal = sum(item.line_total for item in self.sale.sale_items)
        totals_layout.addRow("المجموع الفرعي:", QLabel(f"{subtotal:.2f} ج.م"))
        totals_layout.addRow("الخصم:", QLabel(f"{self.sale.discount:.2f} ج.م"))
        totals_layout.addRow("الضريبة:", QLabel(f"{self.sale.tax:.2f} ج.م"))
        totals_layout.addRow("الإجمالي:", QLabel(f"{self.sale.total:.2f} ج.م"))
        totals_layout.addRow("المدفوع:", QLabel(f"{self.sale.paid:.2f} ج.م"))
        totals_layout.addRow("الباقي:", QLabel(f"{self.sale.change:.2f} ج.م"))
        
        layout.addWidget(totals_frame)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
