# -*- coding: utf-8 -*-
"""
User management window for admin users
"""

import logging
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                            QLineEdit, QComboBox, QMessageBox, QHeaderView,
                            QFrame, QGroupBox, QFormLayout, QTabWidget,
                            QCheckBox, QTextEdit, QDateEdit, QSplitter)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import bcrypt

from models.user import User, Role
from models.audit import AuditLog
from config.database import get_db_session
from services.auth_service import AuthService
from ui.dialogs.user_dialog import UserDialog
from ui.dialogs.role_dialog import RoleDialog
from utils.helpers import show_error, show_success

class UserManagementWindow(QMainWindow):
    """User management window for admin users"""
    
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.users_data = []
        self.roles_data = []
        self.auth_service = AuthService()
        
        # Check permissions
        if not self.current_user.has_permission("users", "read"):
            show_error(self, "ليس لديك صلاحية للوصول إلى إدارة المستخدمين")
            self.close()
            return
            
        self.setup_ui()
        self.setup_connections()
        self.load_data()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("إدارة المستخدمين والصلاحيات")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Users management tab
        self.setup_users_tab()
        
        # Roles management tab
        self.setup_roles_tab()
        
        # User activity tab
        self.setup_activity_tab()
        
        # Permissions tab
        self.setup_permissions_tab()
        
    def setup_users_tab(self):
        """Setup users management tab"""
        users_widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Search controls
        search_label = QLabel("البحث:")
        self.user_search_input = QLineEdit()
        self.user_search_input.setPlaceholderText("البحث في الاسم أو البريد الإلكتروني...")
        
        role_label = QLabel("الدور:")
        self.user_role_filter = QComboBox()
        self.user_role_filter.addItem("جميع الأدوار", None)
        
        status_label = QLabel("الحالة:")
        self.user_status_filter = QComboBox()
        self.user_status_filter.addItem("جميع المستخدمين", None)
        self.user_status_filter.addItem("نشط", True)
        self.user_status_filter.addItem("غير نشط", False)
        
        # Action buttons
        self.add_user_btn = QPushButton("إضافة مستخدم جديد")
        self.edit_user_btn = QPushButton("تعديل المستخدم")
        self.delete_user_btn = QPushButton("حذف المستخدم")
        self.reset_password_btn = QPushButton("إعادة تعيين كلمة المرور")
        self.toggle_status_btn = QPushButton("تفعيل/إلغاء تفعيل")
        
        # Enable/disable based on permissions
        if not self.current_user.has_permission("users", "create"):
            self.add_user_btn.setEnabled(False)
        if not self.current_user.has_permission("users", "update"):
            self.edit_user_btn.setEnabled(False)
            self.reset_password_btn.setEnabled(False)
            self.toggle_status_btn.setEnabled(False)
        if not self.current_user.has_permission("users", "delete"):
            self.delete_user_btn.setEnabled(False)
        
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.user_search_input)
        toolbar_layout.addWidget(role_label)
        toolbar_layout.addWidget(self.user_role_filter)
        toolbar_layout.addWidget(status_label)
        toolbar_layout.addWidget(self.user_status_filter)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.add_user_btn)
        toolbar_layout.addWidget(self.edit_user_btn)
        toolbar_layout.addWidget(self.delete_user_btn)
        toolbar_layout.addWidget(self.reset_password_btn)
        toolbar_layout.addWidget(self.toggle_status_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "الاسم", "البريد الإلكتروني", "الدور", "الحالة",
            "تاريخ الإنشاء", "آخر دخول"
        ])
        
        # Configure table
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Email
        
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSortingEnabled(True)
        
        layout.addWidget(self.users_table)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.total_users_label = QLabel("إجمالي المستخدمين: 0")
        self.active_users_label = QLabel("المستخدمين النشطين: 0")
        self.online_users_label = QLabel("متصل الآن: 0")
        
        status_layout.addWidget(self.total_users_label)
        status_layout.addWidget(self.active_users_label)
        status_layout.addWidget(self.online_users_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
        users_widget.setLayout(layout)
        self.tab_widget.addTab(users_widget, "المستخدمين")
        
    def setup_roles_tab(self):
        """Setup roles management tab"""
        roles_widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_role_btn = QPushButton("إضافة دور جديد")
        self.edit_role_btn = QPushButton("تعديل الدور")
        self.delete_role_btn = QPushButton("حذف الدور")
        self.copy_role_btn = QPushButton("نسخ الدور")
        
        # Enable/disable based on permissions
        if not self.current_user.has_permission("users", "create"):
            self.add_role_btn.setEnabled(False)
            self.copy_role_btn.setEnabled(False)
        if not self.current_user.has_permission("users", "update"):
            self.edit_role_btn.setEnabled(False)
        if not self.current_user.has_permission("users", "delete"):
            self.delete_role_btn.setEnabled(False)
        
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.add_role_btn)
        toolbar_layout.addWidget(self.edit_role_btn)
        toolbar_layout.addWidget(self.delete_role_btn)
        toolbar_layout.addWidget(self.copy_role_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Roles table
        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(4)
        self.roles_table.setHorizontalHeaderLabels([
            "ID", "اسم الدور", "عدد المستخدمين", "الصلاحيات"
        ])
        
        header = self.roles_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.roles_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.roles_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.roles_table)
        
        roles_widget.setLayout(layout)
        self.tab_widget.addTab(roles_widget, "الأدوار والصلاحيات")
        
    def setup_activity_tab(self):
        """Setup user activity monitoring tab"""
        activity_widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        user_label = QLabel("المستخدم:")
        self.activity_user_filter = QComboBox()
        self.activity_user_filter.addItem("جميع المستخدمين", None)
        
        action_label = QLabel("النشاط:")
        self.activity_action_filter = QComboBox()
        self.activity_action_filter.addItem("جميع الأنشطة", None)
        self.activity_action_filter.addItem("تسجيل الدخول", "login_success")
        self.activity_action_filter.addItem("تسجيل الخروج", "logout")
        self.activity_action_filter.addItem("فشل الدخول", "login_failed")
        self.activity_action_filter.addItem("إنشاء", "create")
        self.activity_action_filter.addItem("تعديل", "update")
        self.activity_action_filter.addItem("حذف", "delete")
        
        date_label = QLabel("التاريخ:")
        self.activity_date_from = QDateEdit()
        self.activity_date_from.setDate(QDate.currentDate().addDays(-7))
        self.activity_date_from.setCalendarPopup(True)
        
        self.activity_date_to = QDateEdit()
        self.activity_date_to.setDate(QDate.currentDate())
        self.activity_date_to.setCalendarPopup(True)
        
        self.refresh_activity_btn = QPushButton("تحديث")
        self.export_activity_btn = QPushButton("تصدير")
        
        filter_layout.addWidget(user_label)
        filter_layout.addWidget(self.activity_user_filter)
        filter_layout.addWidget(action_label)
        filter_layout.addWidget(self.activity_action_filter)
        filter_layout.addWidget(date_label)
        filter_layout.addWidget(self.activity_date_from)
        filter_layout.addWidget(QLabel("إلى"))
        filter_layout.addWidget(self.activity_date_to)
        filter_layout.addWidget(self.refresh_activity_btn)
        filter_layout.addWidget(self.export_activity_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Activity table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(6)
        self.activity_table.setHorizontalHeaderLabels([
            "التاريخ والوقت", "المستخدم", "النشاط", "الوحدة", "التفاصيل", "عنوان IP"
        ])
        
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setSortingEnabled(True)
        
        layout.addWidget(self.activity_table)
        
        activity_widget.setLayout(layout)
        self.tab_widget.addTab(activity_widget, "نشاط المستخدمين")
        
    def setup_permissions_tab(self):
        """Setup permissions overview tab"""
        permissions_widget = QWidget()
        layout = QVBoxLayout()
        
        # Permissions matrix
        permissions_group = QGroupBox("مصفوفة الصلاحيات")
        permissions_layout = QVBoxLayout()
        
        # This would be a detailed permissions matrix
        self.permissions_table = QTableWidget()
        self.permissions_table.setColumnCount(6)
        self.permissions_table.setHorizontalHeaderLabels([
            "الوحدة", "عرض", "إنشاء", "تعديل", "حذف", "الأدوار المتاحة"
        ])
        
        permissions_layout.addWidget(self.permissions_table)
        permissions_group.setLayout(permissions_layout)
        layout.addWidget(permissions_group)
        
        permissions_widget.setLayout(layout)
        self.tab_widget.addTab(permissions_widget, "نظرة عامة على الصلاحيات")
        
    def setup_connections(self):
        """Setup signal connections"""
        # Users tab
        self.user_search_input.textChanged.connect(self.filter_users)
        self.user_role_filter.currentTextChanged.connect(self.filter_users)
        self.user_status_filter.currentTextChanged.connect(self.filter_users)
        
        self.add_user_btn.clicked.connect(self.add_user)
        self.edit_user_btn.clicked.connect(self.edit_user)
        self.delete_user_btn.clicked.connect(self.delete_user)
        self.reset_password_btn.clicked.connect(self.reset_password)
        self.toggle_status_btn.clicked.connect(self.toggle_user_status)
        
        self.users_table.doubleClicked.connect(self.edit_user)
        self.users_table.selectionModel().selectionChanged.connect(self.on_user_selection_changed)
        
        # Roles tab
        self.add_role_btn.clicked.connect(self.add_role)
        self.edit_role_btn.clicked.connect(self.edit_role)
        self.delete_role_btn.clicked.connect(self.delete_role)
        self.copy_role_btn.clicked.connect(self.copy_role)
        
        self.roles_table.doubleClicked.connect(self.edit_role)
        self.roles_table.selectionModel().selectionChanged.connect(self.on_role_selection_changed)
        
        # Activity tab
        self.refresh_activity_btn.clicked.connect(self.refresh_activity)
        self.export_activity_btn.clicked.connect(self.export_activity)
        
    def load_data(self):
        """Load all data"""
        self.load_users()
        self.load_roles()
        self.load_activity()
        self.load_permissions_matrix()
        
    def load_users(self):
        """Load users data"""
        session = get_db_session()
        try:
            users = session.query(User).join(Role).all()
            self.users_data = users
            
            # Update role filter
            self.user_role_filter.clear()
            self.user_role_filter.addItem("جميع الأدوار", None)
            self.activity_user_filter.clear()
            self.activity_user_filter.addItem("جميع المستخدمين", None)
            
            roles_added = set()
            for user in users:
                if user.role and user.role.name not in roles_added:
                    self.user_role_filter.addItem(user.role.name, user.role.id)
                    roles_added.add(user.role.name)
                
                self.activity_user_filter.addItem(user.name, user.id)
            
            self.update_users_table()
            self.update_user_statistics()
            
        finally:
            session.close()
            
    def load_roles(self):
        """Load roles data"""
        session = get_db_session()
        try:
            roles = session.query(Role).all()
            self.roles_data = roles
            
            self.update_roles_table()
            
        finally:
            session.close()
            
    def load_activity(self):
        """Load user activity data"""
        self.refresh_activity()
        
    def load_permissions_matrix(self):
        """Load permissions matrix"""
        # Define modules and their permissions
        modules = {
            "المستخدمين": ["read", "create", "update", "delete"],
            "المنتجات": ["read", "create", "update", "delete"],
            "المبيعات": ["read", "create", "update", "delete"],
            "الصيانة": ["read", "create", "update", "delete"],
            "التحويلات": ["read", "create", "update", "delete"],
            "التقارير": ["read"],
            "الإعدادات": ["read", "update"],
            "النسخ الاحتياطي": ["read", "create"]
        }
        
        self.permissions_table.setRowCount(len(modules))
        
        for row, (module_name, permissions) in enumerate(modules.items()):
            self.permissions_table.setItem(row, 0, QTableWidgetItem(module_name))
            
            # Check permissions for each action
            for col, permission in enumerate(["read", "create", "update", "delete"], 1):
                if permission in permissions:
                    # Find which roles have this permission
                    roles_with_permission = []
                    for role in self.roles_data:
                        if role.has_permission(module_name.lower(), permission):
                            roles_with_permission.append(role.name)
                    
                    self.permissions_table.setItem(row, col, QTableWidgetItem("✓" if roles_with_permission else "✗"))
                else:
                    self.permissions_table.setItem(row, col, QTableWidgetItem("-"))
            
            # List roles with any permission for this module
            roles_with_access = []
            for role in self.roles_data:
                for permission in permissions:
                    if role.has_permission(module_name.lower(), permission):
                        if role.name not in roles_with_access:
                            roles_with_access.append(role.name)
                        break
            
            self.permissions_table.setItem(row, 5, QTableWidgetItem(", ".join(roles_with_access)))
            
    def update_users_table(self):
        """Update users table display"""
        self.users_table.setRowCount(len(self.users_data))
        
        for row, user in enumerate(self.users_data):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.name))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.email))
            self.users_table.setItem(row, 3, QTableWidgetItem(user.role.name if user.role else ""))
            
            # Status with color coding
            status_item = QTableWidgetItem("نشط" if user.active else "غير نشط")
            if user.active:
                status_item.setBackground(QColor("#e8f5e8"))  # Light green
            else:
                status_item.setBackground(QColor("#ffebee"))  # Light red
            self.users_table.setItem(row, 4, status_item)
            
            self.users_table.setItem(row, 5, QTableWidgetItem(user.created_at.strftime("%Y-%m-%d")))
            
            last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "لم يسجل دخول"
            self.users_table.setItem(row, 6, QTableWidgetItem(last_login))
            
            # Store user ID in first column
            self.users_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, user.id)
            
    def update_roles_table(self):
        """Update roles table display"""
        self.roles_table.setRowCount(len(self.roles_data))
        
        for row, role in enumerate(self.roles_data):
            user_count = len(role.users)
            
            self.roles_table.setItem(row, 0, QTableWidgetItem(str(role.id)))
            self.roles_table.setItem(row, 1, QTableWidgetItem(role.name))
            self.roles_table.setItem(row, 2, QTableWidgetItem(str(user_count)))
            
            # Permissions summary
            permissions = role.permissions
            permission_summary = []
            for module, actions in permissions.items():
                if actions:
                    permission_summary.append(f"{module}: {', '.join(actions)}")
            
            permissions_text = "; ".join(permission_summary) if permission_summary else "لا توجد صلاحيات"
            self.roles_table.setItem(row, 3, QTableWidgetItem(permissions_text))
            
            # Store role ID in first column
            self.roles_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, role.id)
            
    def update_user_statistics(self):
        """Update user statistics"""
        total_users = len(self.users_data)
        active_users = len([u for u in self.users_data if u.active])
        
        # For online users, we'd need to track active sessions
        online_users = 0  # Placeholder
        
        self.total_users_label.setText(f"إجمالي المستخدمين: {total_users}")
        self.active_users_label.setText(f"المستخدمين النشطين: {active_users}")
        self.online_users_label.setText(f"متصل الآن: {online_users}")
        
    def filter_users(self):
        """Filter users based on search criteria"""
        search_text = self.user_search_input.text().lower()
        role_id = self.user_role_filter.currentData()
        status = self.user_status_filter.currentData()
        
        for row in range(self.users_table.rowCount()):
            show_row = True
            
            # Search filter
            if search_text:
                name = self.users_table.item(row, 1).text().lower()
                email = self.users_table.item(row, 2).text().lower()
                if search_text not in name and search_text not in email:
                    show_row = False
            
            # Role filter
            if role_id and show_row:
                user_id = self.users_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                user = next((u for u in self.users_data if u.id == user_id), None)
                if user and user.role_id != role_id:
                    show_row = False
            
            # Status filter
            if status is not None and show_row:
                user_id = self.users_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                user = next((u for u in self.users_data if u.id == user_id), None)
                if user and user.active != status:
                    show_row = False
            
            self.users_table.setRowHidden(row, not show_row)
            
    def refresh_activity(self):
        """Refresh user activity data"""
        session = get_db_session()
        try:
            date_from = self.activity_date_from.date().toPython()
            date_to = self.activity_date_to.date().toPython()
            user_id = self.activity_user_filter.currentData()
            action = self.activity_action_filter.currentData()
            
            query = session.query(AuditLog).join(User, AuditLog.user_id == User.id, isouter=True)
            
            # Apply filters
            query = query.filter(AuditLog.timestamp >= date_from)
            query = query.filter(AuditLog.timestamp <= date_to)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if action:
                query = query.filter(AuditLog.action == action)
            
            activities = query.order_by(AuditLog.timestamp.desc()).limit(1000).all()
            
            self.activity_table.setRowCount(len(activities))
            
            for row, activity in enumerate(activities):
                self.activity_table.setItem(row, 0, QTableWidgetItem(activity.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
                
                user_name = activity.user.name if activity.user else "نظام"
                self.activity_table.setItem(row, 1, QTableWidgetItem(user_name))
                
                action_display = self.get_action_display(activity.action)
                self.activity_table.setItem(row, 2, QTableWidgetItem(action_display))
                
                self.activity_table.setItem(row, 3, QTableWidgetItem(activity.module or ""))
                self.activity_table.setItem(row, 4, QTableWidgetItem(activity.details or ""))
                self.activity_table.setItem(row, 5, QTableWidgetItem(activity.ip_address or ""))
                
        finally:
            session.close()
            
    def get_action_display(self, action: str) -> str:
        """Get Arabic display text for action"""
        action_map = {
            "login_success": "تسجيل دخول ناجح",
            "login_failed": "فشل تسجيل الدخول",
            "logout": "تسجيل خروج",
            "create": "إنشاء",
            "update": "تعديل",
            "delete": "حذف",
            "view": "عرض"
        }
        return action_map.get(action, action)
        
    def on_user_selection_changed(self):
        """Handle user selection change"""
        has_selection = bool(self.users_table.selectedItems())
        selected_user_id = None
        
        if has_selection:
            row = self.users_table.currentRow()
            selected_user_id = self.users_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        # Don't allow editing/deleting own account
        is_own_account = selected_user_id == self.current_user.id
        
        self.edit_user_btn.setEnabled(has_selection and self.current_user.has_permission("users", "update"))
        self.delete_user_btn.setEnabled(has_selection and not is_own_account and self.current_user.has_permission("users", "delete"))
        self.reset_password_btn.setEnabled(has_selection and self.current_user.has_permission("users", "update"))
        self.toggle_status_btn.setEnabled(has_selection and not is_own_account and self.current_user.has_permission("users", "update"))
        
    def on_role_selection_changed(self):
        """Handle role selection change"""
        has_selection = bool(self.roles_table.selectedItems())
        self.edit_role_btn.setEnabled(has_selection and self.current_user.has_permission("users", "update"))
        self.delete_role_btn.setEnabled(has_selection and self.current_user.has_permission("users", "delete"))
        self.copy_role_btn.setEnabled(has_selection and self.current_user.has_permission("users", "create"))
        
    def add_user(self):
        """Add new user"""
        dialog = UserDialog(self, self.current_user)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.load_users()
            show_success(self, "تم إضافة المستخدم بنجاح")
            
    def edit_user(self):
        """Edit selected user"""
        selected_items = self.users_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار مستخدم للتعديل")
            return
        
        row = selected_items[0].row()
        user_id = self.users_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = UserDialog(self, self.current_user, user_id)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.load_users()
            show_success(self, "تم تعديل المستخدم بنجاح")
            
    def delete_user(self):
        """Delete selected user"""
        selected_items = self.users_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار مستخدم للحذف")
            return
        
        row = selected_items[0].row()
        user_id = self.users_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        user_name = self.users_table.item(row, 1).text()
        
        if user_id == self.current_user.id:
            show_error(self, "لا يمكن حذف حسابك الخاص")
            return
        
        reply = QMessageBox.question(self, "تأكيد الحذف",
                                   f"هل أنت متأكد من حذف المستخدم '{user_name}'؟\n"
                                   "سيتم حذف جميع البيانات المرتبطة به.")
        
        if reply == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            try:
                user = session.query(User).get(user_id)
                if user:
                    # Log the deletion
                    AuditLog.log_action(
                        session, self.current_user.id, "delete", "users",
                        record_id=user_id, details=f"Deleted user: {user.name}"
                    )
                    
                    session.delete(user)
                    session.commit()
                    self.load_users()
                    show_success(self, "تم حذف المستخدم بنجاح")
            except Exception as e:
                session.rollback()
                show_error(self, f"فشل في حذف المستخدم:\n{str(e)}")
            finally:
                session.close()
                
    def reset_password(self):
        """Reset password for selected user"""
        selected_items = self.users_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار مستخدم لإعادة تعيين كلمة المرور")
            return
        
        row = selected_items[0].row()
        user_id = self.users_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        user_name = self.users_table.item(row, 1).text()
        
        reply = QMessageBox.question(self, "إعادة تعيين كلمة المرور",
                                   f"هل تريد إعادة تعيين كلمة المرور للمستخدم '{user_name}'؟\n"
                                   "سيتم تعيين كلمة مرور افتراضية.")
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                new_password = "123456"  # Default password
                success = self.auth_service.reset_user_password(user_id, new_password, self.current_user.id)
                
                if success:
                    QMessageBox.information(self, "تم إعادة التعيين",
                                          f"تم إعادة تعيين كلمة المرور بنجاح\n"
                                          f"كلمة المرور الجديدة: {new_password}\n"
                                          "يرجى إبلاغ المستخدم بتغييرها عند أول دخول")
                else:
                    show_error(self, "فشل في إعادة تعيين كلمة المرور")
                    
            except Exception as e:
                show_error(self, f"خطأ في إعادة تعيين كلمة المرور:\n{str(e)}")
                
    def toggle_user_status(self):
        """Toggle user active status"""
        selected_items = self.users_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار مستخدم لتغيير حالته")
            return
        
        row = selected_items[0].row()
        user_id = self.users_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        user_name = self.users_table.item(row, 1).text()
        
        if user_id == self.current_user.id:
            show_error(self, "لا يمكن تغيير حالة حسابك الخاص")
            return
        
        session = get_db_session()
        try:
            user = session.query(User).get(user_id)
            if user:
                new_status = not user.active
                status_text = "تفعيل" if new_status else "إلغاء تفعيل"
                
                reply = QMessageBox.question(self, "تغيير الحالة",
                                           f"هل تريد {status_text} المستخدم '{user_name}'؟")
                
                if reply == QMessageBox.StandardButton.Yes:
                    user.active = new_status
                    
                    # Log the change
                    AuditLog.log_action(
                        session, self.current_user.id, "update", "users",
                        record_id=user_id, details=f"Changed user status to {'active' if new_status else 'inactive'}"
                    )
                    
                    session.commit()
                    self.load_users()
                    show_success(self, f"تم {status_text} المستخدم بنجاح")
                    
        except Exception as e:
            session.rollback()
            show_error(self, f"فشل في تغيير حالة المستخدم:\n{str(e)}")
        finally:
            session.close()
            
    def add_role(self):
        """Add new role"""
        dialog = RoleDialog(self, self.current_user)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.load_roles()
            self.load_permissions_matrix()
            show_success(self, "تم إضافة الدور بنجاح")
            
    def edit_role(self):
        """Edit selected role"""
        selected_items = self.roles_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار دور للتعديل")
            return
        
        row = selected_items[0].row()
        role_id = self.roles_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = RoleDialog(self, self.current_user, role_id)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.load_roles()
            self.load_permissions_matrix()
            show_success(self, "تم تعديل الدور بنجاح")
            
    def delete_role(self):
        """Delete selected role"""
        selected_items = self.roles_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار دور للحذف")
            return
        
        row = selected_items[0].row()
        role_id = self.roles_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        role_name = self.roles_table.item(row, 1).text()
        user_count = int(self.roles_table.item(row, 2).text())
        
        if user_count > 0:
            show_error(self, f"لا يمكن حذف الدور '{role_name}' لأنه مرتبط بـ {user_count} مستخدم")
            return
        
        reply = QMessageBox.question(self, "تأكيد الحذف",
                                   f"هل أنت متأكد من حذف الدور '{role_name}'؟")
        
        if reply == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            try:
                role = session.query(Role).get(role_id)
                if role:
                    # Log the deletion
                    AuditLog.log_action(
                        session, self.current_user.id, "delete", "roles",
                        record_id=role_id, details=f"Deleted role: {role.name}"
                    )
                    
                    session.delete(role)
                    session.commit()
                    self.load_roles()
                    self.load_permissions_matrix()
                    show_success(self, "تم حذف الدور بنجاح")
            except Exception as e:
                session.rollback()
                show_error(self, f"فشل في حذف الدور:\n{str(e)}")
            finally:
                session.close()
                
    def copy_role(self):
        """Copy selected role"""
        selected_items = self.roles_table.selectedItems()
        if not selected_items:
            show_error(self, "يرجى اختيار دور للنسخ")
            return
        
        row = selected_items[0].row()
        role_id = self.roles_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = RoleDialog(self, self.current_user, role_id, copy_mode=True)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.load_roles()
            self.load_permissions_matrix()
            show_success(self, "تم نسخ الدور بنجاح")
            
    def export_activity(self):
        """Export activity log"""
        show_error(self, "ميزة تصدير سجل النشاط قيد التطوير")
