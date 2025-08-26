from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QLineEdit, QComboBox, QCheckBox, QTextEdit,
                            QFormLayout, QDialog, QMessageBox, QGroupBox,
                            QHeaderView, QAbstractItemView, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import json
import bcrypt

from services.user_service import UserService
from ui.styles import get_stylesheet

class UserManagementWindow(QMainWindow):
    """User management and permissions window"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.user_service = UserService()
        self.current_selected_user = None
        
        self.setup_ui()
        self.apply_styles()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("إدارة المستخدمين والصلاحيات")
        self.setMinimumSize(1000, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("إدارة المستخدمين والصلاحيات")
        title_label.setFont(QFont("Noto Sans Arabic", 18, QFont.Weight.Bold))
        title_label.setObjectName("title-label")
        
        # Add user button
        self.add_user_btn = QPushButton("إضافة مستخدم جديد")
        self.add_user_btn.clicked.connect(self.add_user)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_user_btn)
        
        # Search section
        search_group = QGroupBox("البحث في المستخدمين")
        search_layout = QHBoxLayout()
        
        search_label = QLabel("بحث:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بالاسم أو البريد الإلكتروني...")
        self.search_input.textChanged.connect(self.filter_users)
        
        role_label = QLabel("الدور:")
        self.role_filter = QComboBox()
        self.role_filter.currentTextChanged.connect(self.filter_users)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(role_label)
        search_layout.addWidget(self.role_filter)
        search_layout.addStretch()
        
        search_group.setLayout(search_layout)
        
        # Users table
        self.users_table = QTableWidget()
        self.setup_users_table()
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.view_btn = QPushButton("عرض التفاصيل")
        self.view_btn.clicked.connect(self.view_user)
        self.view_btn.setEnabled(False)
        
        self.edit_btn = QPushButton("تعديل")
        self.edit_btn.clicked.connect(self.edit_user)
        self.edit_btn.setEnabled(False)
        
        self.permissions_btn = QPushButton("إدارة الصلاحيات")
        self.permissions_btn.clicked.connect(self.manage_permissions)
        self.permissions_btn.setEnabled(False)
        
        self.activate_btn = QPushButton("تفعيل/إلغاء تفعيل")
        self.activate_btn.clicked.connect(self.toggle_activation)
        self.activate_btn.setEnabled(False)
        
        self.reset_password_btn = QPushButton("إعادة تعيين كلمة المرور")
        self.reset_password_btn.clicked.connect(self.reset_password)
        self.reset_password_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.view_btn)
        buttons_layout.addWidget(self.edit_btn)
        buttons_layout.addWidget(self.permissions_btn)
        buttons_layout.addWidget(self.activate_btn)
        buttons_layout.addWidget(self.reset_password_btn)
        buttons_layout.addStretch()
        
        # Add layouts to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(search_group)
        main_layout.addWidget(self.users_table)
        main_layout.addLayout(buttons_layout)
        
        central_widget.setLayout(main_layout)
        
        # Connect table selection
        self.users_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def setup_users_table(self):
        """Setup users table"""
        headers = ["الاسم", "البريد الإلكتروني", "الدور", "آخر دخول", "الحالة", "تاريخ الإنشاء"]
        
        self.users_table.setColumnCount(len(headers))
        self.users_table.setHorizontalHeaderLabels(headers)
        
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSortingEnabled(True)
        
        # Resize columns
        header = self.users_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(get_stylesheet("light"))
    
    def load_data(self):
        """Load users and roles data"""
        try:
            # Load roles for filter
            roles = self.user_service.get_roles()
            self.role_filter.clear()
            self.role_filter.addItem("الكل")
            for role in roles:
                self.role_filter.addItem(role.name)
            
            # Load users
            self.load_users()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {str(e)}")
    
    def load_users(self):
        """Load users into table"""
        try:
            users = self.user_service.get_users()
            
            self.users_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                # Format last login
                last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "لم يسجل دخول"
                
                # Format creation date
                created_at = user.created_at.strftime("%Y-%m-%d") if user.created_at else ""
                
                # Status
                status = "نشط" if user.active else "غير نشط"
                
                items = [
                    user.name,
                    user.email,
                    user.role.name if user.role else "غير محدد",
                    last_login,
                    status,
                    created_at
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    item.setData(Qt.ItemDataRole.UserRole, user.id)
                    
                    # Color coding for status
                    if col == 4:  # Status column
                        if not user.active:
                            item.setBackground(Qt.GlobalColor.red)
                        else:
                            item.setBackground(Qt.GlobalColor.green)
                    
                    self.users_table.setItem(row, col, item)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل المستخدمين: {str(e)}")
    
    def filter_users(self):
        """Filter users based on search criteria"""
        search_text = self.search_input.text().lower()
        role = self.role_filter.currentText()
        
        for row in range(self.users_table.rowCount()):
            show_row = True
            
            # Search filter
            if search_text:
                name = self.users_table.item(row, 0).text().lower()
                email = self.users_table.item(row, 1).text().lower()
                if search_text not in name and search_text not in email:
                    show_row = False
            
            # Role filter
            if role != "الكل" and show_row:
                user_role = self.users_table.item(row, 2).text()
                if role != user_role:
                    show_row = False
            
            self.users_table.setRowHidden(row, not show_row)
    
    def on_selection_changed(self):
        """Handle table selection change"""
        selected_rows = self.users_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.view_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)
        self.permissions_btn.setEnabled(has_selection)
        self.activate_btn.setEnabled(has_selection)
        self.reset_password_btn.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            user_id = self.users_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.current_selected_user = self.user_service.get_user_by_id(user_id)
    
    def add_user(self):
        """Add new user"""
        dialog = UserDialog(self, self.user_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()
    
    def view_user(self):
        """View user details"""
        if self.current_selected_user:
            dialog = UserViewDialog(self, self.current_selected_user)
            dialog.exec()
    
    def edit_user(self):
        """Edit selected user"""
        if self.current_selected_user:
            dialog = UserDialog(self, self.user_service, self.current_selected_user)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_users()
    
    def manage_permissions(self):
        """Manage user permissions"""
        if self.current_selected_user:
            dialog = PermissionsDialog(self, self.user_service, self.current_selected_user)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_users()
    
    def toggle_activation(self):
        """Toggle user activation status"""
        if not self.current_selected_user:
            return
        
        action = "إلغاء تفعيل" if self.current_selected_user.active else "تفعيل"
        
        reply = QMessageBox.question(
            self,
            'تأكيد',
            f'هل أنت متأكد من {action} المستخدم "{self.current_selected_user.name}"؟',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.user_service.toggle_user_activation(self.current_selected_user.id)
                QMessageBox.information(self, "نجح", f"تم {action} المستخدم بنجاح")
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في {action} المستخدم: {str(e)}")
    
    def reset_password(self):
        """Reset user password"""
        if not self.current_selected_user:
            return
        
        dialog = PasswordResetDialog(self, self.current_selected_user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "نجح", "تم إعادة تعيين كلمة المرور بنجاح")

class UserDialog(QDialog):
    """Dialog for adding/editing users"""
    
    def __init__(self, parent, user_service, user=None):
        super().__init__(parent)
        self.user_service = user_service
        self.user = user
        self.is_edit_mode = user is not None
        
        self.setup_ui()
        if self.is_edit_mode:
            self.load_user_data()
    
    def setup_ui(self):
        """Setup dialog UI"""
        title = "تعديل مستخدم" if self.is_edit_mode else "إضافة مستخدم جديد"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # User fields
        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        
        self.role_combo = QComboBox()
        self.load_roles()
        
        if not self.is_edit_mode:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            
            self.confirm_password_input = QLineEdit()
            self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.active_checkbox = QCheckBox("مستخدم نشط")
        self.active_checkbox.setChecked(True)
        
        # Add fields to form
        form_layout.addRow("الاسم:", self.name_input)
        form_layout.addRow("البريد الإلكتروني:", self.email_input)
        form_layout.addRow("الدور:", self.role_combo)
        
        if not self.is_edit_mode:
            form_layout.addRow("كلمة المرور:", self.password_input)
            form_layout.addRow("تأكيد كلمة المرور:", self.confirm_password_input)
        
        form_layout.addRow("", self.active_checkbox)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("حفظ")
        self.save_btn.clicked.connect(self.save_user)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_roles(self):
        """Load roles into combo box"""
        try:
            roles = self.user_service.get_roles()
            self.role_combo.clear()
            
            for role in roles:
                self.role_combo.addItem(role.name, role.id)
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل الأدوار: {str(e)}")
    
    def load_user_data(self):
        """Load existing user data for editing"""
        if not self.user:
            return
        
        self.name_input.setText(self.user.name)
        self.email_input.setText(self.user.email)
        self.active_checkbox.setChecked(self.user.active)
        
        # Set role
        if self.user.role_id:
            for i in range(self.role_combo.count()):
                if self.role_combo.itemData(i) == self.user.role_id:
                    self.role_combo.setCurrentIndex(i)
                    break
    
    def save_user(self):
        """Save user data"""
        try:
            # Validate required fields
            if not self.name_input.text().strip():
                QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم المستخدم")
                return
            
            if not self.email_input.text().strip():
                QMessageBox.warning(self, "تحذير", "يرجى إدخال البريد الإلكتروني")
                return
            
            if not self.role_combo.currentData():
                QMessageBox.warning(self, "تحذير", "يرجى اختيار دور المستخدم")
                return
            
            # Password validation for new users
            if not self.is_edit_mode:
                if not self.password_input.text():
                    QMessageBox.warning(self, "تحذير", "يرجى إدخال كلمة المرور")
                    return
                
                if self.password_input.text() != self.confirm_password_input.text():
                    QMessageBox.warning(self, "تحذير", "كلمة المرور وتأكيدها غير متطابقين")
                    return
                
                if len(self.password_input.text()) < 6:
                    QMessageBox.warning(self, "تحذير", "كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                    return
            
            # Prepare user data
            user_data = {
                'name': self.name_input.text().strip(),
                'email': self.email_input.text().strip(),
                'role_id': self.role_combo.currentData(),
                'active': self.active_checkbox.isChecked()
            }
            
            if not self.is_edit_mode:
                user_data['password'] = self.password_input.text()
            
            # Save user
            if self.is_edit_mode:
                self.user_service.update_user(self.user.id, user_data)
                QMessageBox.information(self, "نجح", "تم تحديث المستخدم بنجاح")
            else:
                self.user_service.create_user(user_data)
                QMessageBox.information(self, "نجح", "تم إضافة المستخدم بنجاح")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حفظ المستخدم: {str(e)}")

class UserViewDialog(QDialog):
    """Dialog for viewing user details"""
    
    def __init__(self, parent, user):
        super().__init__(parent)
        self.user = user
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"تفاصيل المستخدم - {self.user.name}")
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(f"بيانات المستخدم: {self.user.name}")
        title_label.setFont(QFont("Noto Sans Arabic", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Details
        details_text = f"""
        الاسم: {self.user.name}
        البريد الإلكتروني: {self.user.email}
        الدور: {self.user.role.name if self.user.role else 'غير محدد'}
        
        الحالة: {'نشط' if self.user.active else 'غير نشط'}
        تاريخ الإنشاء: {self.user.created_at.strftime('%Y-%m-%d %H:%M') if self.user.created_at else 'غير محدد'}
        آخر دخول: {self.user.last_login.strftime('%Y-%m-%d %H:%M') if self.user.last_login else 'لم يسجل دخول'}
        
        الصلاحيات:
        {self.format_permissions()}
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
    
    def format_permissions(self):
        """Format user permissions for display"""
        if not self.user.role or not self.user.role.permissions_json:
            return "لا توجد صلاحيات محددة"
        
        try:
            permissions = json.loads(self.user.role.permissions_json)
            if permissions.get("all", False):
                return "جميع الصلاحيات"
            
            perm_list = []
            perm_names = {
                "sales": "المبيعات",
                "inventory": "المخزون", 
                "repairs": "الصيانة",
                "transfers": "التحويلات",
                "reports": "التقارير",
                "users": "إدارة المستخدمين",
                "settings": "الإعدادات",
                "backup": "النسخ الاحتياطي"
            }
            
            for perm, allowed in permissions.items():
                if allowed and perm in perm_names:
                    perm_list.append(perm_names[perm])
            
            return ", ".join(perm_list) if perm_list else "لا توجد صلاحيات محددة"
            
        except:
            return "خطأ في قراءة الصلاحيات"

