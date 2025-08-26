from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
                            QComboBox, QCheckBox, QTextEdit, QFormLayout, QGroupBox,
                            QTabWidget, QFileDialog, QMessageBox, QColorDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from config.settings import app_settings
from ui.styles import get_stylesheet

class SettingsWindow(QMainWindow):
    """Application settings and configuration window"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        
        self.setup_ui()
        self.apply_styles()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("إعدادات النظام")
        self.setMinimumSize(800, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("إعدادات النظام")
        title_label.setFont(QFont("Noto Sans Arabic", 18, QFont.Weight.Bold))
        title_label.setObjectName("title-label")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Tab widget for different settings categories
        self.tabs = QTabWidget()
        
        # Shop info tab
        self.shop_tab = self.create_shop_info_tab()
        self.tabs.addTab(self.shop_tab, "معلومات المحل")
        
        # Invoice settings tab
        self.invoice_tab = self.create_invoice_tab()
        self.tabs.addTab(self.invoice_tab, "إعدادات الفواتير")
        
        # UI settings tab
        self.ui_tab = self.create_ui_tab()
        self.tabs.addTab(self.ui_tab, "واجهة المستخدم")
        
        # Backup settings tab
        self.backup_tab = self.create_backup_tab()
        self.tabs.addTab(self.backup_tab, "النسخ الاحتياطي")
        
        # Printer settings tab
        self.printer_tab = self.create_printer_tab()
        self.tabs.addTab(self.printer_tab, "الطابعة")
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("حفظ الإعدادات")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.reset_btn = QPushButton("استعادة الافتراضي")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.clicked.connect(self.close)
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        
        # Add layouts to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(buttons_layout)
        
        central_widget.setLayout(main_layout)
    
    def create_shop_info_tab(self):
        """Create shop information tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Shop info group
        shop_group = QGroupBox("معلومات المحل")
        shop_layout = QFormLayout()
        
        self.shop_name_input = QLineEdit()
        self.shop_address_input = QTextEdit()
        self.shop_address_input.setMaximumHeight(80)
        self.shop_phone_input = QLineEdit()
        self.shop_email_input = QLineEdit()
        
        shop_layout.addRow("اسم المحل:", self.shop_name_input)
        shop_layout.addRow("العنوان:", self.shop_address_input)
        shop_layout.addRow("رقم الهاتف:", self.shop_phone_input)
        shop_layout.addRow("البريد الإلكتروني:", self.shop_email_input)
        
        shop_group.setLayout(shop_layout)
        
        # Logo section
        logo_group = QGroupBox("شعار المحل")
        logo_layout = QHBoxLayout()
        
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setReadOnly(True)
        
        self.browse_logo_btn = QPushButton("تصفح")
        self.browse_logo_btn.clicked.connect(self.browse_logo)
        
        self.remove_logo_btn = QPushButton("إزالة")
        self.remove_logo_btn.clicked.connect(self.remove_logo)
        
        logo_layout.addWidget(QLabel("مسار الشعار:"))
        logo_layout.addWidget(self.logo_path_input)
        logo_layout.addWidget(self.browse_logo_btn)
        logo_layout.addWidget(self.remove_logo_btn)
        
        logo_group.setLayout(logo_layout)
        
        layout.addWidget(shop_group)
        layout.addWidget(logo_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_invoice_tab(self):
        """Create invoice settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Tax and currency group
        tax_group = QGroupBox("الضريبة والعملة")
        tax_layout = QFormLayout()
        
        self.tax_rate_input = QDoubleSpinBox()
        self.tax_rate_input.setDecimals(2)
        self.tax_rate_input.setMaximum(100.0)
        self.tax_rate_input.setSuffix("%")
        
        self.currency_input = QLineEdit()
        
        tax_layout.addRow("معدل الضريبة:", self.tax_rate_input)
        tax_layout.addRow("العملة:", self.currency_input)
        
        tax_group.setLayout(tax_layout)
        
        # Invoice template group
        template_group = QGroupBox("قالب الفاتورة")
        template_layout = QFormLayout()
        
        self.footer_text_input = QTextEdit()
        self.footer_text_input.setMaximumHeight(100)
        
        self.invoice_notes_input = QTextEdit()
        self.invoice_notes_input.setMaximumHeight(80)
        
        template_layout.addRow("نص التذييل:", self.footer_text_input)
        template_layout.addRow("ملاحظات افتراضية:", self.invoice_notes_input)
        
        template_group.setLayout(template_layout)
        
        # Invoice numbering
        numbering_group = QGroupBox("ترقيم الفواتير")
        numbering_layout = QFormLayout()
        
        self.invoice_prefix_input = QLineEdit()
        
        self.next_invoice_number_input = QSpinBox()
        self.next_invoice_number_input.setMinimum(1)
        self.next_invoice_number_input.setMaximum(999999)
        
        numbering_layout.addRow("بادئة رقم الفاتورة:", self.invoice_prefix_input)
        numbering_layout.addRow("الرقم التالي:", self.next_invoice_number_input)
        
        numbering_group.setLayout(numbering_layout)
        
        layout.addWidget(tax_group)
        layout.addWidget(template_group)
        layout.addWidget(numbering_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_ui_tab(self):
        """Create UI settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Theme group
        theme_group = QGroupBox("المظهر")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["فاتح", "داكن"])
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["العربية", "English"])
        
        self.font_size_input = QSpinBox()
        self.font_size_input.setMinimum(8)
        self.font_size_input.setMaximum(24)
        
        theme_layout.addRow("المظهر:", self.theme_combo)
        theme_layout.addRow("اللغة:", self.language_combo)
        theme_layout.addRow("حجم الخط:", self.font_size_input)
        
        theme_group.setLayout(theme_layout)
        
        # Color customization group
        color_group = QGroupBox("تخصيص الألوان")
        color_layout = QFormLayout()
        
        self.primary_color_btn = QPushButton("اختيار اللون الأساسي")
        self.primary_color_btn.clicked.connect(lambda: self.choose_color("primary"))
        
        self.accent_color_btn = QPushButton("اختيار اللون المميز")
        self.accent_color_btn.clicked.connect(lambda: self.choose_color("accent"))
        
        color_layout.addRow("اللون الأساسي:", self.primary_color_btn)
        color_layout.addRow("اللون المميز:", self.accent_color_btn)
        
        color_group.setLayout(color_layout)
        
        # Window settings
        window_group = QGroupBox("إعدادات النوافذ")
        window_layout = QFormLayout()
        
        self.remember_window_size = QCheckBox("تذكر حجم النوافذ")
        self.remember_window_position = QCheckBox("تذكر مكان النوافذ")
        self.auto_maximize = QCheckBox("تكبير النوافذ تلقائياً")
        
        window_layout.addRow("", self.remember_window_size)
        window_layout.addRow("", self.remember_window_position)
        window_layout.addRow("", self.auto_maximize)
        
        window_group.setLayout(window_layout)
        
        layout.addWidget(theme_group)
        layout.addWidget(color_group)
        layout.addWidget(window_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_backup_tab(self):
        """Create backup settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Auto backup group
        auto_backup_group = QGroupBox("النسخ الاحتياطي التلقائي")
        auto_backup_layout = QFormLayout()
        
        self.auto_backup_enabled = QCheckBox("تفعيل النسخ الاحتياطي التلقائي")
        
        self.backup_frequency_combo = QComboBox()
        self.backup_frequency_combo.addItems(["يومي", "أسبوعي", "شهري"])
        
        self.max_backups_input = QSpinBox()
        self.max_backups_input.setMinimum(1)
        self.max_backups_input.setMaximum(365)
        
        self.backup_location_input = QLineEdit()
        self.backup_location_input.setReadOnly(True)
        
        self.browse_backup_btn = QPushButton("تصفح")
        self.browse_backup_btn.clicked.connect(self.browse_backup_location)
        
        backup_location_layout = QHBoxLayout()
        backup_location_layout.addWidget(self.backup_location_input)
        backup_location_layout.addWidget(self.browse_backup_btn)
        
        auto_backup_layout.addRow("", self.auto_backup_enabled)
        auto_backup_layout.addRow("التكرار:", self.backup_frequency_combo)
        auto_backup_layout.addRow("الحد الأقصى للنسخ:", self.max_backups_input)
        auto_backup_layout.addRow("مكان الحفظ:", backup_location_layout)
        
        auto_backup_group.setLayout(auto_backup_layout)
        
        # Cloud sync group
        cloud_group = QGroupBox("المزامنة السحابية")
        cloud_layout = QFormLayout()
        
        self.cloud_sync_enabled = QCheckBox("تفعيل المزامنة السحابية")
        
        self.cloud_provider_combo = QComboBox()
        self.cloud_provider_combo.addItems(["محلي فقط", "OneDrive", "Google Drive", "Dropbox"])
        
        self.cloud_folder_input = QLineEdit()
        self.cloud_folder_input.setReadOnly(True)
        
        self.browse_cloud_btn = QPushButton("تصفح")
        self.browse_cloud_btn.clicked.connect(self.browse_cloud_folder)
        
        cloud_folder_layout = QHBoxLayout()
        cloud_folder_layout.addWidget(self.cloud_folder_input)
        cloud_folder_layout.addWidget(self.browse_cloud_btn)
        
        cloud_layout.addRow("", self.cloud_sync_enabled)
        cloud_layout.addRow("مزود الخدمة:", self.cloud_provider_combo)
        cloud_layout.addRow("مجلد المزامنة:", cloud_folder_layout)
        
        cloud_group.setLayout(cloud_layout)
        
        layout.addWidget(auto_backup_group)
        layout.addWidget(cloud_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_printer_tab(self):
        """Create printer settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Default printer group
        printer_group = QGroupBox("الطابعة الافتراضية")
        printer_layout = QFormLayout()
        
        self.printer_name_combo = QComboBox()
        self.load_printers()
        
        self.printer_type_combo = QComboBox()
        self.printer_type_combo.addItems(["عادية (A4)", "حرارية"])
        
        printer_layout.addRow("اسم الطابعة:", self.printer_name_combo)
        printer_layout.addRow("نوع الطابعة:", self.printer_type_combo)
        
        printer_group.setLayout(printer_layout)
        
        # Thermal printer group
        thermal_group = QGroupBox("إعدادات الطابعة الحرارية")
        thermal_layout = QFormLayout()
        
        self.paper_width_input = QSpinBox()
        self.paper_width_input.setMinimum(50)
        self.paper_width_input.setMaximum(120)
        self.paper_width_input.setSuffix(" مم")
        
        self.cut_paper_checkbox = QCheckBox("قطع الورق تلقائياً")
        self.print_logo_checkbox = QCheckBox("طباعة الشعار")
        
        thermal_layout.addRow("عرض الورق:", self.paper_width_input)
        thermal_layout.addRow("", self.cut_paper_checkbox)
        thermal_layout.addRow("", self.print_logo_checkbox)
        
        thermal_group.setLayout(thermal_layout)
        
        # Print settings group
        print_settings_group = QGroupBox("إعدادات الطباعة")
        print_settings_layout = QFormLayout()
        
        self.auto_print_checkbox = QCheckBox("طباعة تلقائية بعد الحفظ")
        self.print_copies_input = QSpinBox()
        self.print_copies_input.setMinimum(1)
        self.print_copies_input.setMaximum(10)
        
        print_settings_layout.addRow("", self.auto_print_checkbox)
        print_settings_layout.addRow("عدد النسخ:", self.print_copies_input)
        
        print_settings_group.setLayout(print_settings_layout)
        
        layout.addWidget(printer_group)
        layout.addWidget(thermal_group)
        layout.addWidget(print_settings_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(get_stylesheet("light"))
    
    def load_printers(self):
        """Load available printers"""
        try:
            import win32print
            printers = win32print.EnumPrinters(2)
            self.printer_name_combo.clear()
            self.printer_name_combo.addItem("الافتراضي")
            
            for printer in printers:
                self.printer_name_combo.addItem(printer[2])
        except ImportError:
            self.printer_name_combo.addItem("الافتراضي")
        except Exception:
            self.printer_name_combo.addItem("الافتراضي")
    
    def load_settings(self):
        """Load current settings into UI"""
        try:
            # Shop info
            self.shop_name_input.setText(app_settings.get('shop_info.name', ''))
            self.shop_address_input.setPlainText(app_settings.get('shop_info.address', ''))
            self.shop_phone_input.setText(app_settings.get('shop_info.phone', ''))
            self.shop_email_input.setText(app_settings.get('shop_info.email', ''))
            
            # Invoice settings
            self.tax_rate_input.setValue(app_settings.get('invoice.tax_rate', 14.0))
            self.currency_input.setText(app_settings.get('invoice.currency', 'جنيه مصري'))
            self.footer_text_input.setPlainText(app_settings.get('invoice.footer_text', ''))
            
            # UI settings
            theme = app_settings.get('ui.theme', 'light')
            self.theme_combo.setCurrentText("فاتح" if theme == "light" else "داكن")
            
            self.font_size_input.setValue(app_settings.get('ui.font_size', 10))
            
            # Backup settings
            self.auto_backup_enabled.setChecked(app_settings.get('backup.auto_backup', True))
            
            frequency = app_settings.get('backup.backup_frequency', 'daily')
            frequency_map = {'daily': 'يومي', 'weekly': 'أسبوعي', 'monthly': 'شهري'}
            self.backup_frequency_combo.setCurrentText(frequency_map.get(frequency, 'يومي'))
            
            self.max_backups_input.setValue(app_settings.get('backup.max_backups', 30))
            
            # Printer settings
            printer_name = app_settings.get('printer.printer_name', '')
            if printer_name:
                index = self.printer_name_combo.findText(printer_name)
                if index >= 0:
                    self.printer_name_combo.setCurrentIndex(index)
            
            thermal = app_settings.get('printer.thermal_printer', False)
            self.printer_type_combo.setCurrentText("حرارية" if thermal else "عادية (A4)")
            
            self.paper_width_input.setValue(app_settings.get('printer.paper_width', 80))
            self.cut_paper_checkbox.setChecked(app_settings.get('printer.cut_paper', True))
            self.print_logo_checkbox.setChecked(app_settings.get('printer.print_logo', True))
            self.auto_print_checkbox.setChecked(app_settings.get('printer.auto_print', False))
            self.print_copies_input.setValue(app_settings.get('printer.copies', 1))
            
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"خطأ في تحميل الإعدادات: {str(e)}")
    
    def save_settings(self):
        """Save all settings"""
        try:
            # Shop info
            app_settings.set('shop_info.name', self.shop_name_input.text())
            app_settings.set('shop_info.address', self.shop_address_input.toPlainText())
            app_settings.set('shop_info.phone', self.shop_phone_input.text())
            app_settings.set('shop_info.email', self.shop_email_input.text())
            
            # Invoice settings
            app_settings.set('invoice.tax_rate', self.tax_rate_input.value())
            app_settings.set('invoice.currency', self.currency_input.text())
            app_settings.set('invoice.footer_text', self.footer_text_input.toPlainText())
            
            # UI settings
            theme = "light" if self.theme_combo.currentText() == "فاتح" else "dark"
            app_settings.set('ui.theme', theme)
            app_settings.set('ui.font_size', self.font_size_input.value())
            
            # Backup settings
            app_settings.set('backup.auto_backup', self.auto_backup_enabled.isChecked())
            
            frequency_map = {'يومي': 'daily', 'أسبوعي': 'weekly', 'شهري': 'monthly'}
            frequency = frequency_map.get(self.backup_frequency_combo.currentText(), 'daily')
            app_settings.set('backup.backup_frequency', frequency)
            
            app_settings.set('backup.max_backups', self.max_backups_input.value())
            
            # Printer settings
            app_settings.set('printer.printer_name', self.printer_name_combo.currentText())
            app_settings.set('printer.thermal_printer', self.printer_type_combo.currentText() == "حرارية")
            app_settings.set('printer.paper_width', self.paper_width_input.value())
            app_settings.set('printer.cut_paper', self.cut_paper_checkbox.isChecked())
            app_settings.set('printer.print_logo', self.print_logo_checkbox.isChecked())
            app_settings.set('printer.auto_print', self.auto_print_checkbox.isChecked())
            app_settings.set('printer.copies', self.print_copies_input.value())
            
            QMessageBox.information(self, "نجح", "تم حفظ الإعدادات بنجاح")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حفظ الإعدادات: {str(e)}")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            'تأكيد',
            'هل أنت متأكد من إعادة جميع الإعدادات إلى الوضع الافتراضي؟',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Reset settings to defaults
                app_settings.settings = app_settings.default_settings.copy()
                app_settings.save_settings()
                
                # Reload UI
                self.load_settings()
                
                QMessageBox.information(self, "نجح", "تم إعادة الإعدادات إلى الوضع الافتراضي")
                
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في إعادة تعيين الإعدادات: {str(e)}")
    
    def browse_logo(self):
        """Browse for logo file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "اختيار شعار المحل",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if file_path:
            self.logo_path_input.setText(file_path)
            app_settings.set('shop_info.logo_path', file_path)
    
    def remove_logo(self):
        """Remove logo"""
        self.logo_path_input.clear()
        app_settings.set('shop_info.logo_path', '')
    
    def browse_backup_location(self):
        """Browse for backup location"""
        folder_dialog = QFileDialog()
        folder_path = folder_dialog.getExistingDirectory(
            self,
            "اختيار مجلد النسخ الاحتياطي"
        )
        
        if folder_path:
            self.backup_location_input.setText(folder_path)
            app_settings.set('backup.location', folder_path)
    
    def browse_cloud_folder(self):
        """Browse for cloud sync folder"""
        folder_dialog = QFileDialog()
        folder_path = folder_dialog.getExistingDirectory(
            self,
            "اختيار مجلد المزامنة السحابية"
        )
        
        if folder_path:
            self.cloud_folder_input.setText(folder_path)
            app_settings.set('backup.cloud_folder', folder_path)
    
    def choose_color(self, color_type):
        """Choose color for UI customization"""
        color = QColorDialog.getColor(Qt.GlobalColor.blue, self)
        
        if color.isValid():
            color_hex = color.name()
            app_settings.set(f'ui.{color_type}_color', color_hex)
            
            # Update button color to show selection
            button = self.primary_color_btn if color_type == "primary" else self.accent_color_btn
            button.setStyleSheet(f"background-color: {color_hex}; color: white;")
