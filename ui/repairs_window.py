# -*- coding: utf-8 -*-
"""
Repairs management window for Al-Hussiny Mobile Shop POS System
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox,
                            QDoubleSpinBox, QTextEdit, QTableWidget, QTableWidgetItem,
                            QHeaderView, QAbstractItemView, QMessageBox, QDialog,
                            QFormLayout, QDialogButtonBox, QFrame, QDateEdit,
                            QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
import logging
from datetime import datetime

from .base_window import BaseWindow
from .widgets.data_table import DataTableWidget
from .dialogs.repair_dialog import RepairDialog
from config import Config

logger = logging.getLogger(__name__)

class RepairsWindow(BaseWindow):
    """Repairs management window"""
    
    def __init__(self, db_manager, user_data):
        super().__init__(db_manager, user_data)
        self.setup_repairs()
        self.refresh_data()
    
    def setup_repairs(self):
        """Setup repairs interface"""
        self.set_title("إدارة الصيانة - محل الحسيني")
        self.setMinimumSize(1400, 900)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_layout.addWidget(splitter)
        
        # Left panel - Repairs list
        self.setup_repairs_panel(splitter)
        
        # Right panel - Transfers
        self.setup_transfers_panel(splitter)
    
    def setup_repairs_panel(self, splitter):
        """Setup repairs list panel"""
        repairs_widget = QWidget()
        repairs_layout = QVBoxLayout(repairs_widget)
        
        # Title
        title_label = QLabel("قائمة الصيانات")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        repairs_layout.addWidget(title_label)
        
        # Toolbar
        self.setup_repairs_toolbar(repairs_layout)
        
        # Filters
        self.setup_repairs_filters(repairs_layout)
        
        # Repairs table
        self.setup_repairs_table(repairs_layout)
        
        # Statistics
        self.setup_repairs_statistics(repairs_layout)
        
        splitter.addWidget(repairs_widget)
    
    def setup_repairs_toolbar(self, layout):
        """Setup repairs toolbar"""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_frame.setMaximumHeight(60)
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        
        # New repair button
        if self.has_permission("repairs"):
            self.new_repair_btn = QPushButton("تذكرة صيانة جديدة")
            self.new_repair_btn.setStyleSheet("""
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
            self.new_repair_btn.clicked.connect(self.new_repair)
            toolbar_layout.addWidget(self.new_repair_btn)
        
        # Edit repair button
        if self.has_permission("repairs"):
            self.edit_repair_btn = QPushButton("تعديل التذكرة")
            self.edit_repair_btn.setStyleSheet("""
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
            self.edit_repair_btn.clicked.connect(self.edit_repair)
            self.edit_repair_btn.setEnabled(False)
            toolbar_layout.addWidget(self.edit_repair_btn)
        
        # Update status button
        if self.has_permission("repairs"):
            self.update_status_btn = QPushButton("تحديث الحالة")
            self.update_status_btn.setStyleSheet("""
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
            self.update_status_btn.clicked.connect(self.update_repair_status)
            self.update_status_btn.setEnabled(False)
            toolbar_layout.addWidget(self.update_status_btn)
        
        # Print receipt button
        self.print_receipt_btn = QPushButton("طباعة الإيصال")
        self.print_receipt_btn.clicked.connect(self.print_receipt)
        self.print_receipt_btn.setEnabled(False)
        toolbar_layout.addWidget(self.print_receipt_btn)
        
        toolbar_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("تحديث")
        self.refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(toolbar_frame)
    
    def setup_repairs_filters(self, layout):
        """Setup repairs filters"""
        filters_frame = QFrame()
        filters_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        filters_frame.setMaximumHeight(100)
        
        filters_layout = QGridLayout(filters_frame)
        
        # Date range
        filters_layout.addWidget(QLabel("من تاريخ:"), 0, 0)
        self.repairs_date_from = QDateEdit()
        self.repairs_date_from.setDate(QDate.currentDate().addDays(-30))
        self.repairs_date_from.setCalendarPopup(True)
        self.repairs_date_from.dateChanged.connect(self.filter_repairs)
        filters_layout.addWidget(self.repairs_date_from, 0, 1)
        
        filters_layout.addWidget(QLabel("إلى تاريخ:"), 0, 2)
        self.repairs_date_to = QDateEdit()
        self.repairs_date_to.setDate(QDate.currentDate())
        self.repairs_date_to.setCalendarPopup(True)
        self.repairs_date_to.dateChanged.connect(self.filter_repairs)
        filters_layout.addWidget(self.repairs_date_to, 0, 3)
        
        # Status filter
        filters_layout.addWidget(QLabel("الحالة:"), 1, 0)
        self.status_combo = QComboBox()
        self.status_combo.addItem("جميع الحالات", "")
        for status in Config.REPAIR_STATUSES:
            self.status_combo.addItem(status, status)
        self.status_combo.currentTextChanged.connect(self.filter_repairs)
        filters_layout.addWidget(self.status_combo, 1, 1)
        
        # Search
        filters_layout.addWidget(QLabel("البحث:"), 1, 2)
        self.repairs_search_edit = QLineEdit()
        self.repairs_search_edit.setPlaceholderText("رقم التذكرة أو اسم العميل أو نوع الجهاز...")
        self.repairs_search_edit.textChanged.connect(self.filter_repairs)
        filters_layout.addWidget(self.repairs_search_edit, 1, 3)
        
        layout.addWidget(filters_frame)
    
    def setup_repairs_table(self, layout):
        """Setup repairs table"""
        self.repairs_table = DataTableWidget()
        self.repairs_table.setColumns([
            "رقم التذكرة", "العميل", "الهاتف", "نوع الجهاز", 
            "المشكلة", "الحالة", "تاريخ الدخول", "التكلفة", "الفني"
        ])
        
        # Connect selection signal
        self.repairs_table.itemSelectionChanged.connect(self.on_repair_selection_changed)
        self.repairs_table.itemDoubleClicked.connect(self.edit_repair)
        
        layout.addWidget(self.repairs_table)
    
    def setup_repairs_statistics(self, layout):
        """Setup repairs statistics"""
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        stats_frame.setMaximumHeight(60)
        
        stats_layout = QHBoxLayout(stats_frame)
        
        self.total_repairs_label = QLabel("إجمالي التذاكر: 0")
        self.pending_repairs_label = QLabel("قيد الإنجاز: 0")
        self.completed_repairs_label = QLabel("مكتملة: 0")
        self.total_revenue_label = QLabel("إجمالي الإيرادات: 0 ج.م")
        
        stats_layout.addWidget(self.total_repairs_label)
        stats_layout.addWidget(self.pending_repairs_label)
        stats_layout.addWidget(self.completed_repairs_label)
        stats_layout.addWidget(self.total_revenue_label)
        stats_layout.addStretch()
        
        layout.addWidget(stats_frame)
    
    def setup_transfers_panel(self, splitter):
        """Setup transfers panel"""
        transfers_widget = QWidget()
        transfers_layout = QVBoxLayout(transfers_widget)
        
        # Title
        title_label = QLabel("تحويلات الرصيد")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        transfers_layout.addWidget(title_label)
        
        # Transfers toolbar
        self.setup_transfers_toolbar(transfers_layout)
        
        # Transfers filters
        self.setup_transfers_filters(transfers_layout)
        
        # Transfers table
        self.setup_transfers_table(transfers_layout)
        
        # Transfers statistics
        self.setup_transfers_statistics(transfers_layout)
        
        splitter.addWidget(transfers_widget)
        
        # Set splitter proportions
        splitter.setSizes([800, 600])
    
    def setup_transfers_toolbar(self, layout):
        """Setup transfers toolbar"""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_frame.setMaximumHeight(60)
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        
        # New transfer button
        if self.has_permission("repairs"):
            self.new_transfer_btn = QPushButton("تحويل جديد")
            self.new_transfer_btn.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #117a8b;
                }
            """)
            self.new_transfer_btn.clicked.connect(self.new_transfer)
            toolbar_layout.addWidget(self.new_transfer_btn)
        
        toolbar_layout.addStretch()
        
        layout.addWidget(toolbar_frame)
    
    def setup_transfers_filters(self, layout):
        """Setup transfers filters"""
        filters_frame = QFrame()
        filters_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        filters_frame.setMaximumHeight(80)
        
        filters_layout = QHBoxLayout(filters_frame)
        
        # Type filter
        filters_layout.addWidget(QLabel("النوع:"))
        self.transfer_type_combo = QComboBox()
        self.transfer_type_combo.addItem("جميع الأنواع", "")
        for transfer_type in Config.TRANSFER_TYPES:
            self.transfer_type_combo.addItem(transfer_type, transfer_type)
        self.transfer_type_combo.currentTextChanged.connect(self.filter_transfers)
        filters_layout.addWidget(self.transfer_type_combo)
        
        # Date filter
        filters_layout.addWidget(QLabel("من تاريخ:"))
        self.transfers_date_from = QDateEdit()
        self.transfers_date_from.setDate(QDate.currentDate().addDays(-7))
        self.transfers_date_from.setCalendarPopup(True)
        self.transfers_date_from.dateChanged.connect(self.filter_transfers)
        filters_layout.addWidget(self.transfers_date_from)
        
        filters_layout.addWidget(QLabel("إلى تاريخ:"))
        self.transfers_date_to = QDateEdit()
        self.transfers_date_to.setDate(QDate.currentDate())
        self.transfers_date_to.setCalendarPopup(True)
        self.transfers_date_to.dateChanged.connect(self.filter_transfers)
        filters_layout.addWidget(self.transfers_date_to)
        
        filters_layout.addStretch()
        
        layout.addWidget(filters_frame)
    
    def setup_transfers_table(self, layout):
        """Setup transfers table"""
        self.transfers_table = DataTableWidget()
        self.transfers_table.setColumns([
            "النوع", "المبلغ", "من حساب", "إلى حساب", "رقم العملية", "التاريخ", "المستخدم"
        ])
        
        layout.addWidget(self.transfers_table)
    
    def setup_transfers_statistics(self, layout):
        """Setup transfers statistics"""
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        stats_frame.setMaximumHeight(60)
        
        stats_layout = QHBoxLayout(stats_frame)
        
        self.total_transfers_label = QLabel("إجمالي التحويلات: 0")
        self.total_transfer_amount_label = QLabel("إجمالي المبلغ: 0 ج.م")
        
        stats_layout.addWidget(self.total_transfers_label)
        stats_layout.addWidget(self.total_transfer_amount_label)
        stats_layout.addStretch()
        
        layout.addWidget(stats_frame)
    
    def refresh_data(self):
        """Refresh repairs and transfers data"""
        try:
            session = self.db_manager.get_session()
            self.load_repairs(session)
            self.load_transfers(session)
            self.update_repairs_statistics(session)
            self.update_transfers_statistics(session)
            self.update_status("تم تحديث بيانات الصيانة والتحويلات")
        except Exception as e:
            self.logger.error(f"خطأ في تحديث بيانات الصيانة: {e}")
            self.show_message(f"خطأ في تحديث البيانات: {str(e)}", "error")
        finally:
            if 'session' in locals():
                session.close()
    
    def load_repairs(self, session):
        """Load repairs into table"""
        from models import Repair
        
        # Get filter values
        date_from = self.repairs_date_from.date().toPython()
        date_to = self.repairs_date_to.date().toPython()
        status = self.status_combo.currentData()
        search_text = self.repairs_search_edit.text().strip()
        
        # Build query
        query = session.query(Repair)
        
        # Date filter
        date_from_dt = datetime.combine(date_from, datetime.min.time())
        date_to_dt = datetime.combine(date_to, datetime.max.time())
        query = query.filter(Repair.entry_date >= date_from_dt, Repair.entry_date <= date_to_dt)
        
        # Status filter
        if status:
            query = query.filter_by(status=status)
        
        # Search filter
        if search_text:
            query = query.filter(
                (Repair.ticket_no.contains(search_text)) |
                (Repair.device_model.contains(search_text)) |
                (Repair.problem_desc.contains(search_text)) |
                (Repair.customer.has(name=search_text))
            )
        
        # Get repairs
        repairs = query.order_by(Repair.entry_date.desc()).all()
        
        # Populate table
        data = []
        for repair in repairs:
            customer_name = repair.customer.name if repair.customer else "غير محدد"
            customer_phone = repair.customer.phone if repair.customer and repair.customer.phone else ""
            data.append([
                repair.ticket_no,
                customer_name,
                customer_phone,
                repair.device_model,
                repair.problem_desc[:50] + "..." if len(repair.problem_desc) > 50 else repair.problem_desc,
                repair.status,
                repair.entry_date.strftime("%Y-%m-%d"),
                f"{repair.total_cost:.2f}",
                repair.user.name if repair.user else ""
            ])
        
        self.repairs_table.setData(data)
        self.current_repairs = repairs
    
    def load_transfers(self, session):
        """Load transfers into table"""
        from models import Transfer
        
        # Get filter values
        date_from = self.transfers_date_from.date().toPython()
        date_to = self.transfers_date_to.date().toPython()
        transfer_type = self.transfer_type_combo.currentData()
        
        # Build query
        query = session.query(Transfer)
        
        # Date filter
        date_from_dt = datetime.combine(date_from, datetime.min.time())
        date_to_dt = datetime.combine(date_to, datetime.max.time())
        query = query.filter(Transfer.date >= date_from_dt, Transfer.date <= date_to_dt)
        
        # Type filter
        if transfer_type:
            query = query.filter_by(type=transfer_type)
        
        # Get transfers
        transfers = query.order_by(Transfer.date.desc()).all()
        
        # Populate table
        data = []
        for transfer in transfers:
            data.append([
                transfer.type,
                f"{transfer.amount:.2f}",
                transfer.from_account or "",
                transfer.to_account,
                transfer.reference_id or "",
                transfer.date.strftime("%Y-%m-%d %H:%M"),
                transfer.user.name if transfer.user else ""
            ])
        
        self.transfers_table.setData(data)
        self.current_transfers = transfers
    
    def update_repairs_statistics(self, session):
        """Update repairs statistics"""
        if hasattr(self, 'current_repairs'):
            total_repairs = len(self.current_repairs)
            pending_repairs = sum(1 for r in self.current_repairs if not r.is_completed)
            completed_repairs = sum(1 for r in self.current_repairs if r.is_completed)
            total_revenue = sum(r.total_cost for r in self.current_repairs if r.is_completed)
            
            self.total_repairs_label.setText(f"إجمالي التذاكر: {total_repairs}")
            self.pending_repairs_label.setText(f"قيد الإنجاز: {pending_repairs}")
            self.completed_repairs_label.setText(f"مكتملة: {completed_repairs}")
            self.total_revenue_label.setText(f"إجمالي الإيرادات: {total_revenue:.2f} ج.م")
    
    def update_transfers_statistics(self, session):
        """Update transfers statistics"""
        if hasattr(self, 'current_transfers'):
            total_transfers = len(self.current_transfers)
            total_amount = sum(t.amount for t in self.current_transfers)
            
            self.total_transfers_label.setText(f"إجمالي التحويلات: {total_transfers}")
            self.total_transfer_amount_label.setText(f"إجمالي المبلغ: {total_amount:.2f} ج.م")
    
    def filter_repairs(self):
        """Filter repairs based on current settings"""
        self.refresh_data()
    
    def filter_transfers(self):
        """Filter transfers based on current settings"""
        self.refresh_data()
    
    def on_repair_selection_changed(self):
        """Handle repair selection change"""
        selected_rows = self.repairs_table.get_selected_rows()
        has_selection = len(selected_rows) > 0
        
        if self.has_permission("repairs"):
            self.edit_repair_btn.setEnabled(has_selection)
            self.update_status_btn.setEnabled(has_selection)
        
        self.print_receipt_btn.setEnabled(has_selection)
    
    def new_repair(self):
        """Create new repair ticket"""
        if not self.require_permission("repairs", "إنشاء تذكرة صيانة جديدة"):
            return
        
        dialog = RepairDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.log_action("new_repair", "إنشاء تذكرة صيانة جديدة")
    
    def edit_repair(self):
        """Edit selected repair"""
        if not self.require_permission("repairs", "تعديل تذكرة الصيانة"):
            return
        
        selected_rows = self.repairs_table.get_selected_rows()
        if not selected_rows:
            self.show_message("يرجى اختيار تذكرة للتعديل", "warning")
            return
        
        row_index = selected_rows[0]
        if hasattr(self, 'current_repairs') and row_index < len(self.current_repairs):
            repair = self.current_repairs[row_index]
            
            dialog = RepairDialog(self.db_manager, repair, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh_data()
                self.log_action("edit_repair", f"تعديل تذكرة الصيانة: {repair.ticket_no}")
    
    def update_repair_status(self):
        """Update repair status"""
        if not self.require_permission("repairs", "تحديث حالة الصيانة"):
            return
        
        selected_rows = self.repairs_table.get_selected_rows()
        if not selected_rows:
            self.show_message("يرجى اختيار تذكرة لتحديث حالتها", "warning")
            return
        
        row_index = selected_rows[0]
        if hasattr(self, 'current_repairs') and row_index < len(self.current_repairs):
            repair = self.current_repairs[row_index]
            
            # Show status selection dialog
            dialog = RepairStatusDialog(repair, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_status = dialog.get_selected_status()
                if new_status and new_status != repair.status:
                    self.update_repair_status_in_db(repair, new_status)
    
    def update_repair_status_in_db(self, repair, new_status):
        """Update repair status in database"""
        try:
            session = self.db_manager.get_session()
            
            repair_obj = session.query(type(repair)).get(repair.id)
            old_status = repair_obj.status
            repair_obj.status = new_status
            
            # Set exit date if completed
            if new_status in ['تم الإصلاح', 'غير قابل للإصلاح', 'تم التسليم']:
                if not repair_obj.exit_date:
                    repair_obj.exit_date = datetime.now()
            
            session.commit()
            
            self.refresh_data()
            self.log_action("update_repair_status", 
                          f"تحديث حالة التذكرة {repair.ticket_no} من '{old_status}' إلى '{new_status}'")
            self.show_message("تم تحديث حالة التذكرة بنجاح", "success")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"خطأ في تحديث حالة الصيانة: {e}")
            self.show_message(f"خطأ في تحديث الحالة: {str(e)}", "error")
        finally:
            session.close()
    
    def print_receipt(self):
        """Print repair receipt"""
        selected_rows = self.repairs_table.get_selected_rows()
        if not selected_rows:
            return
        
        row_index = selected_rows[0]
        if hasattr(self, 'current_repairs') and row_index < len(self.current_repairs):
            repair = self.current_repairs[row_index]
            
            try:
                from utils.pdf_generator import generate_repair_receipt
                pdf_content = generate_repair_receipt(repair)
                
                # Save and open PDF
                from pathlib import Path
                pdf_path = Path(f"repair_receipt_{repair.ticket_no}.pdf")
                with open(pdf_path, "wb") as f:
                    f.write(pdf_content)
                
                # Open with default PDF viewer
                import os
                os.startfile(str(pdf_path))
                
                self.log_action("print_repair_receipt", f"طباعة إيصال الصيانة: {repair.ticket_no}")
                
            except Exception as e:
                self.logger.error(f"خطأ في طباعة الإيصال: {e}")
                self.show_message(f"خطأ في طباعة الإيصال: {str(e)}", "error")
    
    def new_transfer(self):
        """Create new transfer"""
        if not self.require_permission("repairs", "إنشاء تحويل جديد"):
            return
        
        dialog = TransferDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.log_action("new_transfer", "إنشاء تحويل رصيد جديد")


class RepairStatusDialog(QDialog):
    """Dialog for updating repair status"""
    
    def __init__(self, repair, parent=None):
        super().__init__(parent)
        self.repair = repair
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"تحديث حالة التذكرة - {self.repair.ticket_no}")
        self.setMinimumSize(400, 300)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(self)
        
        # Current status
        current_label = QLabel(f"الحالة الحالية: {self.repair.status}")
        current_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(current_label)
        
        # New status selection
        layout.addWidget(QLabel("الحالة الجديدة:"))
        self.status_combo = QComboBox()
        for status in Config.REPAIR_STATUSES:
            self.status_combo.addItem(status)
        
        # Set current status as selected
        current_index = self.status_combo.findText(self.repair.status)
        if current_index >= 0:
            self.status_combo.setCurrentIndex(current_index)
        
        layout.addWidget(self.status_combo)
        
        # Notes
        layout.addWidget(QLabel("ملاحظات:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        layout.addWidget(self.notes_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_selected_status(self):
        """Get selected status"""
        return self.status_combo.currentText()
    
    def get_notes(self):
        """Get notes"""
        return self.notes_edit.toPlainText()


class TransferDialog(QDialog):
    """Dialog for creating new transfer"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("تحويل رصيد جديد")
        self.setMinimumSize(500, 400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QFormLayout(self)
        
        # Transfer type
        self.type_combo = QComboBox()
        for transfer_type in Config.TRANSFER_TYPES:
            self.type_combo.addItem(transfer_type)
        layout.addRow("نوع التحويل:", self.type_combo)
        
        # Amount
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setMaximum(999999.99)
        self.amount_edit.setDecimals(2)
        layout.addRow("المبلغ:", self.amount_edit)
        
        # From account
        self.from_account_edit = QLineEdit()
        layout.addRow("من حساب:", self.from_account_edit)
        
        # To account
        self.to_account_edit = QLineEdit()
        layout.addRow("إلى حساب:", self.to_account_edit)
        
        # Reference ID
        self.reference_id_edit = QLineEdit()
        layout.addRow("رقم العملية:", self.reference_id_edit)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        layout.addRow("ملاحظات:", self.notes_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def accept(self):
        """Handle dialog acceptance"""
        if self.validate_input():
            self.save_transfer()
            super().accept()
    
    def validate_input(self):
        """Validate input"""
        if self.amount_edit.value() <= 0:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال مبلغ صحيح")
            return False
        
        if not self.to_account_edit.text().strip():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال الحساب المحول إليه")
            return False
        
        return True
    
    def save_transfer(self):
        """Save transfer to database"""
        try:
            session = self.db_manager.get_session()
            from models import Transfer
            
            transfer = Transfer(
                type=self.type_combo.currentText(),
                amount=self.amount_edit.value(),
                from_account=self.from_account_edit.text().strip(),
                to_account=self.to_account_edit.text().strip(),
                reference_id=self.reference_id_edit.text().strip(),
                note=self.notes_edit.toPlainText(),
                user_id=1  # Should be current user ID
            )
            
            session.add(transfer)
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
