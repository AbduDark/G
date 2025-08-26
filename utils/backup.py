# -*- coding: utf-8 -*-
"""
Legacy backup utilities for compatibility
This file maintains the backup_database and restore_database functions
that were referenced in the existing codebase.
"""

import logging
from pathlib import Path
from datetime import datetime
import shutil

from config import Config

logger = logging.getLogger(__name__)

def create_backup(app=None, backup_path=None):
    """Create database backup - legacy function for compatibility"""
    try:
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = Config.DB_BACKUP_DIR / f'hussiny_backup_{timestamp}.db'
        
        # Ensure backup directory exists
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy database file
        shutil.copy2(Config.DB_PATH, backup_path)
        
        logger.info(f"تم إنشاء نسخة احتياطية: {backup_path}")
        return str(backup_path)
        
    except Exception as e:
        logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
        return None

def restore_backup(app=None, backup_path=None):
    """Restore database from backup - legacy function for compatibility"""
    try:
        if not backup_path or not Path(backup_path).exists():
            logger.error("ملف النسخة الاحتياطية غير موجود")
            return False
        
        # Create backup of current database
        current_backup = create_backup(backup_path=f"{Config.DB_PATH}.pre_restore_backup")
        if current_backup:
            logger.info(f"تم إنشاء نسخة احتياطية من قاعدة البيانات الحالية: {current_backup}")
        
        # Restore from backup
        shutil.copy2(backup_path, Config.DB_PATH)
        
        logger.info(f"تم استعادة قاعدة البيانات من: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"خطأ في استعادة قاعدة البيانات: {e}")
        return False
