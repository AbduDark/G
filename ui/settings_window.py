# -*- coding: utf-8 -*-
"""
Settings and configuration window
"""

import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
                            QDoubleSpinBox, QTextEdit, QCheckBox, QGroupBox,
                            QFormLayout, QTabWidget, QFileDialog, QMessageBox,
                            QColorDialog, QFontDialog, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap

from models.user import User
from config.settings import settings
from utils.helpers import show_error, show_success

class SettingsWindow(QMainWindow):
    """Settings and configuration window"""
    
    # Signals
    settings_changed = pyqtSignal()
    
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.setup_ui()
        self.setup_connections()
        self.load_current_settings()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("إعدادات النظام")
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Shop settings tab
        self.setup_shop_tab()
        
        # Database settings tab
        self.setup_database_tab()
        
        # Printer settings tab
        self.setup_printer_tab()
        
        # UI settings tab
        self.setup_ui_tab()
        
        # User preferences tab
        self.setup_preferences_tab()
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("حفظ الإعدادات")
        self.cancel_btn = QPushButton("إلغاء")
        self.reset_btn = QPushButton("إعادة تعيين")
        self.apply_btn = QPushButton("تطبيق")
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.reset_btn)
        
        main_layout.addLayout(buttons_layout)
        
    def setup_shop_tab(self):
        """Setup shop information tab"""
        shop_widget = QWidget()
        layout = QVBoxLayout()
        
        # Basic information group
        basic_group = QGroupBox("المعلومات الأساسية")
        basic_layout = QFormLayout()
        
        self.shop_name_input = QLineEdit()
        self.shop_address_input = QTextEdit()
        self.shop_address_input.setMaximumHeight(80)
        self.shop_phone_input = QLineEdit()
        self.shop_email_input = QLineEdit()
        
        basic_layout.addRow("اسم المحل:", self.shop_name_input)
        basic_layout.addRow("العنوان:", self.shop_address_input)
        basic_layout.addRow("الهاتف:", self.shop_phone_input)
        basic_layout.addRow("البريد الإلكتروني:", self.shop_email_input)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Tax and currency group
        tax_group = QGroupBox("الضريبة والعملة")
        tax_layout = QFormLayout()
        
        self.tax_number_input = QLineEdit()
        self.tax_rate_input = QDoubleSpinBox()
        self.tax_rate_input.setMaximum(100)
        self.tax_rate_input.setSuffix("%")
        self.tax_rate_input.setDecimals(2)
        
        self.currency_input = QLineEdit()
        
        tax_layout.addRow("الرقم الضريبي:", self.tax_number_input)
        tax_layout.addRow("معدل الضريبة:", self.tax_rate_input)
        tax_layout.addRow("العملة:", self.currency_input)
        
        tax_group.setLayout(tax_layout)
        layout.addWidget(tax_group)
        
        # Logo section
        logo_group = QGroupBox("شعار المحل")
        logo_layout = QVBoxLayout()
        
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setReadOnly(True)
        
        logo_buttons_layout = QHBoxLayout()
        self.browse_logo_btn = QPushButton("تصفح...")
        self.remove_logo_btn = QPushButton("إزالة الشعار")
        
        logo_buttons_layout.addWidget(self.logo_path_input)
        logo_buttons_layout.addWidget(self.browse_logo_btn)
        logo_buttons_layout.addWidget(self.remove_logo_btn)
        
        logo_layout.addLayout(logo_buttons_layout)
        
        # Logo preview
        self.logo_preview = QLabel("لا يوجد شعار")
        self.logo_preview.setFixedSize(150, 100)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setStyleSheet("border: 1px solid #ccc; background: #f8f9fa;")
        
        logo_layout.addWidget(self.logo_preview)
        logo_group.setLayout(logo_layout)
        layout.addWidget(logo_group)
        
        layout.addStretch()
        shop_widget.setLayout(layout)
        self.tab_widget.addTab(shop_widget, "معلومات المحل")
        
    def setup_database_tab(self):
        """Setup database settings tab"""
        db_widget = QWidget()
        layout = QVBoxLayout()
        
        # Database location group
        location_group = QGroupBox("موقع قاعدة البيانات")
        location_layout = QFormLayout()
        
        self.db_path_input = QLineEdit()
        self.db_path_input.setReadOnly(True)
        
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_input)
        
        self.browse_db_btn = QPushButton("تصفح...")
        db_path_layout.addWidget(self.browse_db_btn)
        
        location_layout.addRow("مسار قاعدة البيانات:", db_path_layout)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # Backup settings group
        backup_group = QGroupBox("إعدادات النسخ الاحتياطي")
        backup_layout = QFormLayout()
        
        self.auto_backup_checkbox = QCheckBox("تفعيل النسخ الاحتياطي التلقائي")
        
        self.backup_interval_input = QSpinBox()
        self.backup_interval_input.setMinimum(1)
        self.backup_interval_input.setMaximum(168)  # 1 week
        self.backup_interval_input.setSuffix(" ساعة")
        
        self.max_backups_input = QSpinBox()
        self.max_backups_input.setMinimum(1)
        self.max_backups_input.setMaximum(100)
        
        self.backup_dir_input = QLineEdit()
        self.backup_dir_input.setReadOnly(True)
        
        backup_dir_layout = QHBoxLayout()
        backup_dir_layout.addWidget(self.backup_dir_input)
        
        self.browse_backup_dir_btn = QPushButton("تصفح...")
        backup_dir_layout.addWidget(self.browse_backup_dir_btn)
        
        backup_layout.addRow("", self.auto_backup_checkbox)
        backup_layout.addRow("فترة النسخ:", self.backup_interval_input)
        backup_layout.addRow("أقصى عدد نسخ:", self.max_backups_input)
        backup_layout.addRow("مجلد النسخ:", backup_dir_layout)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # Database maintenance group
        maintenance_group = QGroupBox("صيانة قاعدة البيانات")
        maintenance_layout = QVBoxLayout()
        
        maintenance_buttons_layout = QHBoxLayout()
        
        self.vacuum_db_btn = QPushButton("ضغط قاعدة البيانات")
        self.check_db_btn = QPushButton("فحص سلامة البيانات")
        self.repair_db_btn = QPushButton("إصلاح قاعدة البيانات")
        
        maintenance_buttons_layout.addWidget(self.vacuum_db_btn)
        maintenance_buttons_layout.addWidget(self.check_db_btn)
        maintenance_buttons_layout.addWidget(self.repair_db_btn)
        maintenance_buttons_layout.addStretch()
        
        maintenance_layout.addLayout(maintenance_buttons_layout)
        maintenance_group.setLayout(maintenance_layout)
        layout.addWidget(maintenance_group)
        
        layout.addStretch()
        db_widget.setLayout(layout)
        self.tab_widget.addTab(db_widget, "قاعدة البيانات")
        
    def setup_printer_tab(self):
        """Setup printer settings tab"""
        printer_widget = QWidget()
        layout = QVBoxLayout()
        
        # Default printer group
        default_printer_group = QGroupBox("الطابعة الافتراضية")
        default_printer_layout = QFormLayout()
        
        self.default_printer_combo = QComboBox()
        self.refresh_printers_btn = QPushButton("تحديث قائمة الطابعات")
        
        printer_layout = QHBoxLayout()
        printer_layout.addWidget(self.default_printer_combo)
        printer_layout.addWidget(self.refresh_printers_btn)
        
        default_printer_layout.addRow("الطابعة الافتراضية:", printer_layout)
        
        default_printer_group.setLayout(default_printer_layout)
        layout.addWidget(default_printer_group)
        
        # Thermal printer group
        thermal_printer_group = QGroupBox("الطابعة الحرارية")
        thermal_printer_layout = QFormLayout()
        
        self.thermal_printer_combo = QComboBox()
        self.thermal_printer_combo.addItem("لا توجد", None)
        
        thermal_printer_layout.addRow("الطابعة الحرارية:", self.thermal_printer_combo)
        
        thermal_printer_group.setLayout(thermal_printer_layout)
        layout.addWidget(thermal_printer_group)
        
        # Page settings group
        page_group = QGroupBox("إعدادات الصفحة")
        page_layout = QFormLayout()
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4", "A5", "Letter", "Custom"])
        
        self.margin_top_input = QSpinBox()
        self.margin_top_input.setMaximum(100)
        self.margin_top_input.setSuffix(" مم")
        
        self.margin_bottom_input = QSpinBox()
        self.margin_bottom_input.setMaximum(100)
        self.margin_bottom_input.setSuffix(" مم")
        
        self.margin_left_input = QSpinBox()
        self.margin_left_input.setMaximum(100)
        self.margin_left_input.setSuffix(" مم")
        
        self.margin_right_input = QSpinBox()
        self.margin_right_input.setMaximum(100)
        self.margin_right_input.setSuffix(" مم")
        
        page_layout.addRow("حجم الصفحة:", self.page_size_combo)
        page_layout.addRow("الهامش العلوي:", self.margin_top_input)
        page_layout.addRow("الهامش السفلي:", self.margin_bottom_input)
        page_layout.addRow("الهامش الأيسر:", self.margin_left_input)
        page_layout.addRow("الهامش الأيمن:", self.margin_right_input)
        
        page_group.setLayout(page_layout)
        layout.addWidget(page_group)
        
        # Test printing
        test_group = QGroupBox("اختبار الطباعة")
        test_layout = QVBoxLayout()
        
        test_buttons_layout = QHBoxLayout()
        
        self.test_print_btn = QPushButton("طباعة صفحة اختبار")
        self.test_thermal_btn = QPushButton("اختبار الطابعة الحرارية")
        
        test_buttons_layout.addWidget(self.test_print_btn)
        test_buttons_layout.addWidget(self.test_thermal_btn)
        test_buttons_layout.addStretch()
        
        test_layout.addLayout(test_buttons_layout)
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        layout.addStretch()
        printer_widget.setLayout(layout)
        self.tab_widget.addTab(printer_widget, "الطابعة")
        
    def setup_ui_tab(self):
        """Setup UI settings tab"""
        ui_widget = QWidget()
        layout = QVBoxLayout()
        
        # Theme group
        theme_group = QGroupBox("المظهر")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("فاتح", "light")
        self.theme_combo.addItem("داكن", "dark")
        
        theme_layout.addRow("السمة:", self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Font settings group
        font_group = QGroupBox("إعدادات الخط")
        font_layout = QFormLayout()
        
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Cairo", "Noto Kufi Arabic", "Tahoma", "Arial", "Times New Roman"
        ])
        
        self.font_size_input = QSpinBox()
        self.font_size_input.setMinimum(8)
        self.font_size_input.setMaximum(24)
        
        self.font_preview_label = QLabel("نموذج للنص - Sample Text")
        self.font_preview_label.setStyleSheet("border: 1px solid #ccc; padding: 10px;")
        
        self.change_font_btn = QPushButton("تغيير الخط...")
        
        font_layout.addRow("عائلة الخط:", self.font_family_combo)
        font_layout.addRow("حجم الخط:", self.font_size_input)
        font_layout.addRow("معاينة:", self.font_preview_label)
        font_layout.addRow("", self.change_font_btn)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Window settings group
        window_group = QGroupBox("إعدادات النافذة")
        window_layout = QFormLayout()
        
        self.window_width_input = QSpinBox()
        self.window_width_input.setMinimum(800)
        self.window_width_input.setMaximum(2560)
        
        self.window_height_input = QSpinBox()
        self.window_height_input.setMinimum(600)
        self.window_height_input.setMaximum(1440)
        
        self.remember_window_size_checkbox = QCheckBox("تذكر حجم النافذة")
        self.start_maximized_checkbox = QCheckBox("بدء مكبر")
        
        window_layout.addRow("عرض النافذة:", self.window_width_input)
        window_layout.addRow("ارتفاع النافذة:", self.window_height_input)
        window_layout.addRow("", self.remember_window_size_checkbox)
        window_layout.addRow("", self.start_maximized_checkbox)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        layout.addStretch()
        ui_widget.setLayout(layout)
        self.tab_widget.addTab(ui_widget, "واجهة المستخدم")
        
    def setup_preferences_tab(self):
        """Setup user preferences tab"""
        prefs_widget = QWidget()
        layout = QVBoxLayout()
        
        # Language and region group
        language_group = QGroupBox("اللغة والمنطقة")
        language_layout = QFormLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItem("العربية", "ar")
        self.language_combo.addItem("English", "en")
        
        language_layout.addRow("اللغة:", self.language_combo)
        
        language_group.setLayout(language_layout)
        layout.addWidget(language_group)
        
        # Notifications group
        notifications_group = QGroupBox("الإشعارات")
        notifications_layout = QVBoxLayout()
        
        self.enable_notifications_checkbox = QCheckBox("تفعيل الإشعارات")
        self.show_low_stock_checkbox = QCheckBox("إشعار المخزون المنخفض")
        self.show_overdue_repairs_checkbox = QCheckBox("إشعار الصيانة المتأخرة")
        self.play_sounds_checkbox = QCheckBox("تشغيل الأصوات")
        
        notifications_layout.addWidget(self.enable_notifications_checkbox)
        notifications_layout.addWidget(self.show_low_stock_checkbox)
        notifications_layout.addWidget(self.show_overdue_repairs_checkbox)
        notifications_layout.addWidget(self.play_sounds_checkbox)
        
        notifications_group.setLayout(notifications_layout)
        layout.addWidget(notifications_group)
        
        # Security group
        security_group = QGroupBox("الأمان")
        security_layout = QFormLayout()
        
        self.auto_lock_checkbox = QCheckBox("قفل تلقائي عند عدم النشاط")
        
        self.lock_timeout_input = QSpinBox()
        self.lock_timeout_input.setMinimum(1)
        self.lock_timeout_input.setMaximum(60)
        self.lock_timeout_input.setSuffix(" دقيقة")
        
        self.require_password_checkbox = QCheckBox("طلب كلمة مرور للعمليات الحساسة")
        
        security_layout.addRow("", self.auto_lock_checkbox)
        security_layout.addRow("مهلة القفل:", self.lock_timeout_input)
        security_layout.addRow("", self.require_password_checkbox)
        
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)
        
        # Performance group
        performance_group = QGroupBox("الأداء")
        performance_layout = QFormLayout()
        
        self.enable_animations_checkbox = QCheckBox("تفعيل الرسوم المتحركة")
        self.cache_size_input = QSpinBox()
        self.cache_size_input.setMinimum(10)
        self.cache_size_input.setMaximum(1000)
        self.cache_size_input.setSuffix(" MB")
        
        performance_layout.addRow("", self.enable_animations_checkbox)
        performance_layout.addRow("حجم التخزين المؤقت:", self.cache_size_input)
        
        performance_group.setLayout(performance_layout)
        layout.addWidget(performance_group)
        
        layout.addStretch()
        prefs_widget.setLayout(layout)
        self.tab_widget.addTab(prefs_widget, "التفضيلات")
        
    def setup_connections(self):
        """Setup signal connections"""
        # Shop tab
        self.browse_logo_btn.clicked.connect(self.browse_logo)
        self.remove_logo_btn.clicked.connect(self.remove_logo)
        
        # Database tab
        self.browse_db_btn.clicked.connect(self.browse_database)
        self.browse_backup_dir_btn.clicked.connect(self.browse_backup_dir)
        self.auto_backup_checkbox.toggled.connect(self.toggle_backup_settings)
        
        self.vacuum_db_btn.clicked.connect(self.vacuum_database)
        self.check_db_btn.clicked.connect(self.check_database)
        self.repair_db_btn.clicked.connect(self.repair_database)
        
        # Printer tab
        self.refresh_printers_btn.clicked.connect(self.refresh_printers)
        self.test_print_btn.clicked.connect(self.test_print)
        self.test_thermal_btn.clicked.connect(self.test_thermal_print)
        
        # UI tab
        self.theme_combo.currentTextChanged.connect(self.preview_theme)
        self.font_family_combo.currentTextChanged.connect(self.update_font_preview)
        self.font_size_input.valueChanged.connect(self.update_font_preview)
        self.change_font_btn.clicked.connect(self.change_font)
        
        # Action buttons
        self.save_btn.clicked.connect(self.save_settings)
        self.apply_btn.clicked.connect(self.apply_settings)
        self.cancel_btn.clicked.connect(self.close)
        self.reset_btn.clicked.connect(self.reset_settings)
        
    def load_current_settings(self):
        """Load current settings into the form"""
        try:
            # Shop settings
            self.shop_name_input.setText(settings.shop.name)
            self.shop_address_input.setPlainText(settings.shop.address)
            self.shop_phone_input.setText(settings.shop.phone)
            self.shop_email_input.setText(settings.shop.email)
            self.tax_number_input.setText(settings.shop.tax_number)
            self.tax_rate_input.setValue(settings.shop.tax_rate)
            self.currency_input.setText(settings.shop.currency)
            
            # Database settings
            self.db_path_input.setText(str(settings.get_database_path()))
            self.auto_backup_checkbox.setChecked(settings.database.auto_backup)
            self.backup_interval_input.setValue(settings.database.backup_interval)
            self.max_backups_input.setValue(settings.database.max_backups)
            self.backup_dir_input.setText(str(settings.get_backup_dir()))
            
            self.toggle_backup_settings(settings.database.auto_backup)
            
            # Printer settings
            self.default_printer_combo.setCurrentText(settings.printer.default_printer)
            self.thermal_printer_combo.setCurrentText(settings.printer.thermal_printer)
            self.page_size_combo.setCurrentText(settings.printer.page_size)
            self.margin_top_input.setValue(settings.printer.margin_top)
            self.margin_bottom_input.setValue(settings.printer.margin_bottom)
            self.margin_left_input.setValue(settings.printer.margin_left)
            self.margin_right_input.setValue(settings.printer.margin_right)
            
            # UI settings
            theme_index = self.theme_combo.findData(settings.ui.theme)
            if theme_index >= 0:
                self.theme_combo.setCurrentIndex(theme_index)
                
            self.font_family_combo.setCurrentText(settings.ui.font_family)
            self.font_size_input.setValue(settings.ui.font_size)
            self.window_width_input.setValue(settings.ui.window_size.get("width", 1200))
            self.window_height_input.setValue(settings.ui.window_size.get("height", 800))
            
            self.update_font_preview()
            
            # Load available printers
            self.refresh_printers()
            
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
            show_error(self, f"خطأ في تحميل الإعدادات:\n{str(e)}")
            
    def toggle_backup_settings(self, enabled: bool):
        """Toggle backup settings based on auto backup checkbox"""
        self.backup_interval_input.setEnabled(enabled)
        self.max_backups_input.setEnabled(enabled)
        
    def browse_logo(self):
        """Browse for logo file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف الشعار",
            "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.logo_path_input.setText(file_path)
            self.update_logo_preview(file_path)
            
    def remove_logo(self):
        """Remove current logo"""
        self.logo_path_input.clear()
        self.logo_preview.setText("لا يوجد شعار")
        self.logo_preview.setPixmap(QPixmap())
        
    def update_logo_preview(self, file_path: str):
        """Update logo preview"""
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.logo_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_preview.setPixmap(scaled_pixmap)
                self.logo_preview.setText("")
            else:
                self.logo_preview.setText("صورة غير صالحة")
        except Exception as e:
            self.logo_preview.setText("خطأ في تحميل الصورة")
            
    def browse_database(self):
        """Browse for database file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "اختر موقع قاعدة البيانات",
            str(settings.get_database_path()),
            "Database Files (*.db)"
        )
        
        if file_path:
            self.db_path_input.setText(file_path)
            
    def browse_backup_dir(self):
        """Browse for backup directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "اختر مجلد النسخ الاحتياطي",
            str(settings.get_backup_dir())
        )
        
        if dir_path:
            self.backup_dir_input.setText(dir_path)
            
    def refresh_printers(self):
        """Refresh printer lists"""
        # This would get available printers from the system
        # For now, add some common printer names
        printers = ["Default Printer", "HP LaserJet", "Canon PIXMA", "Epson Thermal"]
        
        current_default = self.default_printer_combo.currentText()
        current_thermal = self.thermal_printer_combo.currentText()
        
        self.default_printer_combo.clear()
        self.thermal_printer_combo.clear()
        self.thermal_printer_combo.addItem("لا توجد", None)
        
        for printer in printers:
            self.default_printer_combo.addItem(printer)
            self.thermal_printer_combo.addItem(printer)
            
        # Restore previous selections
        if current_default:
            index = self.default_printer_combo.findText(current_default)
            if index >= 0:
                self.default_printer_combo.setCurrentIndex(index)
                
        if current_thermal:
            index = self.thermal_printer_combo.findText(current_thermal)
            if index >= 0:
                self.thermal_printer_combo.setCurrentIndex(index)
                
    def test_print(self):
        """Test print a page"""
        show_error(self, "ميزة اختبار الطباعة قيد التطوير")
        
    def test_thermal_print(self):
        """Test thermal printer"""
        show_error(self, "ميزة اختبار الطباعة الحرارية قيد التطوير")
        
    def preview_theme(self):
        """Preview selected theme"""
        # This would apply theme preview
        pass
        
    def update_font_preview(self):
        """Update font preview"""
        family = self.font_family_combo.currentText()
        size = self.font_size_input.value()
        
        font = QFont(family, size)
        self.font_preview_label.setFont(font)
        
    def change_font(self):
        """Open font dialog"""
        current_font = self.font_preview_label.font()
        font, ok = QFontDialog.getFont(current_font, self)
        
        if ok:
            self.font_family_combo.setCurrentText(font.family())
            self.font_size_input.setValue(font.pointSize())
            self.update_font_preview()
            
    def vacuum_database(self):
        """Vacuum database to optimize storage"""
        reply = QMessageBox.question(
            self, "ضغط قاعدة البيانات",
            "هل تريد ضغط قاعدة البيانات؟\n"
            "هذا قد يستغرق عدة دقائق."
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            show_error(self, "ميزة ضغط قاعدة البيانات قيد التطوير")
            
    def check_database(self):
        """Check database integrity"""
        show_error(self, "ميزة فحص قاعدة البيانات قيد التطوير")
        
    def repair_database(self):
        """Repair database"""
        reply = QMessageBox.question(
            self, "إصلاح قاعدة البيانات",
            "هل تريد إصلاح قاعدة البيانات؟\n"
            "تأكد من عمل نسخة احتياطية أولاً."
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            show_error(self, "ميزة إصلاح قاعدة البيانات قيد التطوير")
            
    def save_settings(self):
        """Save all settings"""
        if self.apply_settings():
            settings.save()
            show_success(self, "تم حفظ الإعدادات بنجاح")
            self.settings_changed.emit()
            self.close()
            
    def apply_settings(self):
        """Apply settings without closing"""
        try:
            # Shop settings
            settings.shop.name = self.shop_name_input.text()
            settings.shop.address = self.shop_address_input.toPlainText()
            settings.shop.phone = self.shop_phone_input.text()
            settings.shop.email = self.shop_email_input.text()
            settings.shop.tax_number = self.tax_number_input.text()
            settings.shop.tax_rate = self.tax_rate_input.value()
            settings.shop.currency = self.currency_input.text()
            
            # Database settings
            settings.database.path = self.db_path_input.text()
            settings.database.auto_backup = self.auto_backup_checkbox.isChecked()
            settings.database.backup_interval = self.backup_interval_input.value()
            settings.database.max_backups = self.max_backups_input.value()
            settings.database.backup_dir = self.backup_dir_input.text()
            
            # Printer settings
            settings.printer.default_printer = self.default_printer_combo.currentText()
            settings.printer.thermal_printer = self.thermal_printer_combo.currentText()
            settings.printer.page_size = self.page_size_combo.currentText()
            settings.printer.margin_top = self.margin_top_input.value()
            settings.printer.margin_bottom = self.margin_bottom_input.value()
            settings.printer.margin_left = self.margin_left_input.value()
            settings.printer.margin_right = self.margin_right_input.value()
            
            # UI settings
            settings.ui.theme = self.theme_combo.currentData()
            settings.ui.font_family = self.font_family_combo.currentText()
            settings.ui.font_size = self.font_size_input.value()
            settings.ui.window_size = {
                "width": self.window_width_input.value(),
                "height": self.window_height_input.value()
            }
            
            show_success(self, "تم تطبيق الإعدادات بنجاح")
            self.settings_changed.emit()
            return True
            
        except Exception as e:
            logging.error(f"Error applying settings: {e}")
            show_error(self, f"خطأ في تطبيق الإعدادات:\n{str(e)}")
            return False
            
    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self, "إعادة تعيين الإعدادات",
            "هل تريد إعادة تعيين جميع الإعدادات إلى القيم الافتراضية؟"
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset to default values
            self.load_current_settings()
            show_success(self, "تم إعادة تعيين الإعدادات")
