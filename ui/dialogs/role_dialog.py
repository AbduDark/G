# -*- coding: utf-8 -*-
"""
Role add/edit dialog
"""

import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLineEdit, QPushButton, QLabel, QGroupBox, QTreeWidget,
                            QTreeWidgetItem, QCheckBox, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.user import User, Role
from config.database import get_db_session
from utils.helpers import show_error, show_success

class RoleDialog(QDialog):
    """Dialog for adding/editing roles and permissions"""
    
    def __init__(self, parent=None, current_user: User = None, role_id: int = None, copy_mode: bool = False):
        super().__init__(parent)
        self.current_user = current_user
        self.role_id = role_id
        self.copy_mode = copy_mode
        self.role = None
        
        self.setup_ui()
        
        if role_id:
            self.load_role()
            
    def setup_ui(self):
        """Setup user interface"""
        title = "إضافة دور جديد"
        if self.role_id and not self.copy_mode:
            title = "تعديل الدور"
        elif self.copy_mode:
            title = "نسخ الدور"
            
        self.setWindowTitle(title)
        self.setMinimumSize(600, 700)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Role info group
        info_group = QGroupBox("معلومات الدور")
        info_layout = QFormLayout()
        
        # Role name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم الدور")
        
        info_layout.addRow("اسم الدور *:", self.name_input)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Permissions group
        permissions_group = QGroupBox("الصلاحيات")
        permissions_layout = QVBoxLayout()
        
        # Permissions tree
        self.permissions_tree = QTreeWidget()
        self.permissions_tree.setHeaderLabels(["الوحدة", "عرض", "إنشاء", "تعديل", "حذف"])
        self.permissions_tree.setColumnWidth(0, 200)
        
        # Add permissions structure
        self.setup_permissions_tree()
        
        permissions_layout.addWidget(self.permissions_tree)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("تحديد الكل")
        self.clear_all_btn = QPushButton("إلغاء تحديد الكل")
        self.admin_preset_btn = QPushButton("صلاحيات المدير")
        self.manager_preset_btn = QPushButton("صلاحيات المدير المساعد")
        self.cashier_preset_btn = QPushButton("صلاحيات الكاشير")
        
        actions_layout.addWidget(self.select_all_btn)
        actions_layout.addWidget(self.clear_all_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.admin_preset_btn)
        actions_layout.addWidget(self.manager_preset_btn)
        actions_layout.addWidget(self.cashier_preset_btn)
        
        permissions_layout.addLayout(actions_layout)
        permissions_group.setLayout(permissions_layout)
        layout.addWidget(permissions_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("حفظ")
        self.cancel_btn = QPushButton("إلغاء")
        
        # Style save button
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        # Connect signals
        self.save_btn.clicked.connect(self.save_role)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.select_all_btn.clicked.connect(self.select_all_permissions)
        self.clear_all_btn.clicked.connect(self.clear_all_permissions)
        self.admin_preset_btn.clicked.connect(self.apply_admin_preset)
        self.manager_preset_btn.clicked.connect(self.apply_manager_preset)
        self.cashier_preset_btn.clicked.connect(self.apply_cashier_preset)
        
    def setup_permissions_tree(self):
        """Setup permissions tree structure"""
        self.permission_items = {}
        
        # Define modules and their permissions
        modules = {
            "users": {
                "name": "إدارة المستخدمين",
                "permissions": ["read", "create", "update", "delete"]
            },
            "products": {
                "name": "إدارة المنتجات",
                "permissions": ["read", "create", "update", "delete"]
            },
            "sales": {
                "name": "المبيعات",
                "permissions": ["read", "create", "update", "delete"]
            },
            "repairs": {
                "name": "الصيانة",
                "permissions": ["read", "create", "update", "delete"]
            },
            "transfers": {
                "name": "التحويلات",
                "permissions": ["read", "create", "update", "delete"]
            },
            "reports": {
                "name": "التقارير",
                "permissions": ["read"]
            },
            "settings": {
                "name": "الإعدادات",
                "permissions": ["read", "update"]
            },
            "backup": {
                "name": "النسخ الاحتياطي",
                "permissions": ["read", "create"]
            }
        }
        
        permission_names = {
            "read": "عرض",
            "create": "إنشاء",
            "update": "تعديل",
            "delete": "حذف"
        }
        
        for module_key, module_data in modules.items():
            # Create main module item
            module_item = QTreeWidgetItem([module_data["name"]])
            self.permissions_tree.addTopLevelItem(module_item)
            
            # Store checkboxes for this module
            self.permission_items[module_key] = {}
            
            # Add permission checkboxes
            for i, permission in enumerate(["read", "create", "update", "delete"], 1):
                if permission in module_data["permissions"]:
                    checkbox = QCheckBox()
                    self.permissions_tree.setItemWidget(module_item, i, checkbox)
                    self.permission_items[module_key][permission] = checkbox
                    
        # Expand all items
        self.permissions_tree.expandAll()
        
    def load_role(self):
        """Load role data for editing"""
        session = get_db_session()
        try:
            role = session.query(Role).get(self.role_id)
            if not role:
                show_error(self, "الدور غير موجود")
                self.reject()
                return
                
            self.role = role
            
            # Populate form fields
            role_name = role.name
            if self.copy_mode:
                role_name = f"نسخة من {role_name}"
                
            self.name_input.setText(role_name)
            
            # Set permissions
            permissions = role.permissions
            for module, module_permissions in permissions.items():
                if module in self.permission_items:
                    for permission in module_permissions:
                        if permission in self.permission_items[module]:
                            self.permission_items[module][permission].setChecked(True)
                            
        finally:
            session.close()
            
    def get_permissions_data(self):
        """Get permissions data from tree"""
        permissions = {}
        
        for module, module_permissions in self.permission_items.items():
            module_perms = []
            for permission, checkbox in module_permissions.items():
                if checkbox.isChecked():
                    module_perms.append(permission)
                    
            if module_perms:
                permissions[module] = module_perms
                
        return permissions
        
    def select_all_permissions(self):
        """Select all permissions"""
        for module, module_permissions in self.permission_items.items():
            for checkbox in module_permissions.values():
                checkbox.setChecked(True)
                
    def clear_all_permissions(self):
        """Clear all permissions"""
        for module, module_permissions in self.permission_items.items():
            for checkbox in module_permissions.values():
                checkbox.setChecked(False)
                
    def apply_admin_preset(self):
        """Apply admin permissions preset"""
        self.select_all_permissions()
        
    def apply_manager_preset(self):
        """Apply manager permissions preset"""
        self.clear_all_permissions()
        
        manager_permissions = {
            "products": ["read", "create", "update"],
            "sales": ["read", "create", "update"],
            "repairs": ["read", "create", "update"],
            "transfers": ["read", "create", "update"],
            "reports": ["read"],
            "settings": ["read"]
        }
        
        for module, permissions in manager_permissions.items():
            if module in self.permission_items:
                for permission in permissions:
                    if permission in self.permission_items[module]:
                        self.permission_items[module][permission].setChecked(True)
                        
    def apply_cashier_preset(self):
        """Apply cashier permissions preset"""
        self.clear_all_permissions()
        
        cashier_permissions = {
            "products": ["read"],
            "sales": ["read", "create"],
            "repairs": ["read"],
            "transfers": ["read", "create"],
            "reports": ["read"]
        }
        
        for module, permissions in cashier_permissions.items():
            if module in self.permission_items:
                for permission in permissions:
                    if permission in self.permission_items[module]:
                        self.permission_items[module][permission].setChecked(True)
                        
    def validate_form(self):
        """Validate form data"""
        # Required fields
        if not self.name_input.text().strip():
            show_error(self, "يرجى إدخال اسم الدور")
            self.name_input.setFocus()
            return False
            
        # Check if at least one permission is selected
        permissions = self.get_permissions_data()
        if not permissions:
            show_error(self, "يرجى تحديد صلاحية واحدة على الأقل")
            return False
            
        return True
        
    def check_duplicate_name(self, name: str):
        """Check for duplicate role name"""
        session = get_db_session()
        try:
            existing_role = session.query(Role).filter_by(name=name).first()
            
            # For copy mode or new role, check if name exists
            # For edit mode, check if name exists for different role
            if self.copy_mode or not self.role_id:
                if existing_role:
                    show_error(self, f"اسم الدور '{name}' موجود مسبقاً")
                    return False
            else:
                if existing_role and existing_role.id != self.role_id:
                    show_error(self, f"اسم الدور '{name}' موجود مسبقاً")
                    return False
                    
            return True
            
        finally:
            session.close()
            
    def save_role(self):
        """Save role data"""
        if not self.validate_form():
            return
            
        name = self.name_input.text().strip()
        if not self.check_duplicate_name(name):
            return
            
        session = get_db_session()
        try:
            if self.role_id and not self.copy_mode:
                # Update existing role
                role = session.query(Role).get(self.role_id)
                if not role:
                    show_error(self, "الدور غير موجود")
                    return
            else:
                # Create new role (new or copy)
                role = Role()
                
            # Update role data
            role.name = name
            role.permissions = self.get_permissions_data()
            
            if not self.role_id or self.copy_mode:
                session.add(role)
                
            session.commit()
            
            # Log the action
            from models.audit import AuditLog
            if self.copy_mode:
                action = "create"
                details = f"Copied role: {name} from {self.role.name}"
            elif not self.role_id:
                action = "create"
                details = f"Created role: {name}"
            else:
                action = "update"
                details = f"Updated role: {name}"
                
            AuditLog.log_action(
                session, self.current_user.id, action, "roles",
                record_id=role.id, details=details
            )
            session.commit()
            
            self.accept()
            
        except Exception as e:
            session.rollback()
            logging.error(f"Role save error: {e}")
            show_error(self, f"فشل في حفظ الدور:\n{str(e)}")
        finally:
            session.close()
