from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc
from models import db, User, Role
from auth import login_required, admin_required, get_current_user, log_audit

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
@login_required
@admin_required
def list_users():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(User.name.contains(search) | User.email.contains(search))
    
    users = query.order_by(desc(User.created_at))\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('users/list.html', users=users, search=search)

@users_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add new user"""
    if request.method == 'POST':
        try:
            # Check if email already exists
            existing_user = User.query.filter_by(email=request.form['email']).first()
            if existing_user:
                flash('البريد الإلكتروني مستخدم من قبل', 'error')
                return render_template('users/form.html', user=None, roles=Role.query.all())
            
            user = User(
                email=request.form['email'],
                password_hash=generate_password_hash(request.form['password']),
                name=request.form['name'],
                role_id=request.form['role_id']
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Log audit
            log_audit('add_user', f'تم إضافة مستخدم جديد: {user.email}')
            
            flash('تم إضافة المستخدم بنجاح', 'success')
            return redirect(url_for('users.list_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إضافة المستخدم: {str(e)}', 'error')
    
    # GET request
    roles = Role.query.order_by(Role.name_ar).all()
    return render_template('users/form.html', user=None, roles=roles)

@users_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    """Edit existing user"""
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Check if email changed and is unique
            if user.email != request.form['email']:
                existing_user = User.query.filter_by(email=request.form['email']).first()
                if existing_user:
                    flash('البريد الإلكتروني مستخدم من قبل', 'error')
                    return render_template('users/form.html', user=user, roles=Role.query.all())
            
            user.email = request.form['email']
            user.name = request.form['name']
            user.role_id = request.form['role_id']
            
            # Update password if provided
            if request.form['password']:
                user.password_hash = generate_password_hash(request.form['password'])
            
            db.session.commit()
            
            # Log audit
            log_audit('edit_user', f'تم تحديث المستخدم: {user.email}')
            
            flash('تم تحديث المستخدم بنجاح', 'success')
            return redirect(url_for('users.list_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في تحديث المستخدم: {str(e)}', 'error')
    
    # GET request
    roles = Role.query.order_by(Role.name_ar).all()
    return render_template('users/form.html', user=user, roles=roles)

@users_bp.route('/toggle-active/<int:id>')
@login_required
@admin_required
def toggle_active(id):
    """Toggle user active status"""
    user = User.query.get_or_404(id)
    
    # Prevent deactivating own account
    if user.id == get_current_user().id:
        flash('لا يمكنك إلغاء تفعيل حسابك الخاص', 'error')
        return redirect(url_for('users.list_users'))
    
    try:
        user.active = not user.active
        db.session.commit()
        
        status = 'تفعيل' if user.active else 'إلغاء تفعيل'
        log_audit('toggle_user_status', f'تم {status} المستخدم: {user.email}')
        
        flash(f'تم {status} المستخدم بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في تحديث حالة المستخدم: {str(e)}', 'error')
    
    return redirect(url_for('users.list_users'))

@users_bp.route('/roles')
@login_required
@admin_required
def list_roles():
    """List and manage user roles"""
    roles = Role.query.order_by(Role.name).all()
    return render_template('users/roles.html', roles=roles)

@users_bp.route('/roles/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_role():
    """Add new role"""
    if request.method == 'POST':
        try:
            # Parse permissions
            permissions = request.form.getlist('permissions')
            
            role = Role(
                name=request.form['name'],
                name_ar=request.form['name_ar'],
                permissions=permissions
            )
            
            db.session.add(role)
            db.session.commit()
            
            # Log audit
            log_audit('add_role', f'تم إضافة دور جديد: {role.name_ar}')
            
            flash('تم إضافة الدور بنجاح', 'success')
            return redirect(url_for('users.list_roles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إضافة الدور: {str(e)}', 'error')
    
    # Available permissions
    available_permissions = [
        {'key': 'all', 'name': 'جميع الصلاحيات'},
        {'key': 'sales', 'name': 'المبيعات'},
        {'key': 'inventory', 'name': 'المخزون'},
        {'key': 'repairs', 'name': 'الصيانة'},
        {'key': 'reports', 'name': 'التقارير'},
        {'key': 'users', 'name': 'إدارة المستخدمين'},
        {'key': 'returns', 'name': 'المرتجعات'},
        {'key': 'inventory_view', 'name': 'عرض المخزون فقط'},
        {'key': 'view_only', 'name': 'عرض فقط'}
    ]
    
    return render_template('users/role_form.html', 
                         role=None, 
                         available_permissions=available_permissions)

@users_bp.route('/roles/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role(id):
    """Edit existing role"""
    role = Role.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Parse permissions
            permissions = request.form.getlist('permissions')
            
            role.name = request.form['name']
            role.name_ar = request.form['name_ar']
            role.permissions = permissions
            
            db.session.commit()
            
            # Log audit
            log_audit('edit_role', f'تم تحديث الدور: {role.name_ar}')
            
            flash('تم تحديث الدور بنجاح', 'success')
            return redirect(url_for('users.list_roles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في تحديث الدور: {str(e)}', 'error')
    
    # Available permissions
    available_permissions = [
        {'key': 'all', 'name': 'جميع الصلاحيات'},
        {'key': 'sales', 'name': 'المبيعات'},
        {'key': 'inventory', 'name': 'المخزون'},
        {'key': 'repairs', 'name': 'الصيانة'},
        {'key': 'reports', 'name': 'التقارير'},
        {'key': 'users', 'name': 'إدارة المستخدمين'},
        {'key': 'returns', 'name': 'المرتجعات'},
        {'key': 'inventory_view', 'name': 'عرض المخزون فقط'},
        {'key': 'view_only', 'name': 'عرض فقط'}
    ]
    
    return render_template('users/role_form.html', 
                         role=role, 
                         available_permissions=available_permissions)

@users_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = get_current_user()
    return render_template('users/profile.html', user=user)

@users_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    user = get_current_user()
    
    try:
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Verify current password
        if not check_password_hash(user.password_hash, current_password):
            flash('كلمة المرور الحالية غير صحيحة', 'error')
            return redirect(url_for('users.profile'))
        
        # Verify new password confirmation
        if new_password != confirm_password:
            flash('كلمة المرور الجديدة وتأكيدها غير متطابقتان', 'error')
            return redirect(url_for('users.profile'))
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        # Log audit
        log_audit('change_password', 'تم تغيير كلمة المرور')
        
        flash('تم تغيير كلمة المرور بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في تغيير كلمة المرور: {str(e)}', 'error')
    
    return redirect(url_for('users.profile'))
