# -*- coding: utf-8 -*-
"""
Application settings and configuration
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class DatabaseSettings:
    """Database configuration"""
    path: str = ""
    backup_dir: str = ""
    auto_backup: bool = True
    backup_interval: int = 24  # hours
    max_backups: int = 30

@dataclass
class PrinterSettings:
    """Printer configuration"""
    default_printer: str = ""
    thermal_printer: str = ""
    page_size: str = "A4"
    margin_top: int = 20
    margin_bottom: int = 20
    margin_left: int = 20
    margin_right: int = 20

@dataclass
class ShopSettings:
    """Shop information"""
    name: str = "محل الحسيني"
    address: str = ""
    phone: str = ""
    email: str = ""
    tax_number: str = ""
    currency: str = "ج.م"
    tax_rate: float = 0.0

@dataclass
class UISettings:
    """User interface settings"""
    theme: str = "light"  # light, dark
    font_family: str = "Cairo"
    font_size: int = 12
    window_size: Dict[str, int] = None
    language: str = "ar"

    def __post_init__(self):
        if self.window_size is None:
            self.window_size = {"width": 1200, "height": 800}

class AppSettings:
    """Application settings manager"""
    
    def __init__(self):
        self.settings_dir = self.get_settings_dir()
        self.settings_file = self.settings_dir / "settings.json"
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        
        # Default settings
        self.database = DatabaseSettings()
        self.printer = PrinterSettings()
        self.shop = ShopSettings()
        self.ui = UISettings()
        
        # Load existing settings
        self.load()
        
    def get_settings_dir(self) -> Path:
        """Get settings directory path"""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', Path.home()))
        else:
            base_dir = Path.home() / ".config"
        
        return base_dir / "AlHussinyShop"
    
    def load(self):
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Update settings from loaded data
                if 'database' in data:
                    self.database = DatabaseSettings(**data['database'])
                if 'printer' in data:
                    self.printer = PrinterSettings(**data['printer'])
                if 'shop' in data:
                    self.shop = ShopSettings(**data['shop'])
                if 'ui' in data:
                    self.ui = UISettings(**data['ui'])
                    
        except Exception as e:
            print(f"Failed to load settings: {e}")
    
    def save(self):
        """Save settings to file"""
        try:
            data = {
                'database': asdict(self.database),
                'printer': asdict(self.printer),
                'shop': asdict(self.shop),
                'ui': asdict(self.ui)
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Failed to save settings: {e}")
    
    def get_database_path(self) -> Path:
        """Get database file path"""
        if self.database.path:
            return Path(self.database.path)
        
        # Default database location
        return self.settings_dir / "hussiny.db"
    
    def get_backup_dir(self) -> Path:
        """Get backup directory path"""
        if self.database.backup_dir:
            return Path(self.database.backup_dir)
        
        # Default backup location
        return self.settings_dir / "backups"

# Global settings instance
settings = AppSettings()
