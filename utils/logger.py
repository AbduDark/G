import logging
import os
from pathlib import Path
from datetime import datetime
import sys

def setup_logger():
    """Setup the main application logger"""
    # Create logs directory
    log_dir = Path.home() / "AppData" / "Roaming" / "AlHussinyShop" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log filename with date
    log_filename = f"hussiny_{datetime.now().strftime('%Y%m%d')}.log"
    log_filepath = log_dir / log_filename
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_filepath), encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('AlHussiny')
    logger.info("تم تشغيل نظام السجلات")
    
    return logger

def get_logger(name=None):
    """Get a logger instance for a specific module"""
    if name:
        return logging.getLogger(f'AlHussiny.{name}')
    else:
        return logging.getLogger('AlHussiny')

class DatabaseLogger:
    """Database operations logger"""
    
    def __init__(self):
        self.logger = get_logger('Database')
    
    def log_query(self, query, params=None):
        """Log database queries"""
        if params:
            self.logger.debug(f"SQL Query: {query} | Params: {params}")
        else:
            self.logger.debug(f"SQL Query: {query}")
    
    def log_transaction_start(self, operation):
        """Log transaction start"""
        self.logger.info(f"Transaction started: {operation}")
    
    def log_transaction_commit(self, operation):
        """Log successful transaction commit"""
        self.logger.info(f"Transaction committed: {operation}")
    
    def log_transaction_rollback(self, operation, error):
        """Log transaction rollback"""
        self.logger.error(f"Transaction rolled back: {operation} - Error: {error}")
    
    def log_connection_error(self, error):
        """Log database connection errors"""
        self.logger.critical(f"Database connection error: {error}")

class SecurityLogger:
    """Security and authentication logger"""
    
    def __init__(self):
        self.logger = get_logger('Security')
    
    def log_login_attempt(self, email, success, ip_address=None):
        """Log login attempts"""
        status = "نجح" if success else "فشل"
        ip_info = f" من IP: {ip_address}" if ip_address else ""
        self.logger.info(f"محاولة تسجيل دخول {status} للمستخدم: {email}{ip_info}")
    
    def log_logout(self, email):
        """Log user logout"""
        self.logger.info(f"تسجيل خروج للمستخدم: {email}")
    
    def log_password_change(self, email):
        """Log password changes"""
        self.logger.info(f"تم تغيير كلمة المرور للمستخدم: {email}")
    
    def log_permission_denied(self, email, action):
        """Log permission denied events"""
        self.logger.warning(f"رُفِضَ الوصول للمستخدم {email} للعملية: {action}")
    
    def log_suspicious_activity(self, email, activity):
        """Log suspicious activities"""
        self.logger.warning(f"نشاط مشبوه من المستخدم {email}: {activity}")

class BusinessLogger:
    """Business operations logger"""
    
    def __init__(self):
        self.logger = get_logger('Business')
    
    def log_sale_created(self, invoice_no, total, user):
        """Log new sale creation"""
        self.logger.info(f"تم إنشاء فاتورة جديدة: {invoice_no} - المبلغ: {total:.2f} - المستخدم: {user}")
    
    def log_product_added(self, product_name, sku, user):
        """Log new product addition"""
        self.logger.info(f"تم إضافة منتج جديد: {product_name} ({sku}) - بواسطة: {user}")
    
    def log_stock_movement(self, product_name, change_qty, movement_type, user):
        """Log stock movements"""
        self.logger.info(f"حركة مخزون: {product_name} - الكمية: {change_qty} - النوع: {movement_type} - المستخدم: {user}")
    
    def log_repair_created(self, ticket_no, customer, device, user):
        """Log repair ticket creation"""
        self.logger.info(f"تم إنشاء تذكرة صيانة: {ticket_no} - العميل: {customer} - الجهاز: {device} - المستخدم: {user}")
    
    def log_backup_created(self, backup_path, user):
        """Log backup creation"""
        self.logger.info(f"تم إنشاء نسخة احتياطية: {backup_path} - بواسطة: {user}")
    
    def log_backup_restored(self, backup_path, user):
        """Log backup restoration"""
        self.logger.warning(f"تم استعادة نسخة احتياطية: {backup_path} - بواسطة: {user}")
    
    def log_data_export(self, export_type, file_path, user):
        """Log data exports"""
        self.logger.info(f"تم تصدير البيانات: {export_type} إلى {file_path} - بواسطة: {user}")
    
    def log_data_import(self, import_type, file_path, records_count, user):
        """Log data imports"""
        self.logger.info(f"تم استيراد البيانات: {import_type} من {file_path} - عدد السجلات: {records_count} - بواسطة: {user}")

