# -*- coding: utf-8 -*-
"""
Main window for Al-Hussiny Mobile Shop POS System
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QPushButton, QLabel, QFrame, QSplitter, QScrollArea,
                            QMenuBar, QMenu, QToolBar, QStatusBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont
import logging

from .base_window import BaseWindow
from .dashboard_window import DashboardWindow
from .inventory_window import InventoryWindow
from .sales_window import SalesWindow
from .repairs_window import RepairsWindow
from .reports_window import ReportsWindow
from .users_window import UsersWindow
from .widgets.search_widget import GlobalSearchWidget
from config import Config

logger = logging.getLogger(__name__)

class MainWindow(BaseWindow):
    """Main application window with navigation and module access"""
    
    # Signals
    logout_requested = pyqtSignal()
    
    def __init__(self, db_manager, user_data):
        super().__init__(db_manager, user_data)
        
        self.child_windows = {}
        self.setup_main_window()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.refresh_data()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
        
    def setup_main_window(self):
        """Setup main window properties"""
        self.set_title("محل الحسيني - نظام إدارة المبيعات والمخزون")
        self.setMinimumSize(*Config.MAIN_WINDOW_MIN_SIZE)
        self.center_on_screen()
        
        # Setup main content
        self.setup_main_content()
        
    def setup_main_content(self):
        """Setup main content area"""
        # Main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Welcome section
        self.setup_welcome_section(content_layout)
        
        # Quick actions grid
        self.setup_quick_actions(content_layout)
        
        # Statistics section
        self.setup_statistics(content_layout)
        
        # Make content scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Set central widget
        self.setCentralWidget(scroll_area)
    
    def setup_welcome_section(self, layout):
        """Setup welcome section"""
        welcome_frame = QFrame()
        welcome_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        welcome_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #4e73df, stop: 1 #224abe);
                border-radius: 10px;
                color: white;
                padding: 20px;
            }
        """)
        
        welcome_layout = QVBoxLayout(welcome_frame)
        
        # Welcome message
        welcome_label = QLabel(f"مرحباً {self.user_data['name']}")
        welcome_font = QFont()
        welcome_font.setPointSize(16)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_label.setStyleSheet("color: white;")
        
        # Date and time
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        time_label = QLabel(f"التاريخ والوقت: {current_time}")
        time_label.setStyleSheet("color: #e3e6f0; font-size: 12pt;")
        
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addWidget(time_label)
        
        layout.addWidget(welcome_frame)
    
    def setup_quick_actions(self, layout):
        """Setup quick actions grid"""
        actions_frame = QFrame()
        actions_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fc;
                border: 1px solid #e3e6f0;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        actions_layout = QVBoxLayout(actions_frame)
        
        # Title
        title_label = QLabel("الوظائف الرئيسية")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #5a5c69; margin-bottom: 15px;")
        
        actions_layout.addWidget(title_label)
        
        # Actions grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        # Define actions with permissions
        actions = [
            ("لوحة التحكم", "dashboard", "all", self.open_dashboard),
            ("المبيعات", "sales", "sales", self.open_sales),
            ("المخزون", "inventory", "inventory", self.open_inventory),
            ("الصيانة", "repairs", "repairs", self.open_repairs),
            ("التقارير", "reports", "reports", self.open_reports),
            ("إدارة المستخدمين", "users", "users", self.open_users),
        ]
        
        row, col = 0, 0
        for name, icon, permission, callback in actions:
            if self.has_permission(permission):
                button = self.create_action_button(name, callback)
                grid_layout.addWidget(button, row, col)
                
                col += 1
                if col >= 3:  # 3 columns
                    col = 0
                    row += 1
        
        actions_layout.addLayout(grid_layout)
        layout.addWidget(actions_frame)
    
    def create_action_button(self, text, callback):
        """Create styled action button"""
        button = QPushButton(text)
        button.setMinimumSize(200, 80)
        button.setStyleSheet("""
            QPushButton {
                background-color: #4e73df;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2e59d9;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
            }
        """)
        button.clicked.connect(callback)
        return button
    
    def setup_statistics(self, layout):
        """Setup statistics section"""
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fc;
                border: 1px solid #e3e6f0;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        stats_layout = QVBoxLayout(stats_frame)
        
        # Title
        title_label = QLabel("إحصائيات سريعة")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #5a5c69; margin-bottom: 15px;")
        
        stats_layout.addWidget(title_label)
        
        # Stats grid
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(10)
        
        # Initialize stats widgets
        self.stats_widgets = {}
        self.create_stat_widget("مبيعات اليوم", "0", "#1cc88a", 0, 0)
        self.create_stat_widget("المنتجات", "0", "#36b9cc", 0, 1)
        self.create_stat_widget("الصيانات المعلقة", "0", "#f6c23e", 1, 0)
        self.create_stat_widget("المنتجات المنخفضة", "0", "#e74a3b", 1, 1)
        
        stats_layout.addLayout(self.stats_grid)
        layout.addWidget(stats_frame)
    
    def create_stat_widget(self, title, value, color, row, col):
        """Create statistics widget"""
        stat_frame = QFrame()
        stat_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 15px;
                min-height: 80px;
            }}
        """)
        
        stat_layout = QVBoxLayout(stat_frame)
        
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 11pt;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        stat_layout.addWidget(value_label)
        stat_layout.addWidget(title_label)
        
        self.stats_widgets[title] = value_label
        self.stats_grid.addWidget(stat_frame, row, col)
    
    def setup_menu_bar(self):
        """Setup application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("ملف")
        
        # Backup submenu
        backup_menu = file_menu.addMenu("النسخ الاحتياطي")
        
        backup_action = QAction("إنشاء نسخة احتياطية", self)
        backup_action.triggered.connect(self.create_backup)
        backup_menu.addAction(backup_action)
        
        restore_action = QAction("استعادة نسخة احتياطية", self)
        restore_action.triggered.connect(self.restore_backup)
        backup_menu.addAction(restore_action)
        
        file_menu.addSeparator()
        
        # Logout action
        logout_action = QAction("تسجيل الخروج", self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        # Exit action
        exit_action = QAction("خروج", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("أدوات")
        
        settings_action = QAction("الإعدادات", self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("مساعدة")
        
        about_action = QAction("حول البرنامج", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Setup application toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Global search widget
        self.search_widget = GlobalSearchWidget(self.db_manager)
        self.search_widget.result_selected.connect(self.handle_search_result)
        toolbar.addWidget(self.search_widget)
        
        toolbar.addSeparator()
        
        # Quick action buttons
        if self.has_permission("sales"):
            new_sale_action = QAction("مبيعة جديدة", self)
            new_sale_action.triggered.connect(self.new_sale)
            toolbar.addAction(new_sale_action)
        
        if self.has_permission("inventory"):
            new_product_action = QAction("منتج جديد", self)
            new_product_action.triggered.connect(self.new_product)
            toolbar.addAction(new_product_action)
        
        toolbar.addSeparator()
        
        # Refresh action
        refresh_action = QAction("تحديث", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
    
    def refresh_data(self):
        """Refresh dashboard statistics"""
        try:
            session = self.db_manager.get_session()
            
            # Get today's sales
            from datetime import datetime, timedelta
            from models import Sale, Product, Repair
            
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            today_sales = session.query(Sale).filter(
                Sale.created_at >= today_start,
                Sale.created_at <= today_end
            ).count()
            
            # Get product count
            product_count = session.query(Product).filter_by(active=True).count()
            
            # Get pending repairs
            pending_repairs = session.query(Repair).filter(
                ~Repair.status.in_(['تم التسليم', 'غير قابل للإصلاح'])
            ).count()
            
            # Get low stock products
            low_stock_count = session.query(Product).filter(
                Product.quantity <= Product.min_quantity,
                Product.active == True
            ).count()
            
            # Update statistics widgets
            if "مبيعات اليوم" in self.stats_widgets:
                self.stats_widgets["مبيعات اليوم"].setText(str(today_sales))
            
            if "المنتجات" in self.stats_widgets:
                self.stats_widgets["المنتجات"].setText(str(product_count))
            
            if "الصيانات المعلقة" in self.stats_widgets:
                self.stats_widgets["الصيانات المعلقة"].setText(str(pending_repairs))
            
            if "المنتجات المنخفضة" in self.stats_widgets:
                self.stats_widgets["المنتجات المنخفضة"].setText(str(low_stock_count))
            
            self.update_status("تم تحديث البيانات")
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث البيانات: {e}")
        finally:
            if 'session' in locals():
                session.close()
    
    # Window opening methods
    def open_dashboard(self):
        """Open dashboard window"""
        self.open_child_window("dashboard", DashboardWindow)
    
    def open_sales(self):
        """Open sales window"""
        self.open_child_window("sales", SalesWindow)
    
    def open_inventory(self):
        """Open inventory window"""
        self.open_child_window("inventory", InventoryWindow)
    
    def open_repairs(self):
        """Open repairs window"""
        self.open_child_window("repairs", RepairsWindow)
    
    def open_reports(self):
        """Open reports window"""
        self.open_child_window("reports", ReportsWindow)
    
    def open_users(self):
        """Open users window"""
        if self.require_permission("users", "إدارة المستخدمين"):
            self.open_child_window("users", UsersWindow)
    
    def open_child_window(self, window_key, window_class):
        """Open or focus child window"""
        try:
            if window_key in self.child_windows:
                # Window already exists, bring to front
                window = self.child_windows[window_key]
                window.show()
                window.raise_()
                window.activateWindow()
            else:
                # Create new window
                window = window_class(self.db_manager, self.user_data)
                window.window_closing.connect(lambda: self.child_windows.pop(window_key, None))
                self.child_windows[window_key] = window
                window.show()
                
        except Exception as e:
            self.logger.error(f"خطأ في فتح النافذة {window_key}: {e}")
            self.show_message(f"خطأ في فتح النافذة: {str(e)}", "error")
    
    def new_sale(self):
        """Create new sale"""
        if self.require_permission("sales", "إنشاء مبيعة جديدة"):
            self.open_sales()
            # TODO: Signal to sales window to create new sale
    
    def new_product(self):
        """Create new product"""
        if self.require_permission("inventory", "إضافة منتج جديد"):
            self.open_inventory()
            # TODO: Signal to inventory window to create new product
    
    def handle_search_result(self, result):
        """Handle global search result selection"""
        try:
            result_type = result.get("type")
            
            if result_type == "منتج":
                self.open_inventory()
                # TODO: Signal to inventory window to show product
            elif result_type == "فاتورة":
                self.open_sales()
                # TODO: Signal to sales window to show sale
            elif result_type == "صيانة":
                self.open_repairs()
                # TODO: Signal to repairs window to show repair
                
        except Exception as e:
            self.logger.error(f"خطأ في معالجة نتيجة البحث: {e}")
    
    def create_backup(self):
        """Create database backup"""
        try:
            backup_path = self.db_manager.backup_database()
            if backup_path:
                self.show_message(f"تم إنشاء النسخة الاحتياطية بنجاح:\n{backup_path}", "success")
                self.log_action("create_backup", f"نسخة احتياطية: {backup_path}")
            else:
                self.show_message("فشل في إنشاء النسخة الاحتياطية", "error")
                
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            self.show_message(f"خطأ في إنشاء النسخة الاحتياطية:\n{str(e)}", "error")
    
    def restore_backup(self):
        """Restore database from backup"""
        from PyQt6.QtWidgets import QFileDialog
        
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "اختر ملف النسخة الاحتياطية",
                str(Config.DB_BACKUP_DIR),
                "Database Files (*.db);;All Files (*)"
            )
            
            if file_path:
                if self.show_question(
                    "هل أنت متأكد من استعادة النسخة الاحتياطية؟\n"
                    "سيتم استبدال قاعدة البيانات الحالية."
                ):
                    if self.db_manager.restore_database(file_path):
                        self.show_message("تم استعادة النسخة الاحتياطية بنجاح", "success")
                        self.log_action("restore_backup", f"استعادة من: {file_path}")
                        self.refresh_data()
                    else:
                        self.show_message("فشل في استعادة النسخة الاحتياطية", "error")
                        
        except Exception as e:
            self.logger.error(f"خطأ في استعادة النسخة الاحتياطية: {e}")
            self.show_message(f"خطأ في استعادة النسخة الاحتياطية:\n{str(e)}", "error")
    
    def open_settings(self):
        """Open settings dialog"""
        # TODO: Implement settings dialog
        self.show_message("إعدادات التطبيق ستكون متاحة قريباً", "info")
    
    def show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox
        
        about_text = f"""
        {Config.APP_NAME}
        الإصدار: {Config.APP_VERSION}
        
        نظام إدارة المبيعات والمخزون لمحلات الهواتف المحمولة
        
        تم التطوير بواسطة: {Config.APP_AUTHOR}
        """
        
        QMessageBox.about(self, "حول البرنامج", about_text)
    
    def logout(self):
        """Handle user logout"""
        if self.show_question("هل تريد تسجيل الخروج؟"):
            self.log_action("logout", "تسجيل خروج المستخدم")
            
            # Close all child windows
            for window in list(self.child_windows.values()):
                window.close()
            self.child_windows.clear()
            
            # Stop refresh timer
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()
            
            self.logout_requested.emit()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.show_question("هل تريد إغلاق البرنامج؟"):
            # Close all child windows
            for window in list(self.child_windows.values()):
                window.close()
            
            # Stop refresh timer
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()
            
            event.accept()
        else:
            event.ignore()
