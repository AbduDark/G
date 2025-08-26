from functools import wraps
from flask import session, redirect, url_for, flash, request
from models import User, Role

def login_required(f):
    """Decorator to require login for accessing routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for accessing routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.role.has_permission('all'):
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """Decorator to require specific permission for accessing routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('يجب تسجيل الدخول أولاً', 'error')
                return redirect(url_for('login'))
            
            user = User.query.get(session['user_id'])
            if not user or not user.role.has_permission(permission):
                flash('ليس لديك صلاحية لتنفيذ هذا الإجراء', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current logged in user"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def log_audit(action, details=None, user=None):
    """Log audit trail for important actions"""
    from models import db, AuditLog
    
    if user is None:
        user = get_current_user()
    
    if user:
        audit_log = AuditLog(
            user_id=user.id,
            action=action,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
