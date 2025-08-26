# -*- coding: utf-8 -*-
"""
Balance transfer management window
"""

import logging
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                            QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit,
                            QMessageBox, QHeaderView, QFrame, QGroupBox,
                            QFormLayout, QTabWidget, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from models.user import User
from models.transfer import Transfer
from config.database import get_db_session
from services.report_service import ReportService
from utils.helpers import format_currency, show_error, show_success, generate_transaction_id

class TransferWindow(QMainWindow):
    """Balance transfer management window"""
    
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.transfers_data = []
        self.report_service = ReportService()
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("تحويلات الرصيد")
        self.setMinimumSize(1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Transfers list tab
        self.setup_transfers_tab()
        
        # New transfer tab
        self.setup_new_transfer_tab()
        
        # Statistics tab
        self.setup_statistics_tab()
        
    def setup_transfers_tab(self):
        """Setup transfers list tab"""
        transfers_widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Search and filter controls
        search_label = QLabel("البحث:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("البحث في رقم المعاملة، رقم الهاتف...")
        
        type_label = QLabel("نوع الخدمة:")
        self.type_filter = QComboBox()
        self.type_filter.addItem("جميع الأنواع", None)
        self.type_filter.addItem("فودافون كاش", "vodafone_cash")
        self.type_filter.addItem("اتصالات كاش", "etisalat_cash")
        self.type_filter.addItem("اورانج كاش", "orange_cash")
        self.type_filter.addItem("امان كاش", "aman_cash")
        self.type_filter.addItem("شحن كروت", "card_charge")
        self.type_filter.addItem("تحويل أموال", "money_transfer")
        self.type_filter.addItem("أخرى", "other")
        
        status_label = QLabel("الحالة:")
        self.status_filter = QComboBox()
        self.status_filter.addItem("جميع الحالات", None)
        self.status_filter.addItem("معلقة", "pending")
        self.status_filter.addItem("مكتملة", "completed")
        self.status_filter.addItem("فاشلة", "failed")
        self.status_filter.addItem("ملغاة", "cancelled")
        
        # Action buttons
        self.new_transfer_btn = QPushButton("معاملة جديدة")
        self.edit_transfer_btn = QPushButton("تعديل المعاملة")
        self.verify_transfer_btn = QPushButton("تأكيد المعاملة")
        self.print_receipt_btn = QPushButton("طباعة إيصال")
        
        # Enable/disable based on permissions
        if not self.current_user.has_permission("transfers", "create"):
            self.new_transfer_btn.setEnabled(False)
        if not self.current_user.has_permission("transfers", "update"):
            self.edit_transfer_btn.setEnabled(False)
            self.verify_transfer_btn.setEnabled(False)
        
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.search_input)
        toolbar_layout.addWidget(type_label)
        toolbar_layout.addWidget(self.type_filter)
        toolbar_layout.addWidget(status_label)
        toolbar_layout.addWidget(self.status_filter)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.new_transfer_btn)
        toolbar_layout.addWidget(self.edit_transfer_btn)
        toolbar_layout.addWidget(self.verify_transfer_btn)
        toolbar_layout.addWidget(self.print_receipt_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Transfers table
        self.transfers_table = QTableWidget()
        self.transfers_table.setColumnCount(12)
        self.transfers_table.setHorizontalHeaderLabels([
            "رقم المعاملة", "نوع الخدمة", "المبلغ", "العمولة", "صافي المبلغ",
            "اسم العميل", "رقم الهاتف", "الحالة", "تاريخ المعاملة", "المشغل",
            "رقم المرجع", "الربح"
        ])
        
        # Configure table
        header = self.transfers_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        self.transfers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.transfers_table.setAlternatingRowColors(True)
        self.transfers_table.setSortingEnabled(True)
        
        layout.addWidget(self.transfers_table)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.total_transfers_label = QLabel("إجمالي المعاملات: 0")
        self.total_amount_label = QLabel("إجمالي المبلغ: 0 ج.م")
        self.total_profit_label = QLabel("إجمالي الربح: 0 ج.م")
        self.pending_count_label = QLabel("معاملات معلقة: 0")
        
        status_layout.addWidget(self.total_transfers_label)
        status_layout.addWidget(self.total_amount_label)
        status_layout.addWidget(self.total_profit_label)
        status_layout.addWidget(self.pending_count_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
        transfers_widget.setLayout(layout)
        self.tab_widget.addTab(transfers_widget, "قائمة التحويلات")
        
    def setup_new_transfer_tab(self):
        """Setup new transfer entry tab"""
        new_transfer_widget = QWidget()
        layout = QVBoxLayout()
        
        # Service type section
        service_group = QGroupBox("نوع الخدمة")
        service_layout = QFormLayout()
        
        self.service_type_combo = QComboBox()
        self.service_type_combo.addItem("فودافون كاش", "vodafone_cash")
        self.service_type_combo.addItem("اتصالات كاش", "etisalat_cash")
        self.service_type_combo.addItem("اورانج كاش", "orange_cash")
        self.service_type_combo.addItem("امان كاش", "aman_cash")
        self.service_type_combo.addItem("شحن كروت", "card_charge")
        self.service_type_combo.addItem("تحويل أموال", "money_transfer")
        self.service_type_combo.addItem("أخرى", "other")
        
        self.service_name_input = QLineEdit()
        self.service_name_input.setPlaceholderText("اسم الخدمة التفصيلي...")
        
        service_layout.addRow("نوع الخدمة:", self.service_type_combo)
        service_layout.addRow("اسم الخدمة:", self.service_name_input)
        
        service_group.setLayout(service_layout)
        layout.addWidget(service_group)
        
        # Transaction details section
        transaction_group = QGroupBox("تفاصيل المعاملة")
        transaction_layout = QFormLayout()
        
        # Transaction ID
        self.transaction_id_input = QLineEdit()
        self.transaction_id_input.setReadOnly(True)
        
        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setSuffix(" ج.م")
        
        # Commission
        self.commission_input = QDoubleSpinBox()
        self.commission_input.setMaximum(999999)
        self.commission_input.setDecimals(2)
        self.commission_input.setSuffix(" ج.م")
        
        # Net amount (calculated)
        self.net_amount_label = QLabel("0.00 ج.م")
        self.net_amount_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        # Cost price
        self.cost_price_input = QDoubleSpinBox()
        self.cost_price_input.setMaximum(999999)
        self.cost_price_input.setDecimals(2)
        self.cost_price_input.setSuffix(" ج.م")
        
        # Profit (calculated)
        self.profit_label = QLabel("0.00 ج.م")
        self.profit_label.setStyleSheet("font-weight: bold;")
        
        transaction_layout.addRow("رقم المعاملة:", self.transaction_id_input)
        transaction_layout.addRow("المبلغ:", self.amount_input)
        transaction_layout.addRow("العمولة:", self.commission_input)
        transaction_layout.addRow("صافي المبلغ:", self.net_amount_label)
        transaction_layout.addRow("سعر التكلفة:", self.cost_price_input)
        transaction_layout.addRow("الربح:", self.profit_label)
        
        transaction_group.setLayout(transaction_layout)
        layout.addWidget(transaction_group)
        
        # Customer information section
        customer_group = QGroupBox("معلومات العميل")
        customer_layout = QFormLayout()
        
        self.customer_name_input = QLineEdit()
        self.customer_phone_input = QLineEdit()
        self.recipient_name_input = QLineEdit()
        self.recipient_phone_input = QLineEdit()
        
        customer_layout.addRow("اسم العميل:", self.customer_name_input)
        customer_layout.addRow("رقم هاتف العميل:", self.customer_phone_input)
        customer_layout.addRow("اسم المستلم:", self.recipient_name_input)
        customer_layout.addRow("رقم هاتف المستلم:", self.recipient_phone_input)
        
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # Reference information section
        reference_group = QGroupBox("معلومات المرجع")
        reference_layout = QFormLayout()
        
        self.reference_no_input = QLineEdit()
        self.operator_ref_input = QLineEdit()
        self.verification_code_input = QLineEdit()
        
        self.verified_checkbox = QCheckBox("تم التأكيد")
        
        reference_layout.addRow("رقم المرجع:", self.reference_no_input)
        reference_layout.addRow("مرجع المشغل:", self.operator_ref_input)
        reference_layout.addRow("كود التأكيد:", self.verification_code_input)
        reference_layout.addRow("", self.verified_checkbox)
        
        reference_group.setLayout(reference_layout)
        layout.addWidget(reference_group)
        
        # Notes section
        notes_group = QGroupBox("ملاحظات")
        notes_layout = QVBoxLayout()
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        
        notes_layout.addWidget(self.notes_input)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        self.save_transfer_btn = QPushButton("حفظ المعاملة")
        self.save_and_print_btn = QPushButton("حفظ وطباعة إيصال")
        self.clear_form_btn = QPushButton("مسح النموذج")
        
        actions_layout.addWidget(self.save_transfer_btn)
        actions_layout.addWidget(self.save_and_print_btn)
        actions_layout.addWidget(self.clear_form_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        new_transfer_widget.setLayout(layout)
        self.tab_widget.addTab(new_transfer_widget, "معاملة جديدة")
        
    def setup_statistics_tab(self):
        """Setup statistics tab"""
        stats_widget = QWidget()
        layout = QVBoxLayout()
        
        # Daily statistics
        daily_group = QGroupBox("إحصائيات اليوم")
        daily_layout = QFormLayout()
        
        self.today_count_label = QLabel("0")
        self.today_amount_label = QLabel("0.00 ج.م")
        self.today_profit_label = QLabel("0.00 ج.م")
        self.today_commission_label = QLabel("0.00 ج.م")
        
        daily_layout.addRow("عدد المعاملات:", self.today_count_label)
        daily_layout.addRow("إجمالي المبلغ:", self.today_amount_label)
        daily_layout.addRow("إجمالي الربح:", self.today_profit_label)
        daily_layout.addRow("إجمالي العمولات:", self.today_commission_label)
        
        daily_group.setLayout(daily_layout)
        layout.addWidget(daily_group)
        
        # Service type breakdown
        services_group = QGroupBox("تفصيل الخدمات")
        services_layout = QVBoxLayout()
        
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(4)
        self.services_table.setHorizontalHeaderLabels([
            "نوع الخدمة", "عدد المعاملات", "إجمالي المبلغ", "إجمالي الربح"
        ])
        
        services_layout.addWidget(self.services_table)
        services_group.setLayout(services_layout)
        layout.addWidget(services_group)
        
        layout.addStretch()
        
        stats_widget.setLayout(layout)
        self.tab_widget.addTab(stats_widget, "الإحصائيات")
        
    def setup_connections(self):
        """Setup signal connections"""
        # Transfers list tab
        self.search_input.textChanged.connect(self.filter_transfers)
        self.type_filter.currentTextChanged.connect(self.filter_transfers)
        self.status_filter.currentTextChanged.connect(self.filter_transfers)
        
        self.new_transfer_btn.clicked.connect(self.switch_to_new_transfer_tab)
        self.edit_transfer_btn.clicked.connect(self.edit_selected_transfer)
        self.verify_transfer_btn.clicked.connect(self.verify_selected_transfer)
        self.print_receipt_btn.clicked.connect(self.print_transfer_receipt)
        
        self.transfers_table.doubleClicked.connect(self.edit_selected_transfer)
        self.transfers_table.selectionModel().selectionChanged.connect(self.on_transfer_selection_changed)
        
        # New transfer tab
        self.service_type_combo.currentTextChanged.connect(self.update_service_name)
        self.amount_input.valueChanged.connect(self.calculate_amounts)
        self.commission_input.valueChanged.connect(self.calculate_amounts)
        self.cost_price_input.valueChanged.connect(self.calculate_amounts)
        
        self.save_transfer_btn.clicked.connect(self.save_transfer)
        self.save_and_print_btn.clicked.connect(self.save_and_print_transfer)
        self.clear_form_btn.clicked.connect(self.clear_transfer_form)
        
    def load_data(self):
        """Load transfers data"""
        self.load_transfers()
        self.update_statistics()
        self.generate_new_transaction_id()
        
    def load_transfers(self):
        """Load transfers data"""
        session = get_db_session()
        try:
            transfers = session.query(Transfer).order_by(Transfer.processed_at.desc()).limit(1000).all()
            self.transfers_data = transfers
            
            self.update_transfers_table()
            
        finally:
            session.close()
            
    def update_transfers_table(self):
        """Update transfers table display"""
        self.transfers_table.setRowCount(len(self.transfers_data))
        
        total_amount = 0
        total_profit = 0
        pending_count = 0
        
        for row, transfer in enumerate(self.transfers_data):
            # Calculate totals
            total_amount += transfer.amount
            total_profit += transfer.profit
            if transfer.status == "pending":
                pending_count += 1
            
            # Transaction ID
            self.transfers_table.setItem(row, 0, QTableWidgetItem(transfer.transaction_id))
            
            # Service type
            self.transfers_table.setItem(row, 1, QTableWidgetItem(transfer.service_type_ar))
            
            # Amounts
            self.transfers_table.setItem(row, 2, QTableWidgetItem(format_currency(transfer.amount)))
            self.transfers_table.setItem(row, 3, QTableWidgetItem(format_currency(transfer.commission)))
            self.transfers_table.setItem(row, 4, QTableWidgetItem(format_currency(transfer.net_amount)))
            
            # Customer info
            self.transfers_table.setItem(row, 5, QTableWidgetItem(transfer.customer_name or ""))
            self.transfers_table.setItem(row, 6, QTableWidgetItem(transfer.customer_phone))
            
            # Status with color coding
            status_item = QTableWidgetItem(self.get_status_display(transfer.status))
            status_item.setBackground(self.get_status_color(transfer.status))
            self.transfers_table.setItem(row, 7, status_item)
            
            # Date
            self.transfers_table.setItem(row, 8, QTableWidgetItem(transfer.processed_at.strftime("%Y-%m-%d %H:%M")))
            
            # References
            self.transfers_table.setItem(row, 9, QTableWidgetItem(transfer.operator_ref or ""))
            self.transfers_table.setItem(row, 10, QTableWidgetItem(transfer.reference_no or ""))
            
            # Profit with color coding
            profit_item = QTableWidgetItem(format_currency(transfer.profit))
            if transfer.profit > 0:
                profit_item.setBackground(QColor("#e8f5e8"))  # Light green
            elif transfer.profit < 0:
                profit_item.setBackground(QColor("#ffebee"))  # Light red
            self.transfers_table.setItem(row, 11, profit_item)
            
            # Store transfer ID
            self.transfers_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, transfer.id)
        
        # Update status labels
        self.total_transfers_label.setText(f"إجمالي المعاملات: {len(self.transfers_data)}")
        self.total_amount_label.setText(f"إجمالي المبلغ: {format_currency(total_amount)}")
        self.total_profit_label.setText(f"إجمالي الربح: {format_currency(total_profit)}")
        self.pending_count_label.setText(f"معاملات معلقة: {pending_count}")
        
    def update_statistics(self):
        """Update statistics tab"""
        session = get_db_session()
        try:
            # Today's statistics
            today = datetime.now().date()
            today_transfers = session.query(Transfer).filter(
                Transfer.processed_at >= today
            ).all()
            
            today_count = len(today_transfers)
            today_amount = sum(t.amount for t in today_transfers)
            today_profit = sum(t.profit for t in today_transfers)
            today_commission = sum(t.commission for t in today_transfers)
            
            self.today_count_label.setText(str(today_count))
            self.today_amount_label.setText(format_currency(today_amount))
            self.today_profit_label.setText(format_currency(today_profit))
            self.today_commission_label.setText(format_currency(today_commission))
            
            # Service type breakdown
            service_stats = {}
            for transfer in self.transfers_data:
                service_type = transfer.service_type_ar
                if service_type not in service_stats:
                    service_stats[service_type] = {
                        'count': 0,
                        'amount': 0,
                        'profit': 0
                    }
                service_stats[service_type]['count'] += 1
                service_stats[service_type]['amount'] += transfer.amount
                service_stats[service_type]['profit'] += transfer.profit
            
            self.services_table.setRowCount(len(service_stats))
            for row, (service_type, stats) in enumerate(service_stats.items()):
                self.services_table.setItem(row, 0, QTableWidgetItem(service_type))
                self.services_table.setItem(row, 1, QTableWidgetItem(str(stats['count'])))
                self.services_table.setItem(row, 2, QTableWidgetItem(format_currency(stats['amount'])))
                self.services_table.setItem(row, 3, QTableWidgetItem(format_currency(stats['profit'])))
                
        finally:
            session.close()
            
    def get_status_display(self, status: str) -> str:
        """Get Arabic display text for status"""
        status_map = {
            "pending": "معلقة",
            "completed": "مكتملة",
            "failed": "فاشلة",
            "cancelled": "ملغاة"
        }
        return status_map.get(status, status)
        
    def get_status_color(self, status: str) -> QColor:
        """Get color for status"""
        color_map = {
            "pending": QColor("#fff3e0"),     # Light orange
            "completed": QColor("#e8f5e8"),   # Light green
            "failed": QColor("#ffebee"),      # Light red
            "cancelled": QColor("#f5f5f5")    # Light gray
        }
        return color_map.get(status, QColor("#ffffff"))
        
    def filter_transfers(self):
        """Filter transfers based on search criteria"""
        search_text = self.search_input.text().lower()
        transfer_type = self.type_filter.currentData()
        status = self.status_filter.currentData()
        
        for row in range(self.transfers_table.rowCount()):
            show_row = True
            
            # Search filter
            if search_text:
                transaction_id = self.transfers_table.item(row, 0).text().lower()
                customer_phone = self.transfers_table.item(row, 6).text().lower()
                if search_text not in transaction_id and search_text not in customer_phone:
                    show_row = False
            
            # Type filter
            if transfer_type and show_row:
                transfer_id = self.transfers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                transfer = next((t for t in self.transfers_data if t.id == transfer_id), None)
                if transfer and transfer.type != transfer_type:
                    show_row = False
            
            # Status filter
            if status and show_row:
                transfer_id = self.transfers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                transfer = next((t for t in self.transfers_data if t.id == transfer_id), None)
                if transfer and transfer.status != status:
                    show_row = False
            
            self.transfers_table.setRowHidden(row, not show_row)
            
    def on_transfer_selection_changed(self):
        """Handle transfer selection change"""
        has_selection = bool(self.transfers_table.selectedItems())
        self.edit_transfer_btn.setEnabled(has_selection and self.current_user.has_permission("transfers", "update"))
        self.verify_transfer_btn.setEnabled(has_selection and self.current_user.has_permission("transfers", "update"))
        self.print_receipt_btn.setEnabled(has_selection)
        
    def generate_new_transaction_id(self):
        """Generate new transaction ID"""
        self.transaction_id_input.setText(generate_transaction_id())
        
    def update_service_name(self):
        """Update service name based on selected type"""
        service_type = self.service_type_combo.currentData()
        if service_type and not self.service_name_input.text():
            self.service_name_input.setText(self.service_type_combo.currentText())
            
    def calculate_amounts(self):
        """Calculate net amount and profit"""
        amount = self.amount_input.value()
        commission = self.commission_input.value()
        cost_price = self.cost_price_input.value()
        
        net_amount = amount - commission
        profit = net_amount - cost_price
        
        self.net_amount_label.setText(format_currency(net_amount))
        self.profit_label.setText(format_currency(profit))
        
        # Style profit label
        if profit > 0:
            self.profit_label.setStyleSheet("font-weight: bold; color: #28a745;")
        elif profit < 0:
            self.profit_label.setStyleSheet("font-weight: bold; color: #dc3545;")
        else:
            self.profit_label.setStyleSheet("font-weight: bold; color: #6c757d;")
            
    def switch_to_new_transfer_tab(self):
        """Switch to new transfer tab"""
        self.tab_widget.setCurrentIndex(1)
        self.clear_transfer_form()
        
    def clear_transfer_form(self):
        """Clear new transfer form"""
        self.service_type_combo.setCurrentIndex(0)
        self.service_name_input.clear()
        self.amount_input.setValue(0)
        self.commission_input.setValue(0)
        self.cost_price_input.setValue(0)
        self.customer_name_input.clear()
        self.customer_phone_input.clear()
        self.recipient_name_input.clear()
        self.recipient_phone_input.clear()
        self.reference_no_input.clear()
        self.operator_ref_input.clear()
        self.verification_code_input.clear()
        self.verified_checkbox.setChecked(False)
        self.notes_input.clear()
        self.generate_new_transaction_id()
        
    def save_transfer(self):
        """Save new transfer"""
        if not self.validate_transfer_form():
            return False
        
        try:
            transfer_data = self.get_transfer_form_data()
            
            session = get_db_session()
            try:
                transfer = Transfer(**transfer_data)
                transfer.calculate_profit()
                
                session.add(transfer)
                session.commit()
                
                show_success(self, f"تم حفظ المعاملة رقم {self.transaction_id_input.text()} بنجاح")
                self.load_transfers()
                self.update_statistics()
                self.clear_transfer_form()
                self.tab_widget.setCurrentIndex(0)  # Switch to transfers list
                return True
                
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
                
        except Exception as e:
            logging.error(f"Save transfer error: {e}")
            show_error(self, f"خطأ في حفظ المعاملة:\n{str(e)}")
            return False
            
    def save_and_print_transfer(self):
        """Save transfer and print receipt"""
        if self.save_transfer():
            # Print receipt for the saved transfer
            pass
            
    def validate_transfer_form(self):
        """Validate transfer form data"""
        if not self.service_name_input.text().strip():
            show_error(self, "يرجى إدخال اسم الخدمة")
            return False
        
        if self.amount_input.value() <= 0:
            show_error(self, "يرجى إدخال مبلغ صحيح")
            return False
        
        if not self.customer_phone_input.text().strip():
            show_error(self, "يرجى إدخال رقم هاتف العميل")
            return False
        
        return True
        
    def get_transfer_form_data(self):
        """Get transfer form data"""
        return {
            'transaction_id': self.transaction_id_input.text(),
            'type': self.service_type_combo.currentData(),
            'service_name': self.service_name_input.text().strip(),
            'amount': self.amount_input.value(),
            'commission': self.commission_input.value(),
            'cost_price': self.cost_price_input.value(),
            'customer_name': self.customer_name_input.text().strip() or None,
            'customer_phone': self.customer_phone_input.text().strip(),
            'recipient_name': self.recipient_name_input.text().strip() or None,
            'recipient_phone': self.recipient_phone_input.text().strip() or None,
            'reference_no': self.reference_no_input.text().strip() or None,
            'operator_ref': self.operator_ref_input.text().strip() or None,
            'verification_code': self.verification_code_input.text().strip() or None,
            'verified': "yes" if self.verified_checkbox.isChecked() else "no",
            'notes': self.notes_input.toPlainText().strip() or None,
            'processed_by': self.current_user.id,
            'status': "completed" if self.verified_checkbox.isChecked() else "pending"
        }
        
    def edit_selected_transfer(self):
        """Edit selected transfer"""
        show_error(self, "ميزة تعديل المعاملات قيد التطوير")
        
    def verify_selected_transfer(self):
        """Verify selected transfer"""
        show_error(self, "ميزة تأكيد المعاملات قيد التطوير")
        
    def print_transfer_receipt(self):
        """Print transfer receipt"""
        show_error(self, "ميزة طباعة إيصال التحويل قيد التطوير")
