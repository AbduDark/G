# -*- coding: utf-8 -*-
"""
Global search widget for the application
"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, 
                            QCompleter, QListWidget, QListWidgetItem, QVBoxLayout,
                            QFrame, QLabel, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QStringListModel
from PyQt6.QtGui import QFont

from config.database import get_db_session
from models.product import Product
from models.sales import Sale, Customer
from models.repair import Repair

class GlobalSearchWidget(QWidget):
    """Global search widget with live search functionality"""
    
    # Signals
    result_selected = pyqtSignal(str, int)  # table_name, record_id
    
    def __init__(self):
        super().__init__()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("البحث في المنتجات، الفواتير، العملاء، الصيانة...")
        self.search_input.setMinimumWidth(300)
        self.search_input.setMaximumWidth(400)
        
        # Search button
        self.search_button = QPushButton("بحث")
        self.search_button.setMaximumWidth(60)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_button)
        
        self.setLayout(layout)
        
        # Results popup (initially hidden)
        self.results_popup = SearchResultsPopup(self)
        self.results_popup.hide()
        
    def setup_connections(self):
        """Setup signal connections"""
        self.search_input.textChanged.connect(self.on_text_changed)
        self.search_button.clicked.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.perform_search)
        
        # Connect results popup signals
        self.results_popup.result_selected.connect(self.result_selected.emit)
        self.results_popup.result_selected.connect(self.hide_results)
        
    def on_text_changed(self, text: str):
        """Handle text change with debouncing"""
        if len(text) >= 2:  # Start searching after 2 characters
            self.search_timer.start(300)  # 300ms delay
        else:
            self.search_timer.stop()
            self.hide_results()
            
    def perform_search(self):
        """Perform search across all tables"""
        query = self.search_input.text().strip()
        if len(query) < 2:
            self.hide_results()
            return
        
        try:
            results = self.search_database(query)
            self.show_results(results)
        except Exception as e:
            print(f"Search error: {e}")
            
    def search_database(self, query: str):
        """Search across all relevant database tables"""
        session = get_db_session()
        results = []
        
        try:
            # Search products
            products = session.query(Product).filter(
                (Product.name_ar.contains(query)) |
                (Product.sku.contains(query)) |
                (Product.barcode.contains(query))
            ).limit(10).all()
            
            for product in products:
                results.append({
                    'type': 'product',
                    'id': product.id,
                    'title': product.name_ar,
                    'subtitle': f"SKU: {product.sku} | الكمية: {product.quantity}",
                    'icon': '📦'
                })
            
            # Search sales/invoices
            sales = session.query(Sale).filter(
                Sale.invoice_no.contains(query)
            ).limit(5).all()
            
            for sale in sales:
                customer_name = sale.customer.name if sale.customer else "عميل نقدي"
                results.append({
                    'type': 'sale',
                    'id': sale.id,
                    'title': f"فاتورة رقم: {sale.invoice_no}",
                    'subtitle': f"العميل: {customer_name} | المبلغ: {sale.total} ج.م",
                    'icon': '🧾'
                })
            
            # Search customers
            customers = session.query(Customer).filter(
                (Customer.name.contains(query)) |
                (Customer.phone.contains(query))
            ).limit(5).all()
            
            for customer in customers:
                results.append({
                    'type': 'customer',
                    'id': customer.id,
                    'title': customer.name,
                    'subtitle': f"الهاتف: {customer.phone}",
                    'icon': '👤'
                })
            
            # Search repairs
            repairs = session.query(Repair).filter(
                (Repair.ticket_no.contains(query)) |
                (Repair.device_model.contains(query)) |
                (Repair.problem_desc.contains(query))
            ).limit(5).all()
            
            for repair in repairs:
                results.append({
                    'type': 'repair',
                    'id': repair.id,
                    'title': f"تذكرة صيانة: {repair.ticket_no}",
                    'subtitle': f"الجهاز: {repair.device_model} | الحالة: {repair.status}",
                    'icon': '🔧'
                })
                
        finally:
            session.close()
            
        return results
        
    def show_results(self, results):
        """Show search results popup"""
        if results:
            self.results_popup.set_results(results)
            self.results_popup.show_at_widget(self.search_input)
        else:
            self.hide_results()
            
    def hide_results(self):
        """Hide search results popup"""
        self.results_popup.hide()
        
    def clear_search(self):
        """Clear search input and results"""
        self.search_input.clear()
        self.hide_results()

class SearchResultsPopup(QFrame):
    """Popup widget to display search results"""
    
    # Signals
    result_selected = pyqtSignal(str, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        
    def setup_ui(self):
        """Setup user interface"""
        self.setFixedSize(400, 300)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setFrameStyle(QFrame.Shape.NoFrame)
        self.results_list.itemClicked.connect(self.on_item_clicked)
        
        layout.addWidget(self.results_list)
        self.setLayout(layout)
        
        # Apply styles
        self.setStyleSheet("""
            SearchResultsPopup {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            
            QListWidget {
                background-color: white;
                border: none;
                outline: none;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        
    def set_results(self, results):
        """Set search results"""
        self.results_list.clear()
        
        for result in results:
            item = QListWidgetItem()
            
            # Create widget for item content
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(5, 5, 5, 5)
            
            # Icon
            icon_label = QLabel(result['icon'])
            icon_label.setFont(QFont("Segoe UI Emoji", 16))
            icon_label.setFixedWidth(30)
            
            # Content
            content_layout = QVBoxLayout()
            content_layout.setSpacing(2)
            
            title_label = QLabel(result['title'])
            title_label.setFont(QFont("Cairo", 10, QFont.Weight.Bold))
            
            subtitle_label = QLabel(result['subtitle'])
            subtitle_label.setFont(QFont("Cairo", 9))
            subtitle_label.setStyleSheet("color: #6c757d;")
            
            content_layout.addWidget(title_label)
            content_layout.addWidget(subtitle_label)
            
            item_layout.addWidget(icon_label)
            item_layout.addLayout(content_layout)
            item_layout.addStretch()
            
            item_widget.setLayout(item_layout)
            
            # Store result data
            item.setData(Qt.ItemDataRole.UserRole, result)
            
            # Add to list
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, item_widget)
            
    def show_at_widget(self, widget):
        """Show popup below the specified widget"""
        pos = widget.mapToGlobal(widget.rect().bottomLeft())
        self.move(pos)
        self.show()
        
    def on_item_clicked(self, item):
        """Handle item click"""
        result_data = item.data(Qt.ItemDataRole.UserRole)
        if result_data:
            self.result_selected.emit(result_data['type'], result_data['id'])
