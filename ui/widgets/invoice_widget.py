# -*- coding: utf-8 -*-
"""
Invoice preview widget
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QScrollArea, QFrame, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPrintDialog, QPrinter

from models.sales import Sale
from config.settings import settings
from utils.helpers import format_currency

class InvoiceWidget(QWidget):
    """Invoice preview widget for displaying formatted invoices"""
    
    print_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_sale = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for invoice content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Invoice content widget
        self.invoice_content = QWidget()
        self.invoice_content.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
            }
        """)
        
        scroll_area.setWidget(self.invoice_content)
        layout.addWidget(scroll_area)
        
        self.setLayout(layout)
        
    def set_sale(self, sale: Sale):
        """Set sale data and update invoice display"""
        self.current_sale = sale
        self.update_invoice_display()
        
    def update_invoice_display(self):
        """Update invoice display with current sale data"""
        if not self.current_sale:
            return
            
        # Clear existing layout
        if self.invoice_content.layout():
            while self.invoice_content.layout().count():
                child = self.invoice_content.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            layout = QVBoxLayout()
            self.invoice_content.setLayout(layout)
            
        layout = self.invoice_content.layout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section
        self.create_header_section(layout)
        
        # Customer section
        self.create_customer_section(layout)
        
        # Items section
        self.create_items_section(layout)
        
        # Totals section
        self.create_totals_section(layout)
        
        # Footer section
        self.create_footer_section(layout)
        
    def create_header_section(self, parent_layout):
        """Create invoice header section"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.Box)
        header_frame.setLineWidth(1)
        header_layout = QVBoxLayout()
        
        # Shop name
        shop_name = QLabel(settings.shop.name)
        shop_name.setFont(QFont("Cairo", 18, QFont.Weight.Bold))
        shop_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Shop details
        shop_details = []
        if settings.shop.address:
            shop_details.append(f"العنوان: {settings.shop.address}")
        if settings.shop.phone:
            shop_details.append(f"الهاتف: {settings.shop.phone}")
        if settings.shop.email:
            shop_details.append(f"البريد الإلكتروني: {settings.shop.email}")
        if settings.shop.tax_number:
            shop_details.append(f"الرقم الضريبي: {settings.shop.tax_number}")
            
        for detail in shop_details:
            detail_label = QLabel(detail)
            detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(detail_label)
        
        # Invoice title and number
        title_layout = QHBoxLayout()
        
        invoice_title = QLabel("فاتورة مبيعات")
        invoice_title.setFont(QFont("Cairo", 16, QFont.Weight.Bold))
        
        invoice_number = QLabel(f"رقم الفاتورة: {self.current_sale.invoice_no}")
        invoice_number.setFont(QFont("Cairo", 12, QFont.Weight.Bold))
        
        title_layout.addWidget(invoice_title)
        title_layout.addStretch()
        title_layout.addWidget(invoice_number)
        
        # Invoice date
        invoice_date = QLabel(f"التاريخ: {self.current_sale.created_at.strftime('%Y-%m-%d %H:%M')}")
        invoice_date.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        header_layout.addWidget(shop_name)
        header_layout.addLayout(title_layout)
        header_layout.addWidget(invoice_date)
        
        header_frame.setLayout(header_layout)
        parent_layout.addWidget(header_frame)
        
    def create_customer_section(self, parent_layout):
        """Create customer information section"""
        if self.current_sale.customer:
            customer_frame = QFrame()
            customer_frame.setFrameStyle(QFrame.Shape.Box)
            customer_frame.setLineWidth(1)
            customer_layout = QVBoxLayout()
            
            customer_title = QLabel("بيانات العميل")
            customer_title.setFont(QFont("Cairo", 12, QFont.Weight.Bold))
            
            customer_name = QLabel(f"الاسم: {self.current_sale.customer.name}")
            customer_phone = QLabel(f"الهاتف: {self.current_sale.customer.phone or ''}")
            
            customer_layout.addWidget(customer_title)
            customer_layout.addWidget(customer_name)
            customer_layout.addWidget(customer_phone)
            
            customer_frame.setLayout(customer_layout)
            parent_layout.addWidget(customer_frame)
            
    def create_items_section(self, parent_layout):
        """Create items table section"""
        items_frame = QFrame()
        items_frame.setFrameStyle(QFrame.Shape.Box)
        items_frame.setLineWidth(1)
        items_layout = QVBoxLayout()
        
        # Table header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(0)
        
        headers = ["م", "المنتج", "سعر الوحدة", "الكمية", "المجموع"]
        header_widths = [50, 300, 100, 80, 100]
        
        for i, (header, width) in enumerate(zip(headers, header_widths)):
            header_label = QLabel(header)
            header_label.setFont(QFont("Cairo", 11, QFont.Weight.Bold))
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_label.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px;")
            header_label.setFixedWidth(width)
            header_layout.addWidget(header_label)
        
        items_layout.addLayout(header_layout)
        
        # Table rows
        for i, item in enumerate(self.current_sale.items, 1):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(0)
            
            # Row number
            num_label = QLabel(str(i))
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setStyleSheet("border: 1px solid #dee2e6; padding: 8px;")
            num_label.setFixedWidth(header_widths[0])
            
            # Product name
            product_label = QLabel(item.product.name_ar if item.product else "منتج محذوف")
            product_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            product_label.setStyleSheet("border: 1px solid #dee2e6; padding: 8px;")
            product_label.setFixedWidth(header_widths[1])
            product_label.setWordWrap(True)
            
            # Unit price
            price_label = QLabel(format_currency(item.unit_price))
            price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_label.setStyleSheet("border: 1px solid #dee2e6; padding: 8px;")
            price_label.setFixedWidth(header_widths[2])
            
            # Quantity
            qty_label = QLabel(str(item.quantity))
            qty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_label.setStyleSheet("border: 1px solid #dee2e6; padding: 8px;")
            qty_label.setFixedWidth(header_widths[3])
            
            # Line total
            total_label = QLabel(format_currency(item.line_total))
            total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            total_label.setStyleSheet("border: 1px solid #dee2e6; padding: 8px;")
            total_label.setFixedWidth(header_widths[4])
            
            row_layout.addWidget(num_label)
            row_layout.addWidget(product_label)
            row_layout.addWidget(price_label)
            row_layout.addWidget(qty_label)
            row_layout.addWidget(total_label)
            
            items_layout.addLayout(row_layout)
        
        items_frame.setLayout(items_layout)
        parent_layout.addWidget(items_frame)
        
    def create_totals_section(self, parent_layout):
        """Create totals section"""
        totals_frame = QFrame()
        totals_frame.setFrameStyle(QFrame.Shape.Box)
        totals_frame.setLineWidth(1)
        totals_layout = QVBoxLayout()
        
        # Totals grid
        totals_grid = QGridLayout()
        totals_grid.setColumnStretch(0, 1)
        totals_grid.setColumnStretch(1, 0)
        
        row = 0
        
        # Subtotal
        totals_grid.addWidget(QLabel("المجموع الفرعي:"), row, 0, Qt.AlignmentFlag.AlignRight)
        subtotal_label = QLabel(format_currency(self.current_sale.subtotal))
        subtotal_label.setFont(QFont("Cairo", 11, QFont.Weight.Bold))
        totals_grid.addWidget(subtotal_label, row, 1, Qt.AlignmentFlag.AlignLeft)
        row += 1
        
        # Discount
        if self.current_sale.discount_amount > 0:
            totals_grid.addWidget(QLabel("الخصم:"), row, 0, Qt.AlignmentFlag.AlignRight)
            discount_label = QLabel(f"- {format_currency(self.current_sale.discount_amount)}")
            discount_label.setStyleSheet("color: #dc3545;")
            totals_grid.addWidget(discount_label, row, 1, Qt.AlignmentFlag.AlignLeft)
            row += 1
        
        # Tax
        if self.current_sale.tax_amount > 0:
            totals_grid.addWidget(QLabel("الضريبة:"), row, 0, Qt.AlignmentFlag.AlignRight)
            tax_label = QLabel(format_currency(self.current_sale.tax_amount))
            totals_grid.addWidget(tax_label, row, 1, Qt.AlignmentFlag.AlignLeft)
            row += 1
        
        # Total
        totals_grid.addWidget(QLabel("المجموع الكلي:"), row, 0, Qt.AlignmentFlag.AlignRight)
        total_label = QLabel(format_currency(self.current_sale.total))
        total_label.setFont(QFont("Cairo", 14, QFont.Weight.Bold))
        total_label.setStyleSheet("color: #28a745; background-color: #e8f5e8; padding: 5px; border-radius: 3px;")
        totals_grid.addWidget(total_label, row, 1, Qt.AlignmentFlag.AlignLeft)
        row += 1
        
        # Payment info
        if self.current_sale.paid > 0:
            totals_grid.addWidget(QLabel("المبلغ المدفوع:"), row, 0, Qt.AlignmentFlag.AlignRight)
            paid_label = QLabel(format_currency(self.current_sale.paid))
            totals_grid.addWidget(paid_label, row, 1, Qt.AlignmentFlag.AlignLeft)
            row += 1
            
            if self.current_sale.change_amount > 0:
                totals_grid.addWidget(QLabel("الباقي:"), row, 0, Qt.AlignmentFlag.AlignRight)
                change_label = QLabel(format_currency(self.current_sale.change_amount))
                change_label.setStyleSheet("color: #007bff;")
                totals_grid.addWidget(change_label, row, 1, Qt.AlignmentFlag.AlignLeft)
        
        totals_layout.addLayout(totals_grid)
        totals_frame.setLayout(totals_layout)
        parent_layout.addWidget(totals_frame)
        
    def create_footer_section(self, parent_layout):
        """Create footer section"""
        footer_frame = QFrame()
        footer_layout = QVBoxLayout()
        
        # Payment method
        payment_method_map = {
            "cash": "نقدي",
            "card": "بطاقة ائتمان",
            "credit": "آجل"
        }
        payment_method = payment_method_map.get(self.current_sale.payment_method, self.current_sale.payment_method)
        
        payment_label = QLabel(f"طريقة الدفع: {payment_method}")
        payment_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Cashier info
        cashier_label = QLabel(f"الكاشير: {self.current_sale.user.name}")
        cashier_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Thank you message
        thanks_label = QLabel("شكراً لتعاملكم معنا")
        thanks_label.setFont(QFont("Cairo", 12, QFont.Weight.Bold))
        thanks_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thanks_label.setStyleSheet("margin: 10px 0;")
        
        footer_layout.addWidget(payment_label)
        footer_layout.addWidget(cashier_label)
        footer_layout.addWidget(thanks_label)
        
        footer_frame.setLayout(footer_layout)
        parent_layout.addWidget(footer_frame)
        
        # Add stretch to push content to top
        parent_layout.addStretch()
        
    def clear_invoice(self):
        """Clear invoice display"""
        self.current_sale = None
        if self.invoice_content.layout():
            while self.invoice_content.layout().count():
                child = self.invoice_content.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
    def print_invoice(self):
        """Print the current invoice"""
        if not self.current_sale:
            return
            
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPrinter.PageSize.A4)
        
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() == print_dialog.DialogCode.Accepted:
            painter = QPainter(printer)
            
            # Scale widget to fit printer page
            widget_rect = self.invoice_content.rect()
            page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            
            # Calculate scale factor
            scale_x = page_rect.width() / widget_rect.width()
            scale_y = page_rect.height() / widget_rect.height()
            scale = min(scale_x, scale_y) * 0.9  # 90% to leave margins
            
            painter.scale(scale, scale)
            self.invoice_content.render(painter)
            painter.end()
