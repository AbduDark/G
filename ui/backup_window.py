# -*- coding: utf-8 -*-
"""
Backup and restore management window
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                            QLineEdit, QFileDialog, QMessageBox, QHeaderView,
                            QFrame, QGroupBox, QFormLayout, QTabWidget,
                            QProgressBar, QTextEdit, QCheckBox, QSpinBox,
                            QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from models.user import User
from models.audit import Backup
from config.database import get_db_session
from config.settings import settings
from services.backup_service import BackupService
from utils.helpers import format_file_size, show_error, show_success

class BackupThread(QThread):
    """Background thread for backup operations"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    backup_completed = pyqtSignal(bool, str)
    
    def __init__(self, operation, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
        
    def run(self):
        """Run backup operation in background"""
        try:
            backup_service = BackupService()
            
            if self.operation == "create":
                self.status_updated.emit("إنشاء النسخة الاحتياطية...")
                result = backup_service.create_backup(
                    self.kwargs.get('backup_path'),
                    self.kwargs.get('description', ''),
                    self.kwargs.get('user_id'),
                    progress_callback=self.progress_updated.emit
                )
                self.backup_completed.emit(result is not None, "تم إنشاء النسخة الاحتياطية بنجاح" if result else "فشل في إنشاء النسخة الاحتياطية")
                
            elif self.operation == "restore":
                self.status_updated.emit("استعادة النسخة الاحتياطية...")
                result = backup_service.restore_backup(
                    self.kwargs.get('backup_path'),
                    progress_callback=self.progress_updated.emit
                )
                self.backup_completed.emit(result, "تم استعادة النسخة الاحتياطية بنجاح" if result else "فشل في استعادة النسخة الاحتياطية")
                
        except Exception as e:
            logging.error(f"Backup thread error: {e}")
            self.backup_completed.emit(False, f"خطأ: {str(e)}")

class BackupWindow(QMainWindow):
    """Backup and restore management window"""
    
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.backups_data = []
        self.backup_service = BackupService()
        self.backup_thread = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("إدارة النسخ الاحتياطي")
        self.setMinimumSize(1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Backup management tab
        self.setup_backup_tab()
        
        # Restore tab
        self.setup_restore_tab()
        
        # Settings tab
        self.setup_settings_tab()
        
    def setup_backup_tab(self):
        """Setup backup management tab"""
        backup_widget = QWidget()
        layout = QVBoxLayout()
        
        # Create backup section
        create_group = QGroupBox("إنشاء نسخة احتياطية جديدة")
        create_layout = QFormLayout()
        
        # Backup location
        backup_location_layout = QHBoxLayout()
        self.backup_path_input = QLineEdit()
        self.backup_path_input.setPlaceholderText("اختر موقع النسخة الاحتياطية...")
        self.browse_backup_btn = QPushButton("تصفح...")
        
        backup_location_layout.addWidget(self.backup_path_input)
        backup_location_layout.addWidget(self.browse_backup_btn)
        
        # Backup description
        self.backup_description_input = QLineEdit()
        self.backup_description_input.setPlaceholderText("وصف اختياري للنسخة الاحتياطية...")
        
        # Backup options
        self.include_attachments_checkbox = QCheckBox("تضمين المرفقات")
        self.include_attachments_checkbox.setChecked(True)
        
        self.compress_backup_checkbox = QCheckBox("ضغط النسخة الاحتياطية")
        self.compress_backup_checkbox.setChecked(True)
        
        create_layout.addRow("موقع النسخة:", backup_location_layout)
        create_layout.addRow("الوصف:", self.backup_description_input)
        create_layout.addRow("", self.include_attachments_checkbox)
        create_layout.addRow("", self.compress_backup_checkbox)
        
        # Create backup button
        self.create_backup_btn = QPushButton("إنشاء نسخة احتياطية")
        self.create_backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        create_layout.addRow("", self.create_backup_btn)
        
        create_group.setLayout(create_layout)
        layout.addWidget(create_group)
        
        # Progress section
        progress_group = QGroupBox("حالة العملية")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("جاهز")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Existing backups section
        backups_group = QGroupBox("النسخ الاحتياطية الموجودة")
        backups_layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.refresh_backups_btn = QPushButton("تحديث")
        self.delete_backup_btn = QPushButton("حذف النسخة")
        self.export_backup_btn = QPushButton("تصدير")
        
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.refresh_backups_btn)
        toolbar_layout.addWidget(self.delete_backup_btn)
        toolbar_layout.addWidget(self.export_backup_btn)
        
        backups_layout.addLayout(toolbar_layout)
        
        # Backups table
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(7)
        self.backups_table.setHorizontalHeaderLabels([
            "ID", "اسم الملف", "حجم الملف", "تاريخ الإنشاء", "النوع", "الحالة", "الوصف"
        ])
        
        header = self.backups_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        
        self.backups_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backups_table.setAlternatingRowColors(True)
        
        backups_layout.addWidget(self.backups_table)
        
        backups_group.setLayout(backups_layout)
        layout.addWidget(backups_group)
        
        backup_widget.setLayout(layout)
        self.tab_widget.addTab(backup_widget, "النسخ الاحتياطي")
        
    def setup_restore_tab(self):
        """Setup restore tab"""
        restore_widget = QWidget()
        layout = QVBoxLayout()
        
        # Restore from file section
        restore_file_group = QGroupBox("استعادة من ملف")
        restore_file_layout = QFormLayout()
        
        # File selection
        file_selection_layout = QHBoxLayout()
        self.restore_file_input = QLineEdit()
        self.restore_file_input.setPlaceholderText("اختر ملف النسخة الاحتياطية...")
        self.browse_restore_btn = QPushButton("تصفح...")
        
        file_selection_layout.addWidget(self.restore_file_input)
        file_selection_layout.addWidget(self.browse_restore_btn)
        
        # Restore options
        self.backup_before_restore_checkbox = QCheckBox("إنشاء نسخة احتياطية قبل الاستعادة")
        self.backup_before_restore_checkbox.setChecked(True)
        
        self.verify_backup_checkbox = QCheckBox("التحقق من سلامة النسخة الاحتياطية")
        self.verify_backup_checkbox.setChecked(True)
        
        restore_file_layout.addRow("ملف النسخة:", file_selection_layout)
        restore_file_layout.addRow("", self.backup_before_restore_checkbox)
        restore_file_layout.addRow("", self.verify_backup_checkbox)
        
        # Restore button
        self.restore_backup_btn = QPushButton("استعادة النسخة الاحتياطية")
        self.restore_backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        restore_file_layout.addRow("", self.restore_backup_btn)
        
        restore_file_group.setLayout(restore_file_layout)
        layout.addWidget(restore_file_group)
        
        # Restore from existing backup section
        restore_existing_group = QGroupBox("استعادة من النسخ الموجودة")
        restore_existing_layout = QVBoxLayout()
        
        # Quick restore table
        self.restore_table = QTableWidget()
        self.restore_table.setColumnCount(5)
        self.restore_table.setHorizontalHeaderLabels([
            "اسم الملف", "التاريخ", "حجم الملف", "الحالة", "استعادة"
        ])
        
        restore_existing_layout.addWidget(self.restore_table)
        restore_existing_group.setLayout(restore_existing_layout)
        layout.addWidget(restore_existing_group)
        
        # Warning section
        warning_group = QGroupBox("تحذير")
        warning_layout = QVBoxLayout()
        
        warning_text = QLabel(
            "تحذير: عملية الاستعادة ستقوم بالكتابة فوق البيانات الحالية.\n"
            "تأكد من إنشاء نسخة احتياطية من البيانات الحالية قبل المتابعة.\n"
            "لا يمكن التراجع عن هذه العملية."
        )
        warning_text.setStyleSheet("color: #dc3545; font-weight: bold; padding: 10px;")
        warning_text.setWordWrap(True)
        
        warning_layout.addWidget(warning_text)
        warning_group.setLayout(warning_layout)
        layout.addWidget(warning_group)
        
        layout.addStretch()
        restore_widget.setLayout(layout)
        self.tab_widget.addTab(restore_widget, "الاستعادة")
        
    def setup_settings_tab(self):
        """Setup backup settings tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout()
        
        # Auto backup settings
        auto_backup_group = QGroupBox("النسخ الاحتياطي التلقائي")
        auto_backup_layout = QFormLayout()
        
        self.enable_auto_backup_checkbox = QCheckBox("تفعيل النسخ الاحتياطي التلقائي")
        
        self.backup_interval_combo = QComboBox()
        self.backup_interval_combo.addItems([
            "يومياً", "كل 3 أيام", "أسبوعياً", "كل أسبوعين", "شهرياً"
        ])
        
        self.backup_time_combo = QComboBox()
        for hour in range(24):
            time_text = f"{hour:02d}:00"
            self.backup_time_combo.addItem(time_text)
        self.backup_time_combo.setCurrentText("02:00")  # Default 2 AM
        
        self.max_auto_backups_input = QSpinBox()
        self.max_auto_backups_input.setMinimum(1)
        self.max_auto_backups_input.setMaximum(100)
        self.max_auto_backups_input.setValue(30)
        
        auto_backup_layout.addRow("", self.enable_auto_backup_checkbox)
        auto_backup_layout.addRow("التكرار:", self.backup_interval_combo)
        auto_backup_layout.addRow("الوقت:", self.backup_time_combo)
        auto_backup_layout.addRow("أقصى عدد نسخ:", self.max_auto_backups_input)
        
        auto_backup_group.setLayout(auto_backup_layout)
        layout.addWidget(auto_backup_group)
        
        # Default locations
        locations_group = QGroupBox("المواقع الافتراضية")
        locations_layout = QFormLayout()
        
        # Default backup directory
        backup_dir_layout = QHBoxLayout()
        self.default_backup_dir_input = QLineEdit()
        self.browse_default_dir_btn = QPushButton("تصفح...")
        
        backup_dir_layout.addWidget(self.default_backup_dir_input)
        backup_dir_layout.addWidget(self.browse_default_dir_btn)
        
        locations_layout.addRow("مجلد النسخ الاحتياطي:", backup_dir_layout)
        
        locations_group.setLayout(locations_layout)
        layout.addWidget(locations_group)
        
        # Cloud sync settings
        cloud_group = QGroupBox("المزامنة السحابية")
        cloud_layout = QFormLayout()
        
        self.enable_cloud_sync_checkbox = QCheckBox("تفعيل المزامنة السحابية")
        
        self.cloud_provider_combo = QComboBox()
        self.cloud_provider_combo.addItems([
            "OneDrive", "Google Drive", "Dropbox", "مخصص"
        ])
        
        cloud_folder_layout = QHBoxLayout()
        self.cloud_folder_input = QLineEdit()
        self.browse_cloud_folder_btn = QPushButton("تصفح...")
        
        cloud_folder_layout.addWidget(self.cloud_folder_input)
        cloud_folder_layout.addWidget(self.browse_cloud_folder_btn)
        
        cloud_layout.addRow("", self.enable_cloud_sync_checkbox)
        cloud_layout.addRow("مزود الخدمة:", self.cloud_provider_combo)
        cloud_layout.addRow("مجلد المزامنة:", cloud_folder_layout)
        
        cloud_group.setLayout(cloud_layout)
        layout.addWidget(cloud_group)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.save_settings_btn = QPushButton("حفظ الإعدادات")
        self.test_backup_btn = QPushButton("اختبار النسخ الاحتياطي")
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_settings_btn)
        buttons_layout.addWidget(self.test_backup_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        settings_widget.setLayout(layout)
        self.tab_widget.addTab(settings_widget, "الإعدادات")
        
    def setup_connections(self):
        """Setup signal connections"""
        # Backup tab
        self.browse_backup_btn.clicked.connect(self.browse_backup_location)
        self.create_backup_btn.clicked.connect(self.create_backup)
        self.refresh_backups_btn.clicked.connect(self.load_backups)
        self.delete_backup_btn.clicked.connect(self.delete_backup)
        self.export_backup_btn.clicked.connect(self.export_backup)
        
        self.backups_table.selectionModel().selectionChanged.connect(self.on_backup_selection_changed)
        
        # Restore tab
        self.browse_restore_btn.clicked.connect(self.browse_restore_file)
        self.restore_backup_btn.clicked.connect(self.restore_backup)
        
        # Settings tab
        self.enable_auto_backup_checkbox.toggled.connect(self.toggle_auto_backup_settings)
        self.enable_cloud_sync_checkbox.toggled.connect(self.toggle_cloud_sync_settings)
        self.browse_default_dir_btn.clicked.connect(self.browse_default_backup_dir)
        self.browse_cloud_folder_btn.clicked.connect(self.browse_cloud_folder)
        self.save_settings_btn.clicked.connect(self.save_backup_settings)
        self.test_backup_btn.clicked.connect(self.test_backup)
        
    def load_data(self):
        """Load data"""
        self.load_backups()
        self.load_settings()
        
    def load_backups(self):
        """Load backups list"""
        session = get_db_session()
        try:
            backups = session.query(Backup).order_by(Backup.created_at.desc()).all()
            self.backups_data = backups
            
            self.update_backups_table()
            self.update_restore_table()
            
        finally:
            session.close()
            
    def update_backups_table(self):
        """Update backups table"""
        self.backups_table.setRowCount(len(self.backups_data))
        
        for row, backup in enumerate(self.backups_data):
            self.backups_table.setItem(row, 0, QTableWidgetItem(str(backup.id)))
            self.backups_table.setItem(row, 1, QTableWidgetItem(backup.filename))
            self.backups_table.setItem(row, 2, QTableWidgetItem(backup.file_size_formatted))
            self.backups_table.setItem(row, 3, QTableWidgetItem(backup.created_at.strftime("%Y-%m-%d %H:%M")))
            self.backups_table.setItem(row, 4, QTableWidgetItem(backup.backup_type))
            
            # Status with color coding
            status_item = QTableWidgetItem(backup.status)
            if backup.status == "completed":
                status_item.setBackground(QColor("#e8f5e8"))
            elif backup.status == "failed":
                status_item.setBackground(QColor("#ffebee"))
            self.backups_table.setItem(row, 5, status_item)
            
            self.backups_table.setItem(row, 6, QTableWidgetItem(backup.description or ""))
            
            # Store backup ID
            self.backups_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, backup.id)
            
    def update_restore_table(self):
        """Update restore table"""
        self.restore_table.setRowCount(len(self.backups_data))
        
        for row, backup in enumerate(self.backups_data):
            if backup.status == "completed":
                self.restore_table.setItem(row, 0, QTableWidgetItem(backup.filename))
                self.restore_table.setItem(row, 1, QTableWidgetItem(backup.created_at.strftime("%Y-%m-%d %H:%M")))
                self.restore_table.setItem(row, 2, QTableWidgetItem(backup.file_size_formatted))
                self.restore_table.setItem(row, 3, QTableWidgetItem("متاح"))
                
                # Restore button
                restore_btn = QPushButton("استعادة")
                restore_btn.clicked.connect(lambda checked, b=backup: self.restore_from_existing(b))
                self.restore_table.setCellWidget(row, 4, restore_btn)
                
    def load_settings(self):
        """Load backup settings"""
        # Load current settings from config
        self.enable_auto_backup_checkbox.setChecked(settings.database.auto_backup)
        self.max_auto_backups_input.setValue(settings.database.max_backups)
        self.default_backup_dir_input.setText(str(settings.get_backup_dir()))
        
        # Toggle dependent controls
        self.toggle_auto_backup_settings(settings.database.auto_backup)
        self.toggle_cloud_sync_settings(False)
        
    def toggle_auto_backup_settings(self, enabled: bool):
        """Toggle auto backup settings"""
        self.backup_interval_combo.setEnabled(enabled)
        self.backup_time_combo.setEnabled(enabled)
        self.max_auto_backups_input.setEnabled(enabled)
        
    def toggle_cloud_sync_settings(self, enabled: bool):
        """Toggle cloud sync settings"""
        self.cloud_provider_combo.setEnabled(enabled)
        self.cloud_folder_input.setEnabled(enabled)
        self.browse_cloud_folder_btn.setEnabled(enabled)
        
    def browse_backup_location(self):
        """Browse for backup file location"""
        default_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ النسخة الاحتياطية",
            str(settings.get_backup_dir() / default_filename),
            "Database Files (*.db);;All Files (*)"
        )
        
        if file_path:
            self.backup_path_input.setText(file_path)
            
    def browse_restore_file(self):
        """Browse for restore file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف النسخة الاحتياطية",
            str(settings.get_backup_dir()),
            "Database Files (*.db);;All Files (*)"
        )
        
        if file_path:
            self.restore_file_input.setText(file_path)
            
    def browse_default_backup_dir(self):
        """Browse for default backup directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "اختر مجلد النسخ الاحتياطي الافتراضي",
            str(settings.get_backup_dir())
        )
        
        if dir_path:
            self.default_backup_dir_input.setText(dir_path)
            
    def browse_cloud_folder(self):
        """Browse for cloud sync folder"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "اختر مجلد المزامنة السحابية",
            ""
        )
        
        if dir_path:
            self.cloud_folder_input.setText(dir_path)
            
    def create_backup(self):
        """Create new backup"""
        backup_path = self.backup_path_input.text().strip()
        
        if not backup_path:
            show_error(self, "يرجى اختيار موقع النسخة الاحتياطية")
            return
        
        description = self.backup_description_input.text().strip()
        
        # Confirm backup creation
        reply = QMessageBox.question(
            self, "تأكيد إنشاء النسخة الاحتياطية",
            f"هل تريد إنشاء نسخة احتياطية في:\n{backup_path}؟"
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Start backup in background thread
        self.create_backup_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("بدء إنشاء النسخة الاحتياطية...")
        
        self.backup_thread = BackupThread(
            "create",
            backup_path=backup_path,
            description=description,
            user_id=self.current_user.id
        )
        
        self.backup_thread.progress_updated.connect(self.progress_bar.setValue)
        self.backup_thread.status_updated.connect(self.status_label.setText)
        self.backup_thread.backup_completed.connect(self.on_backup_completed)
        
        self.backup_thread.start()
        
    def restore_backup(self):
        """Restore from selected file"""
        restore_file = self.restore_file_input.text().strip()
        
        if not restore_file:
            show_error(self, "يرجى اختيار ملف النسخة الاحتياطية")
            return
        
        if not os.path.exists(restore_file):
            show_error(self, "الملف المحدد غير موجود")
            return
        
        # Strong warning
        reply = QMessageBox.warning(
            self, "تحذير: استعادة النسخة الاحتياطية",
            "تحذير: هذه العملية ستقوم بالكتابة فوق جميع البيانات الحالية!\n\n"
            "سيتم فقدان جميع البيانات المدخلة منذ تاريخ النسخة الاحتياطية.\n"
            "تأكد من إنشاء نسخة احتياطية من البيانات الحالية قبل المتابعة.\n\n"
            "هل أنت متأكد من المتابعة؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Create backup before restore if requested
        if self.backup_before_restore_checkbox.isChecked():
            backup_path = settings.get_backup_dir() / f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            try:
                self.backup_service.create_backup(str(backup_path), "نسخة احتياطية قبل الاستعادة", self.current_user.id)
            except Exception as e:
                show_error(self, f"فشل في إنشاء نسخة احتياطية قبل الاستعادة:\n{str(e)}")
                return
        
        # Start restore in background thread
        self.restore_backup_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("بدء استعادة النسخة الاحتياطية...")
        
        self.backup_thread = BackupThread(
            "restore",
            backup_path=restore_file
        )
        
        self.backup_thread.progress_updated.connect(self.progress_bar.setValue)
        self.backup_thread.status_updated.connect(self.status_label.setText)
        self.backup_thread.backup_completed.connect(self.on_restore_completed)
        
        self.backup_thread.start()
        
    def restore_from_existing(self, backup: Backup):
        """Restore from existing backup record"""
        if not os.path.exists(backup.file_path):
            show_error(self, f"ملف النسخة الاحتياطية غير موجود:\n{backup.file_path}")
            return
        
        self.restore_file_input.setText(backup.file_path)
        self.tab_widget.setCurrentIndex(1)  # Switch to restore tab
        
    def delete_backup(self):
        """Delete selected backup"""
        selected_items = self.backups_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار نسخة احتياطية للحذف")
            return
        
        row = selected_items[0].row()
        backup_id = self.backups_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        backup_filename = self.backups_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف النسخة الاحتياطية '{backup_filename}'؟\n"
            "سيتم حذف الملف من القرص الصلب أيضاً."
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = self.backup_service.delete_backup(backup_id)
                if result:
                    self.load_backups()
                    show_success(self, "تم حذف النسخة الاحتياطية بنجاح")
                else:
                    show_error(self, "فشل في حذف النسخة الاحتياطية")
            except Exception as e:
                show_error(self, f"خطأ في حذف النسخة الاحتياطية:\n{str(e)}")
                
    def export_backup(self):
        """Export selected backup"""
        selected_items = self.backups_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار نسخة احتياطية للتصدير")
            return
        
        row = selected_items[0].row()
        backup_id = self.backups_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        session = get_db_session()
        try:
            backup = session.query(Backup).get(backup_id)
            if backup and os.path.exists(backup.file_path):
                export_path, _ = QFileDialog.getSaveFileName(
                    self, "تصدير النسخة الاحتياطية",
                    backup.filename,
                    "Database Files (*.db);;All Files (*)"
                )
                
                if export_path:
                    shutil.copy2(backup.file_path, export_path)
                    show_success(self, f"تم تصدير النسخة الاحتياطية إلى:\n{export_path}")
            else:
                show_error(self, "ملف النسخة الاحتياطية غير موجود")
        finally:
            session.close()
            
    def save_backup_settings(self):
        """Save backup settings"""
        try:
            settings.database.auto_backup = self.enable_auto_backup_checkbox.isChecked()
            settings.database.max_backups = self.max_auto_backups_input.value()
            settings.database.backup_dir = self.default_backup_dir_input.text()
            
            settings.save()
            show_success(self, "تم حفظ إعدادات النسخ الاحتياطي بنجاح")
            
        except Exception as e:
            show_error(self, f"فشل في حفظ الإعدادات:\n{str(e)}")
            
    def test_backup(self):
        """Test backup functionality"""
        try:
            test_path = settings.get_backup_dir() / f"test_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            result = self.backup_service.create_backup(str(test_path), "نسخة تجريبية", self.current_user.id)
            
            if result:
                # Clean up test file
                if os.path.exists(test_path):
                    os.remove(test_path)
                show_success(self, "اختبار النسخ الاحتياطي تم بنجاح")
            else:
                show_error(self, "فشل في اختبار النسخ الاحتياطي")
                
        except Exception as e:
            show_error(self, f"خطأ في اختبار النسخ الاحتياطي:\n{str(e)}")
            
    def on_backup_selection_changed(self):
        """Handle backup selection change"""
        has_selection = bool(self.backups_table.selectedItems())
        self.delete_backup_btn.setEnabled(has_selection)
        self.export_backup_btn.setEnabled(has_selection)
        
    def on_backup_completed(self, success: bool, message: str):
        """Handle backup completion"""
        self.create_backup_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("جاهز")
        
        if success:
            show_success(self, message)
            self.load_backups()
            # Clear form
            self.backup_path_input.clear()
            self.backup_description_input.clear()
        else:
            show_error(self, message)
            
    def on_restore_completed(self, success: bool, message: str):
        """Handle restore completion"""
        self.restore_backup_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("جاهز")
        
        if success:
            QMessageBox.information(
                self, "تمت الاستعادة بنجاح",
                f"{message}\n\nيُنصح بإعادة تشغيل التطبيق لضمان تحديث البيانات."
            )
            self.restore_file_input.clear()
        else:
            show_error(self, message)
