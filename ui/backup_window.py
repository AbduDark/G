from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QProgressBar, QMessageBox, QGroupBox, QFileDialog,
                            QHeaderView, QAbstractItemView, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime
import os

from services.backup_service import BackupService
from ui.styles import get_stylesheet

class BackupWindow(QMainWindow):
    """Backup and restore operations window"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.backup_service = BackupService()
        
        self.setup_ui()
        self.apply_styles()
        self.load_backups()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("النسخ الاحتياطي والاستعادة")
        self.setMinimumSize(900, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("النسخ الاحتياطي والاستعادة")
        title_label.setFont(QFont("Noto Sans Arabic", 18, QFont.Weight.Bold))
        title_label.setObjectName("title-label")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Backup actions group
        actions_group = QGroupBox("العمليات")
        actions_layout = QHBoxLayout()
        
        self.create_backup_btn = QPushButton("إنشاء نسخة احتياطية")
        self.create_backup_btn.clicked.connect(self.create_backup)
        
        self.restore_backup_btn = QPushButton("استعادة من نسخة")
        self.restore_backup_btn.clicked.connect(self.restore_backup)
        self.restore_backup_btn.setEnabled(False)
        
        self.import_backup_btn = QPushButton("استيراد نسخة خارجية")
        self.import_backup_btn.clicked.connect(self.import_backup)
        
        self.export_backup_btn = QPushButton("تصدير للمزامنة")
        self.export_backup_btn.clicked.connect(self.export_backup)
        self.export_backup_btn.setEnabled(False)
        
        self.delete_backup_btn = QPushButton("حذف نسخة")
        self.delete_backup_btn.clicked.connect(self.delete_backup)
        self.delete_backup_btn.setEnabled(False)
        
        actions_layout.addWidget(self.create_backup_btn)
        actions_layout.addWidget(self.restore_backup_btn)
        actions_layout.addWidget(self.import_backup_btn)
        actions_layout.addWidget(self.export_backup_btn)
        actions_layout.addWidget(self.delete_backup_btn)
        actions_layout.addStretch()
        
        actions_group.setLayout(actions_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        
        # Backups table
        backups_label = QLabel("النسخ الاحتياطية المتاحة:")
        backups_label.setFont(QFont("Noto Sans Arabic", 12, QFont.Weight.Bold))
        
        self.backups_table = QTableWidget()
        self.setup_backups_table()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_backups)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("تحديث القائمة")
        self.refresh_btn.clicked.connect(self.load_backups)
        
        self.auto_refresh_btn = QPushButton("تحديث تلقائي")
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.toggled.connect(self.toggle_auto_refresh)
        
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addWidget(self.auto_refresh_btn)
        refresh_layout.addStretch()
        
        # Add layouts to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(actions_group)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(QLabel("حالة العملية:"))
        main_layout.addWidget(self.status_text)
        main_layout.addWidget(backups_label)
        main_layout.addWidget(self.backups_table)
        main_layout.addLayout(refresh_layout)
        
        central_widget.setLayout(main_layout)
        
        # Connect table selection
        self.backups_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def setup_backups_table(self):
        """Setup backups table"""
        headers = ["اسم الملف", "التاريخ", "الحجم", "المسار"]
        
        self.backups_table.setColumnCount(len(headers))
        self.backups_table.setHorizontalHeaderLabels(headers)
        
        self.backups_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.backups_table.setAlternatingRowColors(True)
        self.backups_table.setSortingEnabled(True)
        
        # Resize columns
        header = self.backups_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(get_stylesheet("light"))
    
    def load_backups(self):
        """Load available backups into table"""
        try:
            backups = self.backup_service.get_backups_list()
            
            self.backups_table.setRowCount(len(backups))
            
            for row, backup in enumerate(backups):
                # Format file size
                size_mb = backup['size'] / (1024 * 1024)
                size_text = f"{size_mb:.2f} MB"
                
                # Format date
                date_text = backup['created'].strftime("%Y-%m-%d %H:%M")
                
                items = [
                    backup['name'],
                    date_text,
                    size_text,
                    backup['path']
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    item.setData(Qt.ItemDataRole.UserRole, backup)
                    self.backups_table.setItem(row, col, item)
            
            # Update status
            self.update_status(f"تم تحديث القائمة - العدد: {len(backups)} نسخة احتياطية")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل النسخ الاحتياطية: {str(e)}")
            self.update_status(f"خطأ في تحميل النسخ الاحتياطية: {str(e)}")
    
    def on_selection_changed(self):
        """Handle table selection change"""
        selected_rows = self.backups_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.restore_backup_btn.setEnabled(has_selection)
        self.export_backup_btn.setEnabled(has_selection)
        self.delete_backup_btn.setEnabled(has_selection)
    
    def create_backup(self):
        """Create new backup"""
        try:
            self.update_status("جاري إنشاء نسخة احتياطية...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Create backup in a separate thread
            self.backup_thread = BackupThread(self.backup_service, "create")
            self.backup_thread.finished.connect(self.on_backup_finished)
            self.backup_thread.error.connect(self.on_backup_error)
            self.backup_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في إنشاء النسخة الاحتياطية: {str(e)}")
            self.progress_bar.setVisible(False)
    
    def restore_backup(self):
        """Restore from selected backup"""
        selected_rows = self.backups_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        backup_data = self.backups_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            'تأكيد الاستعادة',
            f'هل أنت متأكد من استعادة النسخة الاحتياطية:\n{backup_data["name"]}\n\n'
            'تحذير: سيتم استبدال جميع البيانات الحالية!',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.update_status(f"جاري الاستعادة من: {backup_data['name']}")
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
                
                # Restore in a separate thread
                self.backup_thread = BackupThread(self.backup_service, "restore", backup_data['path'])
                self.backup_thread.finished.connect(self.on_restore_finished)
                self.backup_thread.error.connect(self.on_backup_error)
                self.backup_thread.start()
                
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في الاستعادة: {str(e)}")
                self.progress_bar.setVisible(False)
    
    def import_backup(self):
        """Import external backup file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "استيراد نسخة احتياطية",
            "",
            "Backup Files (*.zip *.db);;All Files (*)"
        )
        
        if file_path:
            reply = QMessageBox.question(
                self,
                'تأكيد الاستيراد',
                f'هل أنت متأكد من استيراد واستعادة النسخة الاحتياطية:\n{os.path.basename(file_path)}\n\n'
                'تحذير: سيتم استبدال جميع البيانات الحالية!',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.update_status(f"جاري استيراد النسخة الاحتياطية...")
                    self.progress_bar.setVisible(True)
                    self.progress_bar.setRange(0, 0)
                    
                    # Import and restore in a separate thread
                    self.backup_thread = BackupThread(self.backup_service, "restore", file_path)
                    self.backup_thread.finished.connect(self.on_restore_finished)
                    self.backup_thread.error.connect(self.on_backup_error)
                    self.backup_thread.start()
                    
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"خطأ في الاستيراد: {str(e)}")
                    self.progress_bar.setVisible(False)
    
    def export_backup(self):
        """Export backup to cloud sync folder"""
        selected_rows = self.backups_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        backup_data = self.backups_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        folder_dialog = QFileDialog()
        cloud_folder = folder_dialog.getExistingDirectory(
            self,
            "اختيار مجلد المزامنة السحابية"
        )
        
        if cloud_folder:
            try:
                self.update_status(f"جاري تصدير النسخة الاحتياطية...")
                self.backup_service.export_to_cloud_folder(backup_data['path'], cloud_folder)
                
                self.update_status(f"تم تصدير النسخة الاحتياطية إلى: {cloud_folder}")
                QMessageBox.information(
                    self, 
                    "نجح", 
                    f"تم تصدير النسخة الاحتياطية بنجاح إلى:\n{cloud_folder}"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في التصدير: {str(e)}")
    
    def delete_backup(self):
        """Delete selected backup"""
        selected_rows = self.backups_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        backup_data = self.backups_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            'تأكيد الحذف',
            f'هل أنت متأكد من حذف النسخة الاحتياطية:\n{backup_data["name"]}؟',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(backup_data['path'])
                self.load_backups()
                self.update_status(f"تم حذف النسخة الاحتياطية: {backup_data['name']}")
                
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في حذف النسخة الاحتياطية: {str(e)}")
    
    def toggle_auto_refresh(self, checked):
        """Toggle auto refresh of backups list"""
        if checked:
            self.refresh_timer.start(30000)  # Refresh every 30 seconds
            self.auto_refresh_btn.setText("إيقاف التحديث التلقائي")
        else:
            self.refresh_timer.stop()
            self.auto_refresh_btn.setText("تحديث تلقائي")
    
    def update_status(self, message):
        """Update status text"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        
        # Scroll to bottom
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.status_text.setTextCursor(cursor)
    
    def on_backup_finished(self, result):
        """Handle backup thread completion"""
        self.progress_bar.setVisible(False)
        self.load_backups()
        
        if result:
            self.update_status(f"تم إنشاء النسخة الاحتياطية بنجاح: {result}")
            QMessageBox.information(self, "نجح", f"تم إنشاء النسخة الاحتياطية بنجاح")
        else:
            self.update_status("فشل في إنشاء النسخة الاحتياطية")
    
    def on_restore_finished(self, result):
        """Handle restore thread completion"""
        self.progress_bar.setVisible(False)
        
        if result:
            self.update_status("تم الاستعادة بنجاح")
            QMessageBox.information(
                self, 
                "نجح", 
                "تم الاستعادة بنجاح.\nيرجى إعادة تشغيل البرنامج لتطبيق التغييرات."
            )
        else:
            self.update_status("فشل في الاستعادة")
    
    def on_backup_error(self, error):
        """Handle backup thread error"""
        self.progress_bar.setVisible(False)
        self.update_status(f"خطأ: {error}")
        QMessageBox.critical(self, "خطأ", f"حدث خطأ: {error}")

class BackupThread(QThread):
    """Thread for backup/restore operations"""
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, backup_service, operation, file_path=None):
        super().__init__()
        self.backup_service = backup_service
        self.operation = operation
        self.file_path = file_path
    
    def run(self):
        """Run the backup/restore operation"""
        try:
            if self.operation == "create":
                result = self.backup_service.create_backup()
                self.finished.emit(str(result))
            elif self.operation == "restore":
                self.backup_service.restore_backup(self.file_path)
                self.finished.emit("success")
        except Exception as e:
            self.error.emit(str(e))