class ErrorLogger:
    """Error and exception logger"""
    
    def __init__(self):
        self.logger = get_logger('Error')
    
    def log_exception(self, exception, context=None):
        """Log exceptions with context"""
        context_info = f" - السياق: {context}" if context else ""
        self.logger.error(f"خطأ: {str(exception)}{context_info}", exc_info=True)
    
    def log_validation_error(self, field, value, error):
        """Log validation errors"""
        self.logger.warning(f"خطأ في التحقق - الحقل: {field} - القيمة: {value} - الخطأ: {error}")
    
    def log_file_error(self, operation, file_path, error):
        """Log file operation errors"""
        self.logger.error(f"خطأ في العملية على الملف: {operation} - المسار: {file_path} - الخطأ: {error}")
    
    def log_network_error(self, operation, error):
        """Log network errors"""
        self.logger.error(f"خطأ شبكة في العملية: {operation} - الخطأ: {error}")
    
    def log_configuration_error(self, setting, error):
        """Log configuration errors"""
        self.logger.error(f"خطأ في الإعدادات: {setting} - الخطأ: {error}")

class PerformanceLogger:
    """Performance monitoring logger"""
    
    def __init__(self):
        self.logger = get_logger('Performance')
    
    def log_slow_query(self, query, duration):
        """Log slow database queries"""
        self.logger.warning(f"استعلام بطيء ({duration:.2f}s): {query}")
    
    def log_memory_usage(self, operation, memory_mb):
        """Log memory usage"""
        self.logger.info(f"استخدام الذاكرة - العملية: {operation} - الذاكرة: {memory_mb:.2f} MB")
    
    def log_operation_time(self, operation, duration):
        """Log operation execution time"""
        if duration > 5.0:  # Log operations taking more than 5 seconds
            self.logger.info(f"عملية طويلة - {operation}: {duration:.2f} seconds")

# Utility functions for common logging patterns
def log_user_action(user, action, details=None):
    """Log user actions across the application"""
    logger = get_logger('UserAction')
    detail_info = f" - التفاصيل: {details}" if details else ""
    logger.info(f"المستخدم {user} قام بـ: {action}{detail_info}")

def log_system_event(event, severity='info'):
    """Log system events"""
    logger = get_logger('System')
    
    if severity == 'info':
        logger.info(f"حدث النظام: {event}")
    elif severity == 'warning':
        logger.warning(f"تحذير النظام: {event}")
    elif severity == 'error':
        logger.error(f"خطأ النظام: {event}")
    elif severity == 'critical':
        logger.critical(f"خطأ حرج في النظام: {event}")

def cleanup_old_logs(days_to_keep=30):
    """Clean up old log files"""
    try:
        log_dir = Path.home() / "AppData" / "Roaming" / "AlHussinyShop" / "logs"
        if not log_dir.exists():
            return
        
        current_time = datetime.now()
        deleted_count = 0
        
        for log_file in log_dir.glob("*.log"):
            file_age = current_time - datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if file_age.days > days_to_keep:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger = get_logger('LogCleanup')
                    logger.error(f"فشل في حذف ملف السجل القديم {log_file}: {e}")
        
        if deleted_count > 0:
            logger = get_logger('LogCleanup')
            logger.info(f"تم حذف {deleted_count} ملف سجل قديم")
            
    except Exception as e:
        logger = get_logger('LogCleanup')
        logger.error(f"خطأ في تنظيف ملفات السجل القديمة: {e}")

# Initialize loggers on import
db_logger = DatabaseLogger()
security_logger = SecurityLogger()
business_logger = BusinessLogger()
error_logger = ErrorLogger()
performance_logger = PerformanceLogger()

# Set up periodic log cleanup (can be called from main application)
def setup_log_rotation():
    """Setup automatic log rotation"""
    import threading
    import time
    
    def cleanup_worker():
        while True:
            try:
                cleanup_old_logs()
                time.sleep(86400)  # Run once per day
            except Exception as e:
                error_logger.log_exception(e, "Log cleanup worker")
                time.sleep(86400)  # Continue even if cleanup fails
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()

# Context manager for operation logging
class LoggedOperation:
    """Context manager for logging operations with timing"""
    
    def __init__(self, operation_name, user=None, log_performance=True):
        self.operation_name = operation_name
        self.user = user
        self.log_performance = log_performance
        self.start_time = None
        self.logger = get_logger('Operation')
    
    def __enter__(self):
        self.start_time = datetime.now()
        if self.user:
            log_user_action(self.user, f"بدء {self.operation_name}")
        else:
            self.logger.info(f"بدء العملية: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            # Operation completed successfully
            if self.user:
                log_user_action(self.user, f"انتهاء {self.operation_name}", f"المدة: {duration:.2f}s")
            else:
                self.logger.info(f"انتهت العملية بنجاح: {self.operation_name} ({duration:.2f}s)")
            
            if self.log_performance:
                performance_logger.log_operation_time(self.operation_name, duration)
        else:
            # Operation failed
            if self.user:
                log_user_action(self.user, f"فشل في {self.operation_name}", f"الخطأ: {exc_val}")
            else:
                self.logger.error(f"فشلت العملية: {self.operation_name} - الخطأ: {exc_val}")
            
            error_logger.log_exception(exc_val, self.operation_name)
        
        return False  # Don't suppress exceptions
