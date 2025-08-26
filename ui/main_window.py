from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QPushButton, QMenuBar, QStatusBar, QGridLayout,
                            QFrame, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction

from ui.inventory_window import InventoryWindow
from ui.sales_window import SalesWindow
from ui.repair_window import RepairWindow
from ui.transfer_window import TransferWindow
from ui.reports_window import ReportsWindow
from ui.user_management_window import UserManagementWindow
from ui.settings_window import SettingsWindow
from ui.backup_window import BackupWindow
from ui.styles import get_stylesheet
from utils.search_service import SearchService
from services.report_service import ReportService

class MainWindow(QMainWindow):
    """Main application window with dashboard"""
    
    closed = pyqtSignal()
    
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.search_service = SearchService()
        self.report_service = ReportService()
        self.child_windows = []
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.apply_styles()
        self.load_dashboard_data()
        
        # Setup timer for auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_dashboard_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle(f"نظام إدارة محل الحسيني - {self.current_user.name}")
        self.setMinimumSize(1200, 800)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Center widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section with search
        header_layout = QHBoxLayout()
        
        # Welcome label
        welcome_label = QLabel(f"مرحباً، {self.current_user.name}")
        welcome_label.setFont(QFont("Noto Sans Arabic", 16, QFont.Weight.Bold))
        welcome_label.setObjectName("title-label")
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("البحث السريع:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث في المنتجات، الفواتير، العملاء...")
        self.search_input.textChanged.connect(self.perform_search)
        self.search_input.setMaximumWidth(300)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        header_layout.addWidget(welcome_label)
        header_layout.addStretch()
        header_layout.addLayout(search_layout)
        
        # Dashboard cards
        dashboard_layout = QGridLayout()
        self.create_dashboard_cards(dashboard_layout)
        
        # Main menu buttons
        menu_layout = QGridLayout()
        self.create_menu_buttons(menu_layout)
        
        # Add layouts to main layout
        main_layout.addLayout(header_layout)
        main_layout.addLayout(dashboard_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(menu_layout)
        main_layout.addStretch()
        
        central_widget.setLayout(main_layout)
    
    def create_dashboard_cards(self, layout):
        """Create dashboard summary cards"""
        # Today's sales card
        self.sales_card = self.create_info_card("مبيعات اليوم", "0.00 جنيه", "#5E81AC")
        
        # Low stock card
        self.stock_card = self.create_info_card("منتجات منخفضة المخزون", "0", "#EBCB8B")
        
        # Pending repairs card
        self.repairs_card = self.create_info_card("أجهزة قيد الصيانة", "0", "#BF616A")
        
        # Total products card
        self.products_card = self.create_info_card("إجمالي المنتجات", "0", "#A3BE8C")
        
        layout.addWidget(self.sales_card, 0, 0)
        layout.addWidget(self.stock_card, 0, 1)
        layout.addWidget(self.repairs_card, 0, 2)
        layout.addWidget(self.products_card, 0, 3)
    
    def create_info_card(self, title, value, color):
        """Create an information card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                border-left: 4px solid {color};
            }}
        """)
        card.setMinimumHeight(100)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Noto Sans Arabic", 11, QFont.Weight.Bold))
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Noto Sans Arabic", 18, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        
        return card
    
    def create_menu_buttons(self, layout):
        """Create main menu buttons"""
        buttons = [
            ("إدارة المخزون", self.open_inventory_window, "inventory"),
            ("المبيعات والفواتير", self.open_sales_window, "sales"),
            ("خدمة الصيانة", self.open_repair_window, "repairs"),
            ("تحويلات الرصيد", self.open_transfer_window, "transfers"),
            ("التقارير", self.open_reports_window, "reports"),
            ("إدارة المستخدمين", self.open_user_management_window, "users"),
            ("الإعدادات", self.open_settings_window, "settings"),
            ("النسخ الاحتياطي", self.open_backup_window, "backup")
        ]
        
        row = 0
        col = 0
        for text, handler, permission in buttons:
            if self.has_permission(permission):
                button = QPushButton(text)
                button.setFont(QFont("Noto Sans Arabic", 12, QFont.Weight.Bold))
                button.setMinimumSize(200, 80)
                button.clicked.connect(handler)
                
                layout.addWidget(button, row, col)
                
                col += 1
                if col > 3:
                    col = 0
                    row += 1
    
    def setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('ملف')
        
        logout_action = QAction('تسجيل الخروج', self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        exit_action = QAction('خروج', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('أدوات')
        
        backup_action = QAction('نسخ احتياطي', self)
        backup_action.triggered.connect(self.open_backup_window)
        tools_menu.addAction(backup_action)
        
        settings_action = QAction('الإعدادات', self)
        settings_action.triggered.connect(self.open_settings_window)
        tools_menu.addAction(settings_action)
    
    def setup_status_bar(self):
        """Setup the status bar"""
        status_bar = self.statusBar()
        status_bar.showMessage(f"متصل كـ: {self.current_user.name} | الصلاحية: {self.current_user.role.name}")
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(get_stylesheet("light"))
    
    def has_permission(self, permission):
        """Check if current user has a specific permission"""
        # Admin has all permissions
        if self.current_user.role.name == "Admin":
            return True
        
        # Parse permissions JSON and check
        import json
        try:
            permissions = json.loads(self.current_user.role.permissions_json)
            return permissions.get(permission, False) or permissions.get("all", False)
        except:
            return False
    
    def load_dashboard_data(self):
        """Load dashboard summary data"""
        try:
            # Get today's sales total
            today_sales = self.report_service.get_today_sales_total()
            self.sales_card.layout().itemAt(1).widget().setText(f"{today_sales:.2f} جنيه")
            
            # Get low stock count
            low_stock_count = self.report_service.get_low_stock_count()
            self.stock_card.layout().itemAt(1).widget().setText(str(low_stock_count))
            
            # Get pending repairs count
            pending_repairs = self.report_service.get_pending_repairs_count()
            self.repairs_card.layout().itemAt(1).widget().setText(str(pending_repairs))
            
            # Get total products count
            total_products = self.report_service.get_total_products_count()
            self.products_card.layout().itemAt(1).widget().setText(str(total_products))
            
        except Exception as e:
            print(f"Error loading dashboard data: {e}")
    
    def perform_search(self):
        """Perform global search"""
        query = self.search_input.text().strip()
        if len(query) >= 2:
            try:
                results = self.search_service.global_search(query)
                # You could show search results in a popup or separate window
                print(f"Search results for '{query}': {len(results)} items found")
            except Exception as e:
                print(f"Search error: {e}")
    
    def open_inventory_window(self):
        """Open inventory management window"""
        if not self.has_permission("inventory"):
            QMessageBox.warning(self, "تحذير", "ليس لديك صلاحية للوصول إلى إدارة المخزون")
            return
        
        window = InventoryWindow(self.current_user)
        window.show()
        self.child_windows.append(window)
    
    def open_sales_window(self):
        """Open sales window"""
        if not self.has_permission("sales"):
            QMessageBox.warning(self, "تحذير", "ليس لديك صلاحية للوصول إلى المبيعات")
            return
        
        window = SalesWindow(self.current_user)
        window.show()
        self.child_windows.append(window)
    
    def open_repair_window(self):
        """Open repair service window"""
        if not self.has_permission("repairs"):
            QMessageBox.warning(self, "تحذير", "ليس لديك صلاحية للوصول إلى خدمة الصيانة")
            return
        
        window = RepairWindow(self.current_user)
        window.show()
        self.child_windows.append(window)
    
    def open_transfer_window(self):
        """Open balance transfer window"""
        if not self.has_permission("transfers"):
            QMessageBox.warning(self, "تحذير", "ليس لديك صلاحية للوصول إلى تحويلات الرصيد")
            return
        
        window = TransferWindow(self.current_user)
        window.show()
        self.child_windows.append(window)
    
    def open_reports_window(self):
        """Open reports window"""
        if not self.has_permission("reports"):
            QMessageBox.warning(self, "تحذير", "ليس لديك صلاحية للوصول إلى التقارير")
            return
        
        window = ReportsWindow(self.current_user)
        window.show()
        self.child_windows.append(window)
    
    def open_user_management_window(self):
        """Open user management window"""
        if not self.has_permission("users"):
            QMessageBox.warning(self, "تحذير", "ليس لديك صلاحية لإدارة المستخدمين")
            return
        
        window = UserManagementWindow(self.current_user)
        window.show()
        self.child_windows.append(window)
    
    def open_settings_window(self):
        """Open settings window"""
        window = SettingsWindow(self.current_user)
        window.show()
        self.child_windows.append(window)
    
    def open_backup_window(self):
        """Open backup window"""
        if not self.has_permission("backup"):
            QMessageBox.warning(self, "تحذير", "ليس لديك صلاحية للنسخ الاحتياطي")
            return
        
        window = BackupWindow(self.current_user)
        window.show()
        self.child_windows.append(window)
    
    def logout(self):
        """Handle user logout"""
        reply = QMessageBox.question(
            self,
            'تأكيد تسجيل الخروج',
            'هل أنت متأكد من تسجيل الخروج؟',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Close all child windows
            for window in self.child_windows:
                if window and not window.isHidden():
                    window.close()
            
            self.close()
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Close all child windows
        for window in self.child_windows:
            if window and not window.isHidden():
                window.close()
        
        self.closed.emit()
        event.accept()
