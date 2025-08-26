from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import desc, or_
from models import db, Repair, Customer
from auth import login_required, permission_required, get_current_user, log_audit
from datetime import datetime
import uuid

repairs_bp = Blueprint('repairs', __name__)

def generate_ticket_number():
    """Generate unique repair ticket number"""
    today = datetime.utcnow()
    prefix = f"REP{today.strftime('%Y%m%d')}"
    
    # Get last ticket number for today
    last_repair = Repair.query.filter(
        Repair.ticket_no.like(f"{prefix}%")
    ).order_by(desc(Repair.id)).first()
    
    if last_repair:
        # Extract sequence number and increment
        sequence = int(last_repair.ticket_no[-3:]) + 1
    else:
        sequence = 1
    
    return f"{prefix}{sequence:03d}"

@repairs_bp.route('/')
@login_required
@permission_required('repairs')
def list_repairs():
    """List all repairs with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Repair.query
    
    # Apply filters
    if search:
        query = query.filter(or_(
            Repair.ticket_no.contains(search),
            Repair.device_model.contains(search),
            Repair.problem_desc.contains(search)
        ))
    
    if status:
        query = query.filter(Repair.status == status)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Repair.entry_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Repair.entry_date <= date_to_obj)
        except ValueError:
            pass
    
    # Order by entry date (newest first)
    query = query.order_by(desc(Repair.entry_date))
    
    # Paginate
    repairs = query.paginate(page=page, per_page=20, error_out=False)
    
    # Get repair statuses for filter
    from config import Config
    repair_statuses = Config.REPAIR_STATUSES
    
    return render_template('repairs/list.html',
                         repairs=repairs,
                         repair_statuses=repair_statuses,
                         search=search,
                         status=status,
                         date_from=date_from,
                         date_to=date_to)

@repairs_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('repairs')
def add_repair():
    """Add new repair job"""
    if request.method == 'POST':
        try:
            # Create or find customer
            customer_id = None
            customer_name = request.form.get('customer_name', '').strip()
            customer_phone = request.form.get('customer_phone', '').strip()
            
            if customer_name:
                # Try to find existing customer by phone
                customer = None
                if customer_phone:
                    customer = Customer.query.filter_by(phone=customer_phone).first()
                
                if not customer:
                    # Create new customer
                    customer = Customer(
                        name=customer_name,
                        phone=customer_phone,
                        address=request.form.get('customer_address', '')
                    )
                    db.session.add(customer)
                    db.session.flush()
                
                customer_id = customer.id
            
            # Create repair record
            repair = Repair(
                ticket_no=generate_ticket_number(),
                customer_id=customer_id,
                device_model=request.form['device_model'],
                problem_desc=request.form['problem_desc'],
                status=request.form.get('status', 'قيد الفحص'),
                parts_cost=float(request.form.get('parts_cost', 0)),
                labor_cost=float(request.form.get('labor_cost', 0)),
                notes=request.form.get('notes', ''),
                user_id=get_current_user().id
            )
            
            # Calculate total cost
            repair.total_cost = repair.parts_cost + repair.labor_cost
            
            db.session.add(repair)
            db.session.commit()
            
            # Log audit
            log_audit('add_repair', f'تم إضافة تذكرة صيانة رقم: {repair.ticket_no}')
            
            flash('تم إضافة تذكرة الصيانة بنجاح', 'success')
            return redirect(url_for('repairs.view_repair', id=repair.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إضافة تذكرة الصيانة: {str(e)}', 'error')
    
    # GET request
    from config import Config
    repair_statuses = Config.REPAIR_STATUSES
    
    return render_template('repairs/form.html',
                         repair=None,
                         repair_statuses=repair_statuses)

@repairs_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('repairs')
def edit_repair(id):
    """Edit existing repair job"""
    repair = Repair.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update customer info if provided
            if repair.customer:
                repair.customer.name = request.form.get('customer_name', repair.customer.name)
                repair.customer.phone = request.form.get('customer_phone', repair.customer.phone)
                repair.customer.address = request.form.get('customer_address', repair.customer.address)
            
            # Update repair details
            repair.device_model = request.form['device_model']
            repair.problem_desc = request.form['problem_desc']
            repair.status = request.form['status']
            repair.parts_cost = float(request.form.get('parts_cost', 0))
            repair.labor_cost = float(request.form.get('labor_cost', 0))
            repair.notes = request.form.get('notes', '')
            
            # Calculate total cost
            repair.total_cost = repair.parts_cost + repair.labor_cost
            
            # Set exit date if status indicates completion
            if repair.status in ['تم الإصلاح', 'غير قابل للإصلاح', 'تم التسليم']:
                if not repair.exit_date:
                    repair.exit_date = datetime.utcnow()
            
            db.session.commit()
            
            # Log audit
            log_audit('edit_repair', f'تم تحديث تذكرة صيانة رقم: {repair.ticket_no}')
            
            flash('تم تحديث تذكرة الصيانة بنجاح', 'success')
            return redirect(url_for('repairs.view_repair', id=repair.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في تحديث تذكرة الصيانة: {str(e)}', 'error')
    
    # GET request
    from config import Config
    repair_statuses = Config.REPAIR_STATUSES
    
    return render_template('repairs/form.html',
                         repair=repair,
                         repair_statuses=repair_statuses)

@repairs_bp.route('/view/<int:id>')
@login_required
@permission_required('repairs')
def view_repair(id):
    """View repair details"""
    repair = Repair.query.get_or_404(id)
    return render_template('repairs/view.html', repair=repair)

@repairs_bp.route('/print/<int:id>')
@login_required
@permission_required('repairs')
def print_receipt(id):
    """Print repair receipt"""
    repair = Repair.query.get_or_404(id)
    return render_template('repairs/receipt.html', repair=repair)

@repairs_bp.route('/update-status/<int:id>', methods=['POST'])
@login_required
@permission_required('repairs')
def update_status(id):
    """Quick update repair status"""
    repair = Repair.query.get_or_404(id)
    
    try:
        old_status = repair.status
        new_status = request.form['status']
        
        repair.status = new_status
        
        # Set exit date if status indicates completion
        if new_status in ['تم الإصلاح', 'غير قابل للإصلاح', 'تم التسليم']:
            if not repair.exit_date:
                repair.exit_date = datetime.utcnow()
        
        db.session.commit()
        
        # Log audit
        log_audit('update_repair_status', 
                 f'تم تحديث حالة التذكرة {repair.ticket_no} من "{old_status}" إلى "{new_status}"')
        
        flash('تم تحديث حالة التذكرة بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في تحديث الحالة: {str(e)}', 'error')
    
    return redirect(url_for('repairs.list_repairs'))

@repairs_bp.route('/api/customer-search')
@login_required
def customer_search():
    """API endpoint for customer search by phone"""
    phone = request.args.get('phone', '').strip()
    
    if not phone:
        return jsonify(None)
    
    customer = Customer.query.filter_by(phone=phone).first()
    
    if customer:
        return jsonify({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'address': customer.address
        })
    
    return jsonify(None)

@repairs_bp.route('/transfers')
@login_required
@permission_required('repairs')
def list_transfers():
    """List balance transfers"""
    from models import Transfer
    
    page = request.args.get('page', 1, type=int)
    transfer_type = request.args.get('type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Transfer.query
    
    # Apply filters
    if transfer_type:
        query = query.filter(Transfer.type == transfer_type)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Transfer.date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Transfer.date <= date_to_obj)
        except ValueError:
            pass
    
    # Order by date (newest first)
    query = query.order_by(desc(Transfer.date))
    
    # Paginate
    transfers = query.paginate(page=page, per_page=20, error_out=False)
    
    # Get transfer types for filter
    from config import Config
    transfer_types = Config.TRANSFER_TYPES
    
    return render_template('repairs/transfers.html',
                         transfers=transfers,
                         transfer_types=transfer_types,
                         transfer_type=transfer_type,
                         date_from=date_from,
                         date_to=date_to)

@repairs_bp.route('/transfers/add', methods=['GET', 'POST'])
@login_required
@permission_required('repairs')
def add_transfer():
    """Add new balance transfer"""
    from models import Transfer
    
    if request.method == 'POST':
        try:
            transfer = Transfer(
                type=request.form['type'],
                amount=float(request.form['amount']),
                from_account=request.form.get('from_account', ''),
                to_account=request.form['to_account'],
                reference_id=request.form.get('reference_id', ''),
                note=request.form.get('note', ''),
                user_id=get_current_user().id
            )
            
            db.session.add(transfer)
            db.session.commit()
            
            # Log audit
            log_audit('add_transfer', f'تم إضافة تحويل رصيد: {transfer.type} - {transfer.amount}')
            
            flash('تم إضافة التحويل بنجاح', 'success')
            return redirect(url_for('repairs.list_transfers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إضافة التحويل: {str(e)}', 'error')
    
    # GET request
    from config import Config
    transfer_types = Config.TRANSFER_TYPES
    
    return render_template('repairs/transfer_form.html',
                         transfer=None,
                         transfer_types=transfer_types)
