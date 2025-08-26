# -*- coding: utf-8 -*-
"""
Repair service management window
"""

import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                            QLineEdit, QComboBox, QTextEdit, QDateEdit, QDoubleSpinBox,
                            QMessageBox, QHeaderView, QFrame, QGroupBox, QFormLayout,
                            QTabWidget, QSpinBox, QCheckBox, QSplitter, QScrollArea)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from models.user import User
from models.repair import Repair
from models.sales import Customer
from config.database import get_db_session
from ui.dialogs.customer_dialog import CustomerDialog
from services.repair_service import RepairService
from services.print_service import PrintService
from utils.helpers import format_currency, show_error, show_success, generate_ticket_number

class RepairWindow(QMainWindow):
    """Repair service management window"""
    
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.repairs_data = []
        self.customers = []
        self.repair_service = RepairService()
        self.print_service = PrintService()
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("خدمة الصيانة")
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
        
        # Repairs list tab
        self.setup_repairs_tab()
        
        # New repair tab
        self.setup_new_repair_tab()
        
        # Repair details tab
        self.setup_details_tab()
        
    def setup_repairs_tab(self):
        """Setup repairs list tab"""
        repairs_widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Search and filter controls
        search_label = QLabel("البحث:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("البحث في رقم التذكرة، العميل، الجهاز...")
        
        status_label = QLabel("الحالة:")
        self.status_filter = QComboBox()
        self.status_filter.addItem("جميع الحالات", None)
        self.status_filter.addItem("تم الاستلام", "received")
        self.status_filter.addItem("قيد الفحص", "diagnosed")
        self.status_filter.addItem("في انتظار القطع", "waiting_parts")
        self.status_filter.addItem("قيد الإصلاح", "in_progress")
        self.status_filter.addItem("تم الإصلاح", "completed")
        self.status_filter.addItem("تم التسليم", "delivered")
        self.status_filter.addItem("ملغي", "cancelled")
        
        priority_label = QLabel("الأولوية:")
        self.priority_filter = QComboBox()
        self.priority_filter.addItem("جميع الأولويات", None)
        self.priority_filter.addItem("منخفضة", "low")
        self.priority_filter.addItem("عادية", "normal")
        self.priority_filter.addItem("عالية", "high")
        self.priority_filter.addItem("عاجلة", "urgent")
        
        # Action buttons
        self.new_repair_btn = QPushButton("استلام جهاز جديد")
        self.edit_repair_btn = QPushButton("تعديل التذكرة")
        self.print_receipt_btn = QPushButton("طباعة إيصال")
        self.update_status_btn = QPushButton("تحديث الحالة")
        
        # Enable/disable based on permissions
        if not self.current_user.has_permission("repairs", "create"):
            self.new_repair_btn.setEnabled(False)
        if not self.current_user.has_permission("repairs", "update"):
            self.edit_repair_btn.setEnabled(False)
            self.update_status_btn.setEnabled(False)
        
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.search_input)
        toolbar_layout.addWidget(status_label)
        toolbar_layout.addWidget(self.status_filter)
        toolbar_layout.addWidget(priority_label)
        toolbar_layout.addWidget(self.priority_filter)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.new_repair_btn)
        toolbar_layout.addWidget(self.edit_repair_btn)
        toolbar_layout.addWidget(self.print_receipt_btn)
        toolbar_layout.addWidget(self.update_status_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Repairs table
        self.repairs_table = QTableWidget()
        self.repairs_table.setColumnCount(12)
        self.repairs_table.setHorizontalHeaderLabels([
            "رقم التذكرة", "العميل", "الهاتف", "الجهاز", "المشكلة", "الحالة",
            "الأولوية", "تاريخ الاستلام", "تاريخ التسليم المتوقع", "التكلفة",
            "الفني", "الأيام في الخدمة"
        ])
        
        # Configure table
        header = self.repairs_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Customer
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Device
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Problem
        
        self.repairs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.repairs_table.setAlternatingRowColors(True)
        self.repairs_table.setSortingEnabled(True)
        
        layout.addWidget(self.repairs_table)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.total_repairs_label = QLabel("إجمالي التذاكر: 0")
        self.pending_repairs_label = QLabel("قيد الإصلاح: 0")
        self.overdue_repairs_label = QLabel("متأخرة: 0")
        self.completed_today_label = QLabel("مكتملة اليوم: 0")
        
        status_layout.addWidget(self.total_repairs_label)
        status_layout.addWidget(self.pending_repairs_label)
        status_layout.addWidget(self.overdue_repairs_label)
        status_layout.addWidget(self.completed_today_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
        repairs_widget.setLayout(layout)
        self.tab_widget.addTab(repairs_widget, "قائمة الصيانة")
        
    def setup_new_repair_tab(self):
        """Setup new repair entry tab"""
        new_repair_widget = QWidget()
        
        # Scroll area for form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        form_widget = QWidget()
        layout = QVBoxLayout()
        
        # Customer section
        customer_group = QGroupBox("معلومات العميل")
        customer_layout = QFormLayout()
        
        # Customer selection
        customer_selection_layout = QHBoxLayout()
        self.customer_combo = QComboBox()
        self.add_customer_btn = QPushButton("عميل جديد")
        
        customer_selection_layout.addWidget(self.customer_combo, 2)
        customer_selection_layout.addWidget(self.add_customer_btn)
        
        customer_layout.addRow("العميل:", customer_selection_layout)
        
        # Customer details (read-only)
        self.customer_phone_display = QLabel("-")
        self.customer_address_display = QLabel("-")
        
        customer_layout.addRow("الهاتف:", self.customer_phone_display)
        customer_layout.addRow("العنوان:", self.customer_address_display)
        
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # Device section
        device_group = QGroupBox("معلومات الجهاز")
        device_layout = QFormLayout()
        
        self.device_model_input = QLineEdit()
        self.device_brand_input = QLineEdit()
        self.device_color_input = QLineEdit()
        self.device_imei_input = QLineEdit()
        
        device_layout.addRow("موديل الجهاز:", self.device_model_input)
        device_layout.addRow("الماركة:", self.device_brand_input)
        device_layout.addRow("اللون:", self.device_color_input)
        device_layout.addRow("IMEI:", self.device_imei_input)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # Repair details section
        repair_group = QGroupBox("تفاصيل الصيانة")
        repair_layout = QFormLayout()
        
        # Ticket number
        self.ticket_number_input = QLineEdit()
        self.ticket_number_input.setReadOnly(True)
        
        # Problem description
        self.problem_desc_input = QTextEdit()
        self.problem_desc_input.setMaximumHeight(100)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["منخفضة", "عادية", "عالية", "عاجلة"])
        self.priority_combo.setCurrentText("عادية")
        
        # Promised date
        self.promised_date_input = QDateEdit()
        self.promised_date_input.setDate(QDate.currentDate().addDays(3))
        self.promised_date_input.setCalendarPopup(True)
        
        # Warranty
        self.warranty_days_input = QSpinBox()
        self.warranty_days_input.setMaximum(365)
        self.warranty_days_input.setValue(30)
        
        self.warranty_void_checkbox = QCheckBox("الجهاز مكسور الضمان")
        
        repair_layout.addRow("رقم التذكرة:", self.ticket_number_input)
        repair_layout.addRow("وصف المشكلة:", self.problem_desc_input)
        repair_layout.addRow("الأولوية:", self.priority_combo)
        repair_layout.addRow("تاريخ التسليم المتوقع:", self.promised_date_input)
        repair_layout.addRow("أيام الضمان:", self.warranty_days_input)
        repair_layout.addRow("", self.warranty_void_checkbox)
        
        repair_group.setLayout(repair_layout)
        layout.addWidget(repair_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        self.save_repair_btn = QPushButton("حفظ التذكرة")
        self.save_and_print_btn = QPushButton("حفظ وطباعة إيصال")
        self.clear_form_btn = QPushButton("مسح النموذج")
        
        actions_layout.addWidget(self.save_repair_btn)
        actions_layout.addWidget(self.save_and_print_btn)
        actions_layout.addWidget(self.clear_form_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        form_widget.setLayout(layout)
        scroll_area.setWidget(form_widget)
        
        new_repair_layout = QVBoxLayout()
        new_repair_layout.addWidget(scroll_area)
        new_repair_widget.setLayout(new_repair_layout)
        
        self.tab_widget.addTab(new_repair_widget, "استلام جهاز جديد")
        
    def setup_details_tab(self):
        """Setup repair details/edit tab"""
        details_widget = QWidget()
        
        # This tab will be populated when a repair is selected
        layout = QVBoxLayout()
        
        # Placeholder
        placeholder_label = QLabel("اختر تذكرة صيانة من القائمة لعرض التفاصيل")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("color: #6c757d; font-size: 14px;")
        
        layout.addWidget(placeholder_label)
        
        details_widget.setLayout(layout)
        self.tab_widget.addTab(details_widget, "تفاصيل التذكرة")
        
    def setup_connections(self):
        """Setup signal connections"""
        # Repairs list tab
        self.search_input.textChanged.connect(self.filter_repairs)
        self.status_filter.currentTextChanged.connect(self.filter_repairs)
        self.priority_filter.currentTextChanged.connect(self.filter_repairs)
        
        self.new_repair_btn.clicked.connect(self.switch_to_new_repair_tab)
        self.edit_repair_btn.clicked.connect(self.edit_selected_repair)
        self.print_receipt_btn.clicked.connect(self.print_repair_receipt)
        self.update_status_btn.clicked.connect(self.update_repair_status)
        
        self.repairs_table.doubleClicked.connect(self.edit_selected_repair)
        self.repairs_table.selectionModel().selectionChanged.connect(self.on_repair_selection_changed)
        
        # New repair tab
        self.customer_combo.currentTextChanged.connect(self.on_customer_changed)
        self.add_customer_btn.clicked.connect(self.add_customer)
        
        self.save_repair_btn.clicked.connect(self.save_repair)
        self.save_and_print_btn.clicked.connect(self.save_and_print_repair)
        self.clear_form_btn.clicked.connect(self.clear_repair_form)
        
    def load_data(self):
        """Load all data"""
        self.load_customers()
        self.load_repairs()
        self.generate_new_ticket_number()
        
    def load_customers(self):
        """Load customers data"""
        session = get_db_session()
        try:
            customers = session.query(Customer).all()
            self.customers = customers
            
            # Update customer combo
            self.customer_combo.clear()
            self.customer_combo.addItem("اختر العميل...", None)
            
            for customer in customers:
                display_text = f"{customer.name} - {customer.phone}"
                self.customer_combo.addItem(display_text, customer.id)
                
        finally:
            session.close()
            
    def load_repairs(self):
        """Load repairs data"""
        session = get_db_session()
        try:
            repairs = session.query(Repair).join(Customer).order_by(Repair.entry_date.desc()).all()
            self.repairs_data = repairs
            
            self.update_repairs_table()
            self.update_statistics()
            
        finally:
            session.close()
            
    def update_repairs_table(self):
        """Update repairs table display"""
        self.repairs_table.setRowCount(len(self.repairs_data))
        
        for row, repair in enumerate(self.repairs_data):
            # Ticket number
            self.repairs_table.setItem(row, 0, QTableWidgetItem(repair.ticket_no))
            
            # Customer info
            self.repairs_table.setItem(row, 1, QTableWidgetItem(repair.customer.name))
            self.repairs_table.setItem(row, 2, QTableWidgetItem(repair.customer.phone or ""))
            
            # Device info
            device_info = f"{repair.device_brand} {repair.device_model}" if repair.device_brand else repair.device_model
            self.repairs_table.setItem(row, 3, QTableWidgetItem(device_info))
            
            # Problem (truncated)
            problem_text = repair.problem_desc[:50] + "..." if len(repair.problem_desc) > 50 else repair.problem_desc
            self.repairs_table.setItem(row, 4, QTableWidgetItem(problem_text))
            
            # Status with color coding
            status_item = QTableWidgetItem(self.get_status_display(repair.status))
            status_item.setBackground(self.get_status_color(repair.status))
            self.repairs_table.setItem(row, 5, status_item)
            
            # Priority with color coding
            priority_item = QTableWidgetItem(self.get_priority_display(repair.priority))
            priority_item.setBackground(self.get_priority_color(repair.priority))
            self.repairs_table.setItem(row, 6, priority_item)
            
            # Dates
            self.repairs_table.setItem(row, 7, QTableWidgetItem(repair.entry_date.strftime("%Y-%m-%d")))
            promised_date = repair.promised_date.strftime("%Y-%m-%d") if repair.promised_date else "-"
            self.repairs_table.setItem(row, 8, QTableWidgetItem(promised_date))
            
            # Cost
            total_cost = repair.parts_cost + repair.labor_cost
            self.repairs_table.setItem(row, 9, QTableWidgetItem(format_currency(total_cost)))
            
            # Technician
            tech_name = repair.technician.name if repair.technician else "-"
            self.repairs_table.setItem(row, 10, QTableWidgetItem(tech_name))
            
            # Days in service
            days_in_service = repair.days_in_service
            days_item = QTableWidgetItem(str(days_in_service))
            if repair.is_overdue:
                days_item.setBackground(QColor("#ffebee"))  # Light red
            self.repairs_table.setItem(row, 11, days_item)
            
            # Store repair ID
            self.repairs_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, repair.id)
            
    def update_statistics(self):
        """Update statistics labels"""
        total_repairs = len(self.repairs_data)
        pending_repairs = len([r for r in self.repairs_data if r.status not in ["completed", "delivered", "cancelled"]])
        overdue_repairs = len([r for r in self.repairs_data if r.is_overdue])
        completed_today = len([r for r in self.repairs_data if r.completed_date and r.completed_date.date() == datetime.now().date()])
        
        self.total_repairs_label.setText(f"إجمالي التذاكر: {total_repairs}")
        self.pending_repairs_label.setText(f"قيد الإصلاح: {pending_repairs}")
        self.overdue_repairs_label.setText(f"متأخرة: {overdue_repairs}")
        self.completed_today_label.setText(f"مكتملة اليوم: {completed_today}")
        
    def get_status_display(self, status: str) -> str:
        """Get Arabic display text for status"""
        status_map = {
            "received": "تم الاستلام",
            "diagnosed": "قيد الفحص",
            "waiting_parts": "في انتظار القطع",
            "in_progress": "قيد الإصلاح",
            "completed": "تم الإصلاح",
            "delivered": "تم التسليم",
            "cancelled": "ملغي"
        }
        return status_map.get(status, status)
        
    def get_status_color(self, status: str) -> QColor:
        """Get color for status"""
        color_map = {
            "received": QColor("#e3f2fd"),      # Light blue
            "diagnosed": QColor("#fff3e0"),     # Light orange
            "waiting_parts": QColor("#fce4ec"), # Light pink
            "in_progress": QColor("#e8f5e8"),   # Light green
            "completed": QColor("#e8f5e8"),     # Light green
            "delivered": QColor("#f3e5f5"),     # Light purple
            "cancelled": QColor("#ffebee")      # Light red
        }
        return color_map.get(status, QColor("#ffffff"))
        
    def get_priority_display(self, priority: str) -> str:
        """Get Arabic display text for priority"""
        priority_map = {
            "low": "منخفضة",
            "normal": "عادية",
            "high": "عالية",
            "urgent": "عاجلة"
        }
        return priority_map.get(priority, priority)
        
    def get_priority_color(self, priority: str) -> QColor:
        """Get color for priority"""
        color_map = {
            "low": QColor("#e8f5e8"),      # Light green
            "normal": QColor("#e3f2fd"),   # Light blue
            "high": QColor("#fff3e0"),     # Light orange
            "urgent": QColor("#ffebee")    # Light red
        }
        return color_map.get(priority, QColor("#ffffff"))
        
    def filter_repairs(self):
        """Filter repairs based on search criteria"""
        search_text = self.search_input.text().lower()
        status = self.status_filter.currentData()
        priority = self.priority_filter.currentData()
        
        for row in range(self.repairs_table.rowCount()):
            show_row = True
            
            # Search filter
            if search_text:
                ticket_no = self.repairs_table.item(row, 0).text().lower()
                customer = self.repairs_table.item(row, 1).text().lower()
                device = self.repairs_table.item(row, 3).text().lower()
                problem = self.repairs_table.item(row, 4).text().lower()
                
                if not any(search_text in text for text in [ticket_no, customer, device, problem]):
                    show_row = False
            
            # Status filter
            if status and show_row:
                repair_id = self.repairs_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                repair = next((r for r in self.repairs_data if r.id == repair_id), None)
                if repair and repair.status != status:
                    show_row = False
            
            # Priority filter
            if priority and show_row:
                repair_id = self.repairs_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                repair = next((r for r in self.repairs_data if r.id == repair_id), None)
                if repair and repair.priority != priority:
                    show_row = False
            
            self.repairs_table.setRowHidden(row, not show_row)
            
    def on_repair_selection_changed(self):
        """Handle repair selection change"""
        has_selection = bool(self.repairs_table.selectedItems())
        self.edit_repair_btn.setEnabled(has_selection and self.current_user.has_permission("repairs", "update"))
        self.print_receipt_btn.setEnabled(has_selection)
        self.update_status_btn.setEnabled(has_selection and self.current_user.has_permission("repairs", "update"))
        
    def on_customer_changed(self):
        """Handle customer selection change"""
        customer_id = self.customer_combo.currentData()
        
        if customer_id:
            customer = next((c for c in self.customers if c.id == customer_id), None)
            if customer:
                self.customer_phone_display.setText(customer.phone or "-")
                self.customer_address_display.setText(customer.address or "-")
            else:
                self.customer_phone_display.setText("-")
                self.customer_address_display.setText("-")
        else:
            self.customer_phone_display.setText("-")
            self.customer_address_display.setText("-")
            
    def generate_new_ticket_number(self):
        """Generate new ticket number"""
        self.ticket_number_input.setText(generate_ticket_number())
        
    def switch_to_new_repair_tab(self):
        """Switch to new repair tab"""
        self.tab_widget.setCurrentIndex(1)
        self.clear_repair_form()
        
    def clear_repair_form(self):
        """Clear new repair form"""
        self.customer_combo.setCurrentIndex(0)
        self.device_model_input.clear()
        self.device_brand_input.clear()
        self.device_color_input.clear()
        self.device_imei_input.clear()
        self.problem_desc_input.clear()
        self.priority_combo.setCurrentText("عادية")
        self.promised_date_input.setDate(QDate.currentDate().addDays(3))
        self.warranty_days_input.setValue(30)
        self.warranty_void_checkbox.setChecked(False)
        self.generate_new_ticket_number()
        
    def add_customer(self):
        """Add new customer"""
        dialog = CustomerDialog(self, self.current_user)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.load_customers()
            show_success(self, "تم إضافة العميل بنجاح")
            
    def save_repair(self):
        """Save new repair"""
        if not self.validate_repair_form():
            return False
        
        try:
            repair_data = self.get_repair_form_data()
            repair_id = self.repair_service.create_repair(repair_data, self.current_user.id)
            
            if repair_id:
                show_success(self, f"تم حفظ تذكرة الصيانة رقم {self.ticket_number_input.text()} بنجاح")
                self.load_repairs()
                self.clear_repair_form()
                self.tab_widget.setCurrentIndex(0)  # Switch to repairs list
                return True
            else:
                show_error(self, "فشل في حفظ تذكرة الصيانة")
                return False
                
        except Exception as e:
            logging.error(f"Save repair error: {e}")
            show_error(self, f"خطأ في حفظ تذكرة الصيانة:\n{str(e)}")
            return False
            
    def save_and_print_repair(self):
        """Save repair and print receipt"""
        if self.save_repair():
            # Find the saved repair and print receipt
            # This would need the repair ID from save_repair
            pass
            
    def validate_repair_form(self):
        """Validate repair form data"""
        if not self.customer_combo.currentData():
            show_error(self, "يرجى اختيار العميل")
            return False
        
        if not self.device_model_input.text().strip():
            show_error(self, "يرجى إدخال موديل الجهاز")
            return False
        
        if not self.problem_desc_input.toPlainText().strip():
            show_error(self, "يرجى وصف المشكلة")
            return False
        
        return True
        
    def get_repair_form_data(self):
        """Get repair form data"""
        priority_map = {
            "منخفضة": "low",
            "عادية": "normal",
            "عالية": "high",
            "عاجلة": "urgent"
        }
        
        return {
            'ticket_no': self.ticket_number_input.text(),
            'customer_id': self.customer_combo.currentData(),
            'device_model': self.device_model_input.text().strip(),
            'device_brand': self.device_brand_input.text().strip() or None,
            'device_color': self.device_color_input.text().strip() or None,
            'device_imei': self.device_imei_input.text().strip() or None,
            'problem_desc': self.problem_desc_input.toPlainText().strip(),
            'priority': priority_map[self.priority_combo.currentText()],
            'promised_date': self.promised_date_input.date().toPython(),
            'warranty_days': self.warranty_days_input.value(),
            'is_warranty_void': self.warranty_void_checkbox.isChecked()
        }
        
    def edit_selected_repair(self):
        """Edit selected repair"""
        selected_items = self.repairs_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار تذكرة للتعديل")
            return
        
        # This would open a detailed edit dialog or populate the details tab
        show_error(self, "ميزة تعديل تذاكر الصيانة قيد التطوير")
        
    def print_repair_receipt(self):
        """Print repair receipt"""
        selected_items = self.repairs_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار تذكرة للطباعة")
            return
        
        row = selected_items[0].row()
        repair_id = self.repairs_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        session = get_db_session()
        try:
            repair = session.query(Repair).get(repair_id)
            if repair:
                self.print_service.print_repair_receipt(repair)
                show_success(self, "تم إرسال إيصال الصيانة للطباعة")
        except Exception as e:
            logging.error(f"Print repair receipt error: {e}")
            show_error(self, f"خطأ في طباعة إيصال الصيانة:\n{str(e)}")
        finally:
            session.close()
            
    def update_repair_status(self):
        """Update repair status"""
        show_error(self, "ميزة تحديث حالة الصيانة قيد التطوير")
