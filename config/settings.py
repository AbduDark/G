import os
import json
from pathlib import Path

class Settings:
    """Application settings manager"""
    
    def __init__(self):
        self.settings_dir = Path.home() / "AppData" / "Roaming" / "AlHussinyShop"
        self.settings_file = self.settings_dir / "settings.json"
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        
        # Default settings
        self.default_settings = {
            "shop_info": {
                "name": "محل الحسيني",
                "address": "العنوان",
                "phone": "رقم الهاتف",
                "email": "info@alhussiny.com"
            },
            "invoice": {
                "tax_rate": 14.0,
                "currency": "جنيه مصري",
                "footer_text": "شكراً لتعاملكم معنا"
            },
            "ui": {
                "theme": "light",
                "language": "ar",
                "font_size": 10
            },
            "backup": {
                "auto_backup": True,
                "backup_frequency": "daily",
                "max_backups": 30
            },
            "printer": {
                "thermal_printer": False,
                "printer_name": "",
                "paper_width": 80
            }
        }
        
        self.load_settings()
    
    def load_settings(self):
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in self.default_settings.items():
                        if key not in self.settings:
                            self.settings[key] = value
            else:
                self.settings = self.default_settings.copy()
                self.save_settings()
        except Exception:
            self.settings = self.default_settings.copy()
    
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get(self, key, default=None):
        """Get setting value"""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            value = value.get(k, {})
            if not isinstance(value, dict):
                return value
        return default if value == {} else value
    
    def set(self, key, value):
        """Set setting value"""
        keys = key.split('.')
        setting = self.settings
        for k in keys[:-1]:
            if k not in setting:
                setting[k] = {}
            setting = setting[k]
        setting[keys[-1]] = value
        self.save_settings()

# Global settings instance
app_settings = Settings()