class PermissionsDialog(QDialog):
    """Dialog for managing user permissions"""
    
    def __init__(self, parent, user_service, user):
        super().__init__(parent)
        self.user_service = user_service
        self.user = user
        self.setup_ui()
        self.load_permissions()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"إدارة صلاحيات - {self.user.name}")
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(400, 500)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(f"صلاحيات المستخدم: {self.user.name}")
        title_label.setFont(QFont("Noto Sans Arabic", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Permissions checkboxes
        permissions_group = QGroupBox("الصلاحيات")
        permissions_layout = QVBoxLayout()
        
        self.permissions_checkboxes = {}
        permissions_list = [
            ("all", "جميع الصلاحيات"),
            ("sales", "المبيعات والفواتير"),
            ("inventory", "إدارة المخزون"),
            ("repairs", "خدمة الصيانة"),
            ("transfers", "تحويلات الرصيد"),
            ("reports", "التقارير والتحليلات"),
            ("users", "إدارة المستخدمين"),
            ("settings", "الإعدادات"),
            ("backup", "النسخ الاحتياطي")
        ]
        
        for perm_key, perm_name in permissions_list:
            checkbox = QCheckBox(perm_name)
            self.permissions_checkboxes[perm_key] = checkbox
            permissions_layout.addWidget(checkbox)
            
            # Special handling for "all" permissions
            if perm_key == "all":
                checkbox.toggled.connect(self.toggle_all_permissions)
        
        permissions_group.setLayout(permissions_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("حفظ الصلاحيات")
        save_btn.clicked.connect(self.save_permissions)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(title_label)
        layout.addWidget(permissions_group)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_permissions(self):
        """Load current user permissions"""
        if not self.user.role or not self.user.role.permissions_json:
            return
        
        try:
            permissions = json.loads(self.user.role.permissions_json)
            
            for perm_key, checkbox in self.permissions_checkboxes.items():
                checkbox.setChecked(permissions.get(perm_key, False))
                
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"خطأ في تحميل الصلاحيات: {str(e)}")
    
    def toggle_all_permissions(self, checked):
        """Toggle all permissions when 'all' is checked/unchecked"""
        for perm_key, checkbox in self.permissions_checkboxes.items():
            if perm_key != "all":
                checkbox.setChecked(checked)
                checkbox.setEnabled(not checked)
    
    def save_permissions(self):
        """Save user permissions"""
        try:
            permissions = {}
            for perm_key, checkbox in self.permissions_checkboxes.items():
                permissions[perm_key] = checkbox.isChecked()
            
            permissions_json = json.dumps(permissions)
            
            # Update role permissions
            self.user_service.update_role_permissions(self.user.role_id, permissions_json)
            
            QMessageBox.information(self, "نجح", "تم حفظ الصلاحيات بنجاح")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حفظ الصلاحيات: {str(e)}")

class PasswordResetDialog(QDialog):
    """Dialog for resetting user password"""
    
    def __init__(self, parent, user):
        super().__init__(parent)
        self.user = user
        self.user_service = UserService()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"إعادة تعيين كلمة المرور - {self.user.name}")
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(400, 250)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(f"إعادة تعيين كلمة المرور للمستخدم: {self.user.name}")
        title_label.setFont(QFont("Noto Sans Arabic", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Form
        form_layout = QFormLayout()
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        form_layout.addRow("كلمة المرور الجديدة:", self.new_password_input)
        form_layout.addRow("تأكيد كلمة المرور:", self.confirm_password_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("إعادة تعيين")
        reset_btn.clicked.connect(self.reset_password)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(reset_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(title_label)
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def reset_password(self):
        """Reset user password"""
        try:
            new_password = self.new_password_input.text()
            confirm_password = self.confirm_password_input.text()
            
            if not new_password:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال كلمة المرور الجديدة")
                return
            
            if new_password != confirm_password:
                QMessageBox.warning(self, "تحذير", "كلمة المرور وتأكيدها غير متطابقين")
                return
            
            if len(new_password) < 6:
                QMessageBox.warning(self, "تحذير", "كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                return
            
            # Reset password
            self.user_service.reset_user_password(self.user.id, new_password)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في إعادة تعيين كلمة المرور: {str(e)}")

# Create UserService class
class UserService:
    """Service for user management operations"""
    
    def __init__(self):
        from utils.logger import get_logger
        self.logger = get_logger(__name__)
    
    def get_users(self):
        """Get all users"""
        from config.database import SessionLocal
        from models.user import User
        
        db = SessionLocal()
        try:
            return db.query(User).all()
        except Exception as e:
            self.logger.error(f"Error fetching users: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        from config.database import SessionLocal
        from models.user import User
        
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            self.logger.error(f"Error fetching user {user_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_roles(self):
        """Get all roles"""
        from config.database import SessionLocal
        from models.user import Role
        
        db = SessionLocal()
        try:
            return db.query(Role).all()
        except Exception as e:
            self.logger.error(f"Error fetching roles: {str(e)}")
            raise e
        finally:
            db.close()
    
    def create_user(self, user_data):
        """Create new user"""
        from config.database import SessionLocal
        from models.user import User
        import bcrypt
        
        db = SessionLocal()
        try:
            # Check if email already exists
            existing = db.query(User).filter(User.email == user_data['email']).first()
            if existing:
                raise ValueError("البريد الإلكتروني موجود بالفعل")
            
            # Hash password
            password = user_data.pop('password')
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            user = User(
                **user_data,
                password_hash=hashed_password.decode('utf-8')
            )
            
            db.add(user)
            db.commit()
            
            self.logger.info(f"Created user: {user.email}")
            return user
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating user: {str(e)}")
            raise e
        finally:
            db.close()
    
    def update_user(self, user_id, user_data):
        """Update existing user"""
        from config.database import SessionLocal
        from models.user import User
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("المستخدم غير موجود")
            
            # Check if email is being changed and already exists
            if 'email' in user_data and user_data['email'] != user.email:
                existing = db.query(User).filter(
                    User.email == user_data['email'],
                    User.id != user_id
                ).first()
                if existing:
                    raise ValueError("البريد الإلكتروني موجود بالفعل")
            
            # Update user fields
            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            db.commit()
            self.logger.info(f"Updated user: {user.email}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating user {user_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def toggle_user_activation(self, user_id):
        """Toggle user activation status"""
        from config.database import SessionLocal
        from models.user import User
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("المستخدم غير موجود")
            
            user.active = not user.active
            db.commit()
            
            action = "activated" if user.active else "deactivated"
            self.logger.info(f"User {user.email} {action}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error toggling user activation {user_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def reset_user_password(self, user_id, new_password):
        """Reset user password"""
        from config.database import SessionLocal
        from models.user import User
        import bcrypt
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("المستخدم غير موجود")
            
            # Hash new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            user.password_hash = hashed_password.decode('utf-8')
            
            db.commit()
            self.logger.info(f"Password reset for user: {user.email}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error resetting password for user {user_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def update_role_permissions(self, role_id, permissions_json):
        """Update role permissions"""
        from config.database import SessionLocal
        from models.user import Role
        
        db = SessionLocal()
        try:
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ValueError("الدور غير موجود")
            
            role.permissions_json = permissions_json
            db.commit()
            
            self.logger.info(f"Updated permissions for role: {role.name}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating role permissions {role_id}: {str(e)}")
            raise e
        finally:
            db.close()
