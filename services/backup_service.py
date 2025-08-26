import os
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from config.database import DB_PATH, BASE_DIR
from config.settings import app_settings
from utils.logger import get_logger

class BackupService:
    """Service for backup and restore operations"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.backup_dir = BASE_DIR / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, backup_name=None):
        """Create database backup"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"hussiny_backup_{timestamp}"
            
            backup_file = self.backup_dir / f"{backup_name}.db"
            
            # Copy database file
            shutil.copy2(DB_PATH, backup_file)
            
            # Create zip archive with additional files if needed
            zip_file = self.backup_dir / f"{backup_name}.zip"
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add database
                zf.write(backup_file, f"{backup_name}.db")
                
                # Add settings if exists
                settings_file = BASE_DIR / "settings.json"
                if settings_file.exists():
                    zf.write(settings_file, "settings.json")
            
            # Remove temporary db file
            backup_file.unlink()
            
            self.logger.info(f"Backup created: {zip_file}")
            
            # Clean old backups if auto-cleanup is enabled
            self.cleanup_old_backups()
            
            return zip_file
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {str(e)}")
            raise e
    
    def restore_backup(self, backup_file):
        """Restore from backup"""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                raise FileNotFoundError("ملف النسخة الاحتياطية غير موجود")
            
            # Create backup of current database before restore
            current_backup = self.create_backup("pre_restore_backup")
            
            if backup_path.suffix == '.zip':
                # Extract zip file
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    # Find database file in zip
                    db_files = [f for f in zf.namelist() if f.endswith('.db')]
                    if not db_files:
                        raise ValueError("ملف قاعدة البيانات غير موجود في النسخة الاحتياطية")
                    
                    # Extract database
                    zf.extract(db_files[0], self.backup_dir)
                    extracted_db = self.backup_dir / db_files[0]
                    
                    # Replace current database
                    shutil.copy2(extracted_db, DB_PATH)
                    extracted_db.unlink()
                    
                    # Extract settings if exists
                    if "settings.json" in zf.namelist():
                        zf.extract("settings.json", BASE_DIR)
            
            elif backup_path.suffix == '.db':
                # Direct database file
                shutil.copy2(backup_path, DB_PATH)
            
            else:
                raise ValueError("نوع ملف النسخة الاحتياطية غير مدعوم")
            
            self.logger.info(f"Backup restored from: {backup_file}")
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {str(e)}")
            raise e
    
    def get_backups_list(self):
        """Get list of available backups"""
        try:
            backups = []
            for file in self.backup_dir.glob("*.zip"):
                stat = file.stat()
                backups.append({
                    'name': file.name,
                    'path': str(file),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
            
            # Sort by creation date, newest first
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            self.logger.error(f"Error getting backups list: {str(e)}")
            raise e
    
    def cleanup_old_backups(self):
        """Clean up old backups based on settings"""
        try:
            max_backups = app_settings.get('backup.max_backups', 30)
            backups = self.get_backups_list()
            
            if len(backups) > max_backups:
                # Delete oldest backups
                for backup in backups[max_backups:]:
                    Path(backup['path']).unlink()
                    self.logger.info(f"Deleted old backup: {backup['name']}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {str(e)}")
    
    def schedule_auto_backup(self):
        """Schedule automatic backup (to be called from main app)"""
        try:
            if not app_settings.get('backup.auto_backup', True):
                return
            
            last_backup = app_settings.get('backup.last_auto_backup')
            frequency = app_settings.get('backup.backup_frequency', 'daily')
            
            now = datetime.now()
            should_backup = False
            
            if not last_backup:
                should_backup = True
            else:
                last_backup_date = datetime.fromisoformat(last_backup)
                if frequency == 'daily':
                    should_backup = now.date() > last_backup_date.date()
                elif frequency == 'weekly':
                    should_backup = (now - last_backup_date).days >= 7
            
            if should_backup:
                backup_file = self.create_backup("auto_backup")
                app_settings.set('backup.last_auto_backup', now.isoformat())
                self.logger.info("Automatic backup created")
                
        except Exception as e:
            self.logger.error(f"Error in auto backup: {str(e)}")
    
    def export_to_cloud_folder(self, backup_file, cloud_folder):
        """Export backup to cloud sync folder"""
        try:
            cloud_path = Path(cloud_folder)
            if not cloud_path.exists():
                raise FileNotFoundError("مجلد المزامنة غير موجود")
            
            backup_path = Path(backup_file)
            destination = cloud_path / backup_path.name
            
            shutil.copy2(backup_path, destination)
            self.logger.info(f"Backup exported to cloud folder: {destination}")
            
        except Exception as e:
            self.logger.error(f"Error exporting to cloud: {str(e)}")
            raise e
