# -*- coding: utf-8 -*-
"""
Backup management utilities for Al-Hussiny Mobile Shop POS System
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
import zipfile
import json

from config import Config

logger = logging.getLogger(__name__)

class BackupManager:
    """Database backup and restore manager"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.backup_dir = Config.DB_BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, include_attachments=True, compress=True):
        """Create a complete backup of the database and optional attachments"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if compress:
                backup_filename = f'hussiny_backup_{timestamp}.zip'
                backup_path = self.backup_dir / backup_filename
                return self._create_compressed_backup(backup_path, include_attachments)
            else:
                backup_filename = f'hussiny_backup_{timestamp}.db'
                backup_path = self.backup_dir / backup_filename
                return self._create_simple_backup(backup_path)
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            return None
    
    def _create_simple_backup(self, backup_path):
        """Create simple database file backup"""
        try:
            # Copy database file
            shutil.copy2(Config.DB_PATH, backup_path)
            
            # Record backup
            self._record_backup(backup_path)
            
            logger.info(f"تم إنشاء نسخة احتياطية بسيطة: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية البسيطة: {e}")
            return None
    
    def _create_compressed_backup(self, backup_path, include_attachments):
        """Create compressed backup with database and optional attachments"""
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database file
                zipf.write(Config.DB_PATH, 'hussiny.db')
                
                # Add configuration info
                backup_info = {
                    'created_at': datetime.now().isoformat(),
                    'app_version': Config.APP_VERSION,
                    'database_version': '1.0',
                    'includes_attachments': include_attachments
                }
                zipf.writestr('backup_info.json', json.dumps(backup_info, ensure_ascii=False, indent=2))
                
                # Add attachments if requested
                if include_attachments:
                    self._add_attachments_to_zip(zipf)
            
            # Record backup
            self._record_backup(backup_path)
            
            logger.info(f"تم إنشاء نسخة احتياطية مضغوطة: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية المضغوطة: {e}")
            return None
    
    def _add_attachments_to_zip(self, zipf):
        """Add attachment files to zip backup"""
        try:
            # Add any attachment directories
            attachments_dirs = [
                Config.EXPORTS_DIR,
                Config.FONTS_DIR / "*.ttf",  # Only TTF fonts
                Config.ICONS_DIR
            ]
            
            for attach_dir in attachments_dirs:
                if isinstance(attach_dir, Path) and attach_dir.exists():
                    if attach_dir.is_dir():
                        for file_path in attach_dir.rglob('*'):
                            if file_path.is_file():
                                # Add file with relative path
                                arcname = str(file_path.relative_to(Config.BASE_DIR))
                                zipf.write(file_path, arcname)
                                
        except Exception as e:
            logger.error(f"خطأ في إضافة المرفقات للنسخة الاحتياطية: {e}")
    
    def restore_backup(self, backup_path, restore_attachments=True):
        """Restore database from backup file"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"ملف النسخة الاحتياطية غير موجود: {backup_path}")
            
            # Create pre-restore backup
            pre_restore_backup = self.create_backup(compress=False)
            if pre_restore_backup:
                logger.info(f"تم إنشاء نسخة احتياطية قبل الاستعادة: {pre_restore_backup}")
            
            if backup_file.suffix == '.zip':
                return self._restore_compressed_backup(backup_file, restore_attachments)
            else:
                return self._restore_simple_backup(backup_file)
                
        except Exception as e:
            logger.error(f"خطأ في استعادة النسخة الاحتياطية: {e}")
            return False
    
    def _restore_simple_backup(self, backup_file):
        """Restore from simple database backup"""
        try:
            # Close database connections
            if hasattr(self.db_manager, 'engine') and self.db_manager.engine:
                self.db_manager.engine.dispose()
            
            # Restore database file
            shutil.copy2(backup_file, Config.DB_PATH)
            
            # Reinitialize database connection
            self.db_manager.initialize()
            
            logger.info(f"تم استعادة قاعدة البيانات من: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في استعادة النسخة الاحتياطية البسيطة: {e}")
            return False
    
    def _restore_compressed_backup(self, backup_file, restore_attachments):
        """Restore from compressed backup"""
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Check backup info
                try:
                    backup_info_data = zipf.read('backup_info.json')
                    backup_info = json.loads(backup_info_data)
                    logger.info(f"استعادة نسخة احتياطية من: {backup_info['created_at']}")
                except:
                    logger.warning("لا توجد معلومات عن النسخة الاحتياطية")
                
                # Close database connections
                if hasattr(self.db_manager, 'engine') and self.db_manager.engine:
                    self.db_manager.engine.dispose()
                
                # Extract database
                zipf.extract('hussiny.db', Config.BASE_DIR)
                extracted_db = Config.BASE_DIR / 'hussiny.db'
                shutil.move(extracted_db, Config.DB_PATH)
                
                # Extract attachments if requested
                if restore_attachments:
                    self._extract_attachments_from_zip(zipf)
            
            # Reinitialize database connection
            self.db_manager.initialize()
            
            logger.info(f"تم استعادة النسخة الاحتياطية المضغوطة من: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في استعادة النسخة الاحتياطية المضغوطة: {e}")
            return False
    
    def _extract_attachments_from_zip(self, zipf):
        """Extract attachment files from zip backup"""
        try:
            for file_info in zipf.filelist:
                if file_info.filename not in ['hussiny.db', 'backup_info.json']:
                    # Extract to original location
                    extract_path = Config.BASE_DIR / file_info.filename
                    extract_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with zipf.open(file_info) as source, open(extract_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                        
        except Exception as e:
            logger.error(f"خطأ في استخراج المرفقات: {e}")
    
    def _record_backup(self, backup_path):
        """Record backup in database"""
        try:
            session = self.db_manager.get_session()
            try:
                from models import Backup
                
                backup_record = Backup(
                    file_path=str(backup_path),
                    size=Path(backup_path).stat().st_size,
                    created_by=1  # Should be current user ID
                )
                session.add(backup_record)
                session.commit()
                
            except Exception as e:
                session.rollback()
                logger.error(f"خطأ في تسجيل النسخة الاحتياطية: {e}")
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"خطأ في تسجيل النسخة الاحتياطية: {e}")
    
    def list_backups(self):
        """List available backup files"""
        try:
            backup_files = []
            
            # Get all backup files
            for pattern in ['hussiny_backup_*.db', 'hussiny_backup_*.zip']:
                backup_files.extend(self.backup_dir.glob(pattern))
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            # Get file info
            backups = []
            for backup_file in backup_files:
                stat = backup_file.stat()
                backup_info = {
                    'path': str(backup_file),
                    'name': backup_file.name,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'type': 'مضغوط' if backup_file.suffix == '.zip' else 'بسيط'
                }
                backups.append(backup_info)
            
            return backups
            
        except Exception as e:
            logger.error(f"خطأ في قراءة قائمة النسخ الاحتياطية: {e}")
            return []
    
    def cleanup_old_backups(self, max_backups=None):
        """Remove old backup files"""
        if max_backups is None:
            max_backups = Config.DB_MAX_BACKUPS
        
        try:
            backups = self.list_backups()
            
            if len(backups) > max_backups:
                # Remove old backups
                for backup in backups[max_backups:]:
                    try:
                        Path(backup['path']).unlink()
                        logger.info(f"تم حذف النسخة الاحتياطية القديمة: {backup['name']}")
                    except Exception as e:
                        logger.error(f"خطأ في حذف النسخة الاحتياطية {backup['name']}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تنظيف النسخ الاحتياطية: {e}")
            return False
    
    def schedule_auto_backup(self):
        """Setup automatic backup scheduling"""
        try:
            from PyQt6.QtCore import QTimer
            
            # Create timer for auto backup
            self.auto_backup_timer = QTimer()
            self.auto_backup_timer.timeout.connect(self._perform_auto_backup)
            
            # Start timer (interval in milliseconds)
            interval_hours = Config.AUTO_BACKUP_INTERVAL
            interval_ms = interval_hours * 60 * 60 * 1000
            self.auto_backup_timer.start(interval_ms)
            
            logger.info(f"تم تفعيل النسخ الاحتياطي التلقائي كل {interval_hours} ساعة")
            
        except Exception as e:
            logger.error(f"خطأ في تشغيل النسخ الاحتياطي التلقائي: {e}")
    
    def _perform_auto_backup(self):
        """Perform automatic backup"""
        try:
            if Config.AUTO_BACKUP_ENABLED:
                backup_path = self.create_backup(
                    include_attachments=False,
                    compress=Config.BACKUP_COMPRESSION
                )
                
                if backup_path:
                    logger.info(f"تم إنشاء نسخة احتياطية تلقائية: {backup_path}")
                    
                    # Cleanup old backups
                    self.cleanup_old_backups()
                else:
                    logger.error("فشل في إنشاء النسخة الاحتياطية التلقائية")
            
        except Exception as e:
            logger.error(f"خطأ في النسخ الاحتياطي التلقائي: {e}")
    
    def export_to_cloud(self, backup_path, cloud_folder):
        """Export backup to cloud sync folder"""
        try:
            cloud_path = Path(cloud_folder)
            if not cloud_path.exists():
                cloud_path.mkdir(parents=True, exist_ok=True)
            
            backup_file = Path(backup_path)
            destination = cloud_path / backup_file.name
            
            shutil.copy2(backup_file, destination)
            
            logger.info(f"تم تصدير النسخة الاحتياطية إلى: {destination}")
            return str(destination)
            
        except Exception as e:
            logger.error(f"خطأ في تصدير النسخة الاحتياطية للسحابة: {e}")
            return None
    
    def verify_backup(self, backup_path):
        """Verify backup file integrity"""
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False, "ملف النسخة الاحتياطية غير موجود"
            
            if backup_file.suffix == '.zip':
                return self._verify_zip_backup(backup_file)
            else:
                return self._verify_db_backup(backup_file)
                
        except Exception as e:
            logger.error(f"خطأ في التحقق من النسخة الاحتياطية: {e}")
            return False, str(e)
    
    def _verify_zip_backup(self, backup_file):
        """Verify compressed backup file"""
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Test ZIP file integrity
                zipf.testzip()
                
                # Check required files
                file_list = zipf.namelist()
                if 'hussiny.db' not in file_list:
                    return False, "ملف قاعدة البيانات غير موجود في النسخة الاحتياطية"
                
                # Check database file
                with zipf.open('hussiny.db') as db_file:
                    # Basic SQLite header check
                    header = db_file.read(16)
                    if not header.startswith(b'SQLite format 3\x00'):
                        return False, "ملف قاعدة البيانات تالف"
            
            return True, "النسخة الاحتياطية سليمة"
            
        except zipfile.BadZipFile:
            return False, "ملف النسخة الاحتياطية تالف"
        except Exception as e:
            return False, f"خطأ في التحقق من النسخة الاحتياطية: {e}"
    
    def _verify_db_backup(self, backup_file):
        """Verify database backup file"""
        try:
            # Check file size
            if backup_file.stat().st_size < 1024:  # Less than 1KB
                return False, "حجم ملف النسخة الاحتياطية صغير جداً"
            
            # Check SQLite header
            with open(backup_file, 'rb') as f:
                header = f.read(16)
                if not header.startswith(b'SQLite format 3\x00'):
                    return False, "ملف قاعدة البيانات تالف"
            
            return True, "النسخة الاحتياطية سليمة"
            
        except Exception as e:
            return False, f"خطأ في التحقق من النسخة الاحتياطية: {e}"
