from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit,
                            QFormLayout, QDialog, QMessageBox, QGroupBox,
                            QHeaderView, QAbstractItemView, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime

from services.transfer_service import TransferService
from ui.styles import get_stylesheet

class TransferWindow(QMainWindow):
    """Balance transfer and cash transactions window"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.transfer_service = TransferService()
        self.current_transfer = None
        
        self.setup_ui()
        self.apply_styles()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("تحويلات الرصيد والمعاملات النقدية")
        self.setMinimumSize(1000, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("إدارة تحويلات الرصيد")
        title_label.setFont(QFont("Noto Sans Arabic", 18, QFont.Weight.Bold))
        title_label.setObjectName("title-label")
        
        # Add new transfer button
        self.add_transfer_btn = QPushButton("معاملة جديدة")
        self.add_transfer_btn.clicked.connect(self.add_transfer)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_transfer_btn)
        
        # Search and filter section
        filter_group = QGroupBox("البحث والفلترة")
        filter_layout = QHBoxLayout()
        
        # Search box
        search_label = QLabel("بحث:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث برقم المرجع، رقم الحساب، أو الملاحظات...")
        self.search_input.textChanged.connect(self.filter_transfers)
        
        # Type filter
        type_label = QLabel("نوع المعاملة:")
        self.type_filter = QComboBox()
        self.type_filter.addItems(["الكل", "فودافون كاش", "اتصالات كاش", "اورانج كاش", 
                                  "اكسس كاش", "كروت فكّ", "تحويل بنكي", "أخرى"])
        self.type_filter.currentTextChanged.connect(self.filter_transfers)
        
        # Date range
        date_label = QLabel("من تاريخ:")
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        self.from_date.dateChanged.connect(self.filter_transfers)
        
        to_date_label = QLabel("إلى تاريخ:")
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.dateChanged.connect(self.filter_transfers)
        
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(type_label)
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(date_label)
        filter_layout.addWidget(self.from_date)
        filter_layout.addWidget(to_date_label)
        filter_layout.addWidget(self.to_date)
        
        filter_group.setLayout(filter_layout)
        
        # Transfers table
        self.transfers_table = QTableWidget()
        self.setup_transfers_table()
        
        # Summary section
        summary_group = QGroupBox("ملخص المعاملات")
        summary_layout = QHBoxLayout()
        
        self.total_amount_label = QLabel("إجمالي المبلغ: 0.00 جنيه")
        self.total_amount_label.setFont(QFont("Noto Sans Arabic", 12, QFont.Weight.Bold))
        
        self.transaction_count_label = QLabel("عدد المعاملات: 0")
        self.transaction_count_label.setFont(QFont("Noto Sans Arabic", 12, QFont.Weight.Bold))
        
        summary_layout.addWidget(self.total_amount_label)
        summary_layout.addStretch()
        summary_layout.addWidget(self.transaction_count_label)
        
        summary_group.setLayout(summary_layout)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.view_btn = QPushButton("عرض التفاصيل")
        self.view_btn.clicked.connect(self.view_transfer)
        self.view_btn.setEnabled(False)
        
        self.edit_btn = QPushButton("تعديل")
        self.edit_btn.clicked.connect(self.edit_transfer)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.clicked.connect(self.delete_transfer)
        self.delete_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.view_btn)
        buttons_layout.addWidget(self.edit_btn)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addStretch()
        
        # Add layouts to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(filter_group)
        main_layout.addWidget(self.transfers_table)
        main_layout.addWidget(summary_group)
        main_layout.addLayout(buttons_layout)
        
        central_widget.setLayout(main_layout)
        
        # Connect table selection
        self.transfers_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def setup_transfers_table(self):
        """Setup transfers table"""
        headers = ["التاريخ", "نوع المعاملة", "المبلغ", "من حساب", "إلى حساب", "رقم المرجع", "الحالة", "ملاحظات"]
        
        self.transfers_table.setColumnCount(len(headers))
        self.transfers_table.setHorizontalHeaderLabels(headers)
        
        self.transfers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.transfers_table.setAlternatingRowColors(True)
        self.transfers_table.setSortingEnabled(True)
        
        # Resize columns
        header = self.transfers_table.horizontalHeader()
        header.setStretchLastSection(True)
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(get_stylesheet("light"))
    
    def load_data(self):
        """Load transfers data"""
        try:
            self.load_transfers()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {str(e)}")
    
    def load_transfers(self):
        """Load transfers into table"""
        try:
            # Get date range
            from_date = self.from_date.date().toPython()
            to_date = self.to_date.date().toPython()
            
            transfers = self.transfer_service.get_transfers(from_date, to_date)
            
            self.transfers_table.setRowCount(len(transfers))
            
            total_amount = 0
            
            for row, transfer in enumerate(transfers):
                # Format date
                transfer_date = transfer.date.strftime("%Y-%m-%d %H:%M") if transfer.date else ""
                
                items = [
                    transfer_date,
                    transfer.transfer_type,
                    f"{transfer.amount:.2f}",
                    transfer.from_account or "",
                    transfer.to_account,
                    transfer.reference_no or "",
                    transfer.status,
                    transfer.note[:30] + "..." if transfer.note and len(transfer.note) > 30 else transfer.note or ""
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    item.setData(Qt.ItemDataRole.UserRole, transfer.id)
                    
                    # Color coding for status
                    if col == 6:  # Status column
                        if transfer.status == "completed":
                            item.setBackground(Qt.GlobalColor.green)
                        elif transfer.status == "pending":
                            item.setBackground(Qt.GlobalColor.yellow)
                        elif transfer.status == "failed":
                            item.setBackground(Qt.GlobalColor.red)
                    
                    self.transfers_table.setItem(row, col, item)
                
                total_amount += transfer.amount
            
            # Update summary
            self.total_amount_label.setText(f"إجمالي المبلغ: {total_amount:.2f} جنيه")
            self.transaction_count_label.setText(f"عدد المعاملات: {len(transfers)}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل المعاملات: {str(e)}")
    
    def filter_transfers(self):
        """Filter transfers and reload data"""
        self.load_transfers()
    
    def on_selection_changed(self):
        """Handle table selection change"""
        selected_rows = self.transfers_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.view_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            transfer_id = self.transfers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.current_transfer = self.transfer_service.get_transfer_by_id(transfer_id)
    
    def add_transfer(self):
        """Add new transfer"""
        dialog = TransferDialog(self, self.transfer_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_transfers()
    
    def view_transfer(self):
        """View transfer details"""
        if self.current_transfer:
            dialog = TransferViewDialog(self, self.current_transfer)
            dialog.exec()
    
    def edit_transfer(self):
        """Edit selected transfer"""
        if self.current_transfer:
            dialog = TransferDialog(self, self.transfer_service, self.current_transfer)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_transfers()
    
    def delete_transfer(self):
        """Delete selected transfer"""
        if not self.current_transfer:
            return
        
        reply = QMessageBox.question(
            self,
            'تأكيد الحذف',
            f'هل أنت متأكد من حذف المعاملة رقم "{self.current_transfer.reference_no}"؟',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.transfer_service.delete_transfer(self.current_transfer.id)
                QMessageBox.information(self, "نجح", "تم حذف المعاملة بنجاح")
                self.load_transfers()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في حذف المعاملة: {str(e)}")

class TransferDialog(QDialog):
    """Dialog for adding/editing transfers"""
    
    def __init__(self, parent, transfer_service, transfer=None):
        super().__init__(parent)
        self.transfer_service = transfer_service
        self.transfer = transfer
        self.is_edit_mode = transfer is not None
        
        self.setup_ui()
        if self.is_edit_mode:
            self.load_transfer_data()
    
    def setup_ui(self):
        """Setup dialog UI"""
        title = "تعديل المعاملة" if self.is_edit_mode else "معاملة جديدة"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Transfer type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["فودافون كاش", "اتصالات كاش", "اورانج كاش", 
                                 "اكسس كاش", "كروت فكّ", "تحويل بنكي", "أخرى"])
        
        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(999999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setMinimum(0.01)
        
        # Accounts
        self.from_account_input = QLineEdit()
        self.to_account_input = QLineEdit()
        
        # Reference number
        self.reference_input = QLineEdit()
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["completed", "pending", "failed"])
        self.status_combo.setItemText(0, "مكتملة")
        self.status_combo.setItemText(1, "قيد الانتظار")
        self.status_combo.setItemText(2, "فاشلة")
        
        # Note
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(100)
        
        # Add fields to form
        form_layout.addRow("نوع المعاملة:", self.type_combo)
        form_layout.addRow("المبلغ:", self.amount_input)
        form_layout.addRow("من حساب:", self.from_account_input)
        form_layout.addRow("إلى حساب:", self.to_account_input)
        form_layout.addRow("رقم المرجع:", self.reference_input)
        form_layout.addRow("الحالة:", self.status_combo)
        form_layout.addRow("ملاحظات:", self.note_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("حفظ")
        self.save_btn.clicked.connect(self.save_transfer)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_transfer_data(self):
        """Load existing transfer data for editing"""
        if not self.transfer:
            return
        
        # Set transfer type
        type_index = self.type_combo.findText(self.transfer.transfer_type)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
        
        self.amount_input.setValue(self.transfer.amount)
        self.from_account_input.setText(self.transfer.from_account or "")
        self.to_account_input.setText(self.transfer.to_account or "")
        self.reference_input.setText(self.transfer.reference_no or "")
        
        # Set status
        status_map = {"completed": 0, "pending": 1, "failed": 2}
        status_index = status_map.get(self.transfer.status, 0)
        self.status_combo.setCurrentIndex(status_index)
        
        self.note_input.setPlainText(self.transfer.note or "")
    
    def save_transfer(self):
        """Save transfer data"""
        try:
            # Validate required fields
            if self.amount_input.value() <= 0:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال مبلغ صحيح")
                return
            
            if not self.to_account_input.text().strip():
                QMessageBox.warning(self, "تحذير", "يرجى إدخال حساب الوجهة")
                return
            
            # Prepare transfer data
            status_map = {0: "completed", 1: "pending", 2: "failed"}
            transfer_data = {
                'transfer_type': self.type_combo.currentText(),
                'amount': self.amount_input.value(),
                'from_account': self.from_account_input.text().strip() or None,
                'to_account': self.to_account_input.text().strip(),
                'reference_no': self.reference_input.text().strip() or None,
                'status': status_map[self.status_combo.currentIndex()],
                'note': self.note_input.toPlainText().strip() or None,
                'user_id': self.parent().current_user.id
            }
            
            # Save transfer
            if self.is_edit_mode:
                self.transfer_service.update_transfer(self.transfer.id, transfer_data)
                QMessageBox.information(self, "نجح", "تم تحديث المعاملة بنجاح")
            else:
                transfer = self.transfer_service.create_transfer(transfer_data)
                QMessageBox.information(self, "نجح", "تم إضافة المعاملة بنجاح")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حفظ المعاملة: {str(e)}")

class TransferViewDialog(QDialog):
    """Dialog for viewing transfer details"""
    
    def __init__(self, parent, transfer):
        super().__init__(parent)
        self.transfer = transfer
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"تفاصيل المعاملة")
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(400, 350)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(f"معاملة {self.transfer.transfer_type}")
        title_label.setFont(QFont("Noto Sans Arabic", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status mapping for display
        status_text = {
            "completed": "مكتملة",
            "pending": "قيد الانتظار", 
            "failed": "فاشلة"
        }.get(self.transfer.status, self.transfer.status)
        
        # Details
        details_text = f"""
        نوع المعاملة: {self.transfer.transfer_type}
        المبلغ: {self.transfer.amount:.2f} جنيه
        
        من حساب: {self.transfer.from_account or 'غير محدد'}
        إلى حساب: {self.transfer.to_account}
        
        رقم المرجع: {self.transfer.reference_no or 'غير محدد'}
        الحالة: {status_text}
        
        التاريخ: {self.transfer.date.strftime('%Y-%m-%d %H:%M:%S') if self.transfer.date else 'غير محدد'}
        المستخدم: {self.transfer.user.name if self.transfer.user else 'غير محدد'}
        
        ملاحظات: {self.transfer.note or 'لا توجد ملاحظات'}
        """
        
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        details_label.setStyleSheet("QLabel { padding: 15px; background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 5px; }")
        
        # Close button
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        
        layout.addWidget(title_label)
        layout.addWidget(details_label)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

# Create TransferService class
class TransferService:
    """Service for transfer management operations"""
    
    def __init__(self):
        from utils.logger import get_logger
        from config.database import SessionLocal
        self.logger = get_logger(__name__)
    
    def get_transfers(self, start_date=None, end_date=None):
        """Get transfers with optional date filter"""
        from config.database import SessionLocal
        from models.transfer import Transfer
        from datetime import datetime, timedelta
        
        db = SessionLocal()
        try:
            query = db.query(Transfer)
            
            if start_date:
                query = query.filter(Transfer.date >= datetime.combine(start_date, datetime.min.time()))
            if end_date:
                query = query.filter(Transfer.date <= datetime.combine(end_date, datetime.max.time()))
            
            return query.order_by(Transfer.date.desc()).all()
            
        except Exception as e:
            self.logger.error(f"Error fetching transfers: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_transfer_by_id(self, transfer_id):
        """Get transfer by ID"""
        from config.database import SessionLocal
        from models.transfer import Transfer
        
        db = SessionLocal()
        try:
            return db.query(Transfer).filter(Transfer.id == transfer_id).first()
        except Exception as e:
            self.logger.error(f"Error fetching transfer {transfer_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def create_transfer(self, transfer_data):
        """Create new transfer"""
        from config.database import SessionLocal
        from models.transfer import Transfer
        
        db = SessionLocal()
        try:
            transfer = Transfer(**transfer_data)
            db.add(transfer)
            db.commit()
            
            self.logger.info(f"Created transfer: {transfer.reference_no}")
            return transfer
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating transfer: {str(e)}")
            raise e
        finally:
            db.close()
    
    def update_transfer(self, transfer_id, transfer_data):
        """Update existing transfer"""
        from config.database import SessionLocal
        from models.transfer import Transfer
        
        db = SessionLocal()
        try:
            transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
            if not transfer:
                raise ValueError("المعاملة غير موجودة")
            
            for key, value in transfer_data.items():
                if hasattr(transfer, key):
                    setattr(transfer, key, value)
            
            db.commit()
            self.logger.info(f"Updated transfer: {transfer.reference_no}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating transfer {transfer_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def delete_transfer(self, transfer_id):
        """Delete transfer"""
        from config.database import SessionLocal
        from models.transfer import Transfer
        
        db = SessionLocal()
        try:
            transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
            if not transfer:
                raise ValueError("المعاملة غير موجودة")
            
            db.delete(transfer)
            db.commit()
            self.logger.info(f"Deleted transfer: {transfer.reference_no}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error deleting transfer {transfer_id}: {str(e)}")
            raise e
        finally:
            db.close()
