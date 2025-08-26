from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit,
                            QFormLayout, QDialog, QMessageBox, QGroupBox,
                            QHeaderView, QAbstractItemView, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime

from services.repair_service import RepairService
from services.sales_service import SalesService
from ui.styles import get_stylesheet

class RepairWindow(QMainWindow):
    """Repair service management window"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.repair_service = RepairService()
        self.sales_service = SalesService()
        self.current_repair = None
        
        self.setup_ui()
        self.apply_styles()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("خدمة الصيانة")
        self.setMinimumSize(1200, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("إدارة خدمة الصيانة")
        title_label.setFont(QFont("Noto Sans Arabic", 18, QFont.Weight.Bold))
        title_label.setObjectName("title-label")
        
        # Add new repair button
        self.add_repair_btn = QPushButton("استلام جهاز جديد")
        self.add_repair_btn.clicked.connect(self.add_repair)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_repair_btn)
        
        # Search and filter section
        filter_group = QGroupBox("البحث والفلترة")
        filter_layout = QHBoxLayout()
        
        # Search box
        search_label = QLabel("بحث:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث برقم التذكرة، اسم العميل، أو نوع الجهاز...")
        self.search_input.textChanged.connect(self.filter_repairs)
        
        # Status filter
        status_label = QLabel("الحالة:")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["الكل", "قيد الفحص", "قيد الانتظار", "تم الإصلاح", "غير قابل للإصلاح"])
        self.status_filter.currentTextChanged.connect(self.filter_repairs)
        
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()
        
        filter_group.setLayout(filter_layout)
        
        # Repairs table
        self.repairs_table = QTableWidget()
        self.setup_repairs_table()
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.view_btn = QPushButton("عرض التفاصيل")
        self.view_btn.clicked.connect(self.view_repair)
        self.view_btn.setEnabled(False)
        
        self.edit_btn = QPushButton("تعديل")
        self.edit_btn.clicked.connect(self.edit_repair)
        self.edit_btn.setEnabled(False)
        
        self.update_status_btn = QPushButton("تحديث الحالة")
        self.update_status_btn.clicked.connect(self.update_status)
        self.update_status_btn.setEnabled(False)
        
        self.print_receipt_btn = QPushButton("طباعة إيصال")
        self.print_receipt_btn.clicked.connect(self.print_receipt)
        self.print_receipt_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.view_btn)
        buttons_layout.addWidget(self.edit_btn)
        buttons_layout.addWidget(self.update_status_btn)
        buttons_layout.addWidget(self.print_receipt_btn)
        buttons_layout.addStretch()
        
        # Add layouts to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(filter_group)
        main_layout.addWidget(self.repairs_table)
        main_layout.addLayout(buttons_layout)
        
        central_widget.setLayout(main_layout)
        
        # Connect table selection
        self.repairs_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def setup_repairs_table(self):
        """Setup repairs table"""
        headers = ["رقم التذكرة", "العميل", "نوع الجهاز", "تاريخ الدخول", "الحالة", "التكلفة", "ملاحظات"]
        
        self.repairs_table.setColumnCount(len(headers))
        self.repairs_table.setHorizontalHeaderLabels(headers)
        
        self.repairs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.repairs_table.setAlternatingRowColors(True)
        self.repairs_table.setSortingEnabled(True)
        
        # Resize columns
        header = self.repairs_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(get_stylesheet("light"))
    
    def load_data(self):
        """Load repairs data"""
        try:
            self.load_repairs()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {str(e)}")
    
    def load_repairs(self):
        """Load repairs into table"""
        try:
            repairs = self.repair_service.get_repairs()
            
            self.repairs_table.setRowCount(len(repairs))
            
            for row, repair in enumerate(repairs):
                # Format entry date
                entry_date = repair.entry_date.strftime("%Y-%m-%d") if repair.entry_date else ""
                
                items = [
                    repair.ticket_no,
                    repair.customer.name if repair.customer else "",
                    repair.device_model,
                    entry_date,
                    repair.status,
                    f"{repair.total_cost:.2f}" if repair.total_cost else "0.00",
                    repair.notes[:50] + "..." if repair.notes and len(repair.notes) > 50 else repair.notes or ""
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    item.setData(Qt.ItemDataRole.UserRole, repair.id)
                    
                    # Color coding for status
                    if col == 4:  # Status column
                        if repair.status == "تم الإصلاح":
                            item.setBackground(Qt.GlobalColor.green)
                        elif repair.status == "غير قابل للإصلاح":
                            item.setBackground(Qt.GlobalColor.red)
                        elif repair.status == "قيد الانتظار":
                            item.setBackground(Qt.GlobalColor.yellow)
                    
                    self.repairs_table.setItem(row, col, item)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل الصيانات: {str(e)}")
    
    def filter_repairs(self):
        """Filter repairs based on search criteria"""
        search_text = self.search_input.text().lower()
        status = self.status_filter.currentText()
        
        for row in range(self.repairs_table.rowCount()):
            show_row = True
            
            # Search filter
            if search_text:
                ticket_no = self.repairs_table.item(row, 0).text().lower()
                customer = self.repairs_table.item(row, 1).text().lower()
                device = self.repairs_table.item(row, 2).text().lower()
                if (search_text not in ticket_no and 
                    search_text not in customer and 
                    search_text not in device):
                    show_row = False
            
            # Status filter
            if status != "الكل" and show_row:
                repair_status = self.repairs_table.item(row, 4).text()
                if status != repair_status:
                    show_row = False
            
            self.repairs_table.setRowHidden(row, not show_row)
    
    def on_selection_changed(self):
        """Handle table selection change"""
        selected_rows = self.repairs_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.view_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)
        self.update_status_btn.setEnabled(has_selection)
        self.print_receipt_btn.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            repair_id = self.repairs_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.current_repair = self.repair_service.get_repair_by_id(repair_id)
    
    def add_repair(self):
        """Add new repair"""
        dialog = RepairDialog(self, self.repair_service, self.sales_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_repairs()
    
    def view_repair(self):
        """View repair details"""
        if self.current_repair:
            dialog = RepairViewDialog(self, self.current_repair)
            dialog.exec()
    
    def edit_repair(self):
        """Edit selected repair"""
        if self.current_repair:
            dialog = RepairDialog(self, self.repair_service, self.sales_service, self.current_repair)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_repairs()
    
    def update_status(self):
        """Update repair status"""
        if self.current_repair:
            dialog = StatusUpdateDialog(self, self.current_repair)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_repairs()
    
    def print_receipt(self):
        """Print repair receipt"""
        if self.current_repair:
            QMessageBox.information(self, "طباعة", f"سيتم طباعة إيصال الصيانة رقم: {self.current_repair.ticket_no}")

class RepairDialog(QDialog):
    """Dialog for adding/editing repairs"""
    
    def __init__(self, parent, repair_service, sales_service, repair=None):
        super().__init__(parent)
        self.repair_service = repair_service
        self.sales_service = sales_service
        self.repair = repair
        self.is_edit_mode = repair is not None
        
        self.setup_ui()
        if self.is_edit_mode:
            self.load_repair_data()
    
    def setup_ui(self):
        """Setup dialog UI"""
        title = "تعديل الصيانة" if self.is_edit_mode else "استلام جهاز جديد"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Customer selection
        self.customer_combo = QComboBox()
        self.load_customers()
        
        add_customer_btn = QPushButton("عميل جديد")
        add_customer_btn.clicked.connect(self.add_customer)
        
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(self.customer_combo)
        customer_layout.addWidget(add_customer_btn)
        
        # Device and problem details
        self.device_input = QLineEdit()
        self.problem_input = QTextEdit()
        self.problem_input.setMaximumHeight(100)
        
        # Status and costs
        self.status_combo = QComboBox()
        self.status_combo.addItems(["قيد الفحص", "قيد الانتظار", "تم الإصلاح", "غير قابل للإصلاح"])
        
        self.parts_cost_input = QDoubleSpinBox()
        self.parts_cost_input.setMaximum(999999.99)
        self.parts_cost_input.setDecimals(2)
        
        self.labor_cost_input = QDoubleSpinBox()
        self.labor_cost_input.setMaximum(999999.99)
        self.labor_cost_input.setDecimals(2)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        
        # Add fields to form
        form_layout.addRow("العميل:", customer_layout)
        form_layout.addRow("نوع/موديل الجهاز:", self.device_input)
        form_layout.addRow("وصف المشكلة:", self.problem_input)
        form_layout.addRow("الحالة:", self.status_combo)
        form_layout.addRow("تكلفة القطع:", self.parts_cost_input)
        form_layout.addRow("تكلفة العمالة:", self.labor_cost_input)
        form_layout.addRow("ملاحظات:", self.notes_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("حفظ")
        self.save_btn.clicked.connect(self.save_repair)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_customers(self):
        """Load customers into combo box"""
        try:
            customers = self.sales_service.get_customers()
            self.customer_combo.clear()
            
            for customer in customers:
                self.customer_combo.addItem(customer.name, customer.id)
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل العملاء: {str(e)}")
    
    def add_customer(self):
        """Add new customer"""
        from ui.sales_window import CustomerDialog
        dialog = CustomerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_customers()
    
    def load_repair_data(self):
        """Load existing repair data for editing"""
        if not self.repair:
            return
        
        # Set customer
        if self.repair.customer_id:
            for i in range(self.customer_combo.count()):
                if self.customer_combo.itemData(i) == self.repair.customer_id:
                    self.customer_combo.setCurrentIndex(i)
                    break
        
        self.device_input.setText(self.repair.device_model)
        self.problem_input.setPlainText(self.repair.problem_desc)
        
        # Set status
        status_index = self.status_combo.findText(self.repair.status)
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)
        
        self.parts_cost_input.setValue(self.repair.parts_cost)
        self.labor_cost_input.setValue(self.repair.labor_cost)
        self.notes_input.setPlainText(self.repair.notes or "")
    
    def save_repair(self):
        """Save repair data"""
        try:
            # Validate required fields
            if not self.customer_combo.currentData():
                QMessageBox.warning(self, "تحذير", "يرجى اختيار العميل")
                return
            
            if not self.device_input.text().strip():
                QMessageBox.warning(self, "تحذير", "يرجى إدخال نوع الجهاز")
                return
            
            if not self.problem_input.toPlainText().strip():
                QMessageBox.warning(self, "تحذير", "يرجى إدخال وصف المشكلة")
                return
            
            # Prepare repair data
            repair_data = {
                'customer_id': self.customer_combo.currentData(),
                'device_model': self.device_input.text().strip(),
                'problem_desc': self.problem_input.toPlainText().strip(),
                'status': self.status_combo.currentText(),
                'parts_cost': self.parts_cost_input.value(),
                'labor_cost': self.labor_cost_input.value(),
                'notes': self.notes_input.toPlainText().strip() or None
            }
            
            # Save repair
            if self.is_edit_mode:
                self.repair_service.update_repair(self.repair.id, repair_data)
                QMessageBox.information(self, "نجح", "تم تحديث بيانات الصيانة بنجاح")
            else:
                repair = self.repair_service.create_repair(repair_data, self.parent().current_user.id)
                QMessageBox.information(self, "نجح", f"تم إنشاء تذكرة صيانة رقم: {repair.ticket_no}")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حفظ الصيانة: {str(e)}")

class RepairViewDialog(QDialog):
    """Dialog for viewing repair details"""
    
    def __init__(self, parent, repair):
        super().__init__(parent)
        self.repair = repair
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"تفاصيل الصيانة - {self.repair.ticket_no}")
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(f"تذكرة رقم: {self.repair.ticket_no}")
        title_label.setFont(QFont("Noto Sans Arabic", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Details
        details_text = f"""
        العميل: {self.repair.customer.name if self.repair.customer else 'غير محدد'}
        رقم الهاتف: {self.repair.customer.phone if self.repair.customer and self.repair.customer.phone else 'غير محدد'}
        
        نوع الجهاز: {self.repair.device_model}
        وصف المشكلة: {self.repair.problem_desc}
        
        الحالة: {self.repair.status}
        تاريخ الدخول: {self.repair.entry_date.strftime('%Y-%m-%d %H:%M') if self.repair.entry_date else 'غير محدد'}
        تاريخ الخروج: {self.repair.exit_date.strftime('%Y-%m-%d %H:%M') if self.repair.exit_date else 'لم يتم بعد'}
        
        تكلفة القطع: {self.repair.parts_cost:.2f} جنيه
        تكلفة العمالة: {self.repair.labor_cost:.2f} جنيه
        التكلفة الإجمالية: {self.repair.total_cost:.2f} جنيه
        
        ملاحظات: {self.repair.notes or 'لا توجد ملاحظات'}
        """
        
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        details_label.setStyleSheet("QLabel { padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd; }")
        
        # Close button
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        
        layout.addWidget(title_label)
        layout.addWidget(details_label)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class StatusUpdateDialog(QDialog):
    """Dialog for updating repair status"""
    
    def __init__(self, parent, repair):
        super().__init__(parent)
        self.repair = repair
        self.repair_service = RepairService()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"تحديث حالة الصيانة - {self.repair.ticket_no}")
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        # Current status
        current_label = QLabel(f"الحالة الحالية: {self.repair.status}")
        current_label.setFont(QFont("Noto Sans Arabic", 11, QFont.Weight.Bold))
        
        # New status
        form_layout = QFormLayout()
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["قيد الفحص", "قيد الانتظار", "تم الإصلاح", "غير قابل للإصلاح"])
        
        # Set current status
        current_index = self.status_combo.findText(self.repair.status)
        if current_index >= 0:
            self.status_combo.setCurrentIndex(current_index)
        
        form_layout.addRow("الحالة الجديدة:", self.status_combo)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        update_btn = QPushButton("تحديث")
        update_btn.clicked.connect(self.update_status)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(update_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(current_label)
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def update_status(self):
        """Update repair status"""
        try:
            new_status = self.status_combo.currentText()
            if new_status == self.repair.status:
                QMessageBox.information(self, "تنبيه", "لم يتم تغيير الحالة")
                return
            
            update_data = {'status': new_status}
            
            # Set exit date if status is completed
            if new_status == "تم الإصلاح":
                update_data['exit_date'] = datetime.now()
            
            self.repair_service.update_repair(self.repair.id, update_data)
            QMessageBox.information(self, "نجح", f"تم تحديث الحالة إلى: {new_status}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحديث الحالة: {str(e)}")
