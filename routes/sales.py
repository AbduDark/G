from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from sqlalchemy import desc, func
from models import db, Sale, SaleItem, Product, Customer, StockMovement
from auth import login_required, permission_required, get_current_user, log_audit
from utils.pdf_generator import generate_invoice_pdf
from datetime import datetime, timedelta
import json

sales_bp = Blueprint('sales', __name__)

def generate_invoice_number():
    """Generate unique invoice number"""
    today = datetime.utcnow()
    prefix = f"INV{today.strftime('%Y%m%d')}"
    
    # Get last invoice number for today
    last_sale = Sale.query.filter(
        Sale.invoice_no.like(f"{prefix}%")
    ).order_by(desc(Sale.id)).first()
    
    if last_sale:
        # Extract sequence number and increment
        sequence = int(last_sale.invoice_no[-3:]) + 1
    else:
        sequence = 1
    
    return f"{prefix}{sequence:03d}"

@sales_bp.route('/')
@login_required
@permission_required('sales')
def list_sales():
    """List all sales with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Sale.query
    
    # Apply filters
    if search:
        query = query.filter(Sale.invoice_no.contains(search))
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Sale.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Sale.created_at <= date_to_obj)
        except ValueError:
            pass
    
    # Order by creation date (newest first)
    query = query.order_by(desc(Sale.created_at))
    
    # Paginate
    sales = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('sales/list.html',
                         sales=sales,
                         search=search,
                         date_from=date_from,
                         date_to=date_to)

@sales_bp.route('/new', methods=['GET', 'POST'])
@login_required
@permission_required('sales')
def new_sale():
    """Create new sale"""
    if request.method == 'POST':
        try:
            # Parse sale data from form
            sale_data = json.loads(request.form['sale_data'])
            
            # Create customer if provided
            customer_id = None
            if sale_data.get('customer_name'):
                customer = Customer(
                    name=sale_data['customer_name'],
                    phone=sale_data.get('customer_phone', ''),
                    address=sale_data.get('customer_address', '')
                )
                db.session.add(customer)
                db.session.flush()
                customer_id = customer.id
            
            # Create sale
            sale = Sale(
                invoice_no=generate_invoice_number(),
                customer_id=customer_id,
                total=float(sale_data['total']),
                tax=float(sale_data.get('tax', 0)),
                discount=float(sale_data.get('discount', 0)),
                paid=float(sale_data['paid']),
                change=float(sale_data.get('change', 0)),
                user_id=get_current_user().id,
                notes=sale_data.get('notes', '')
            )
            
            db.session.add(sale)
            db.session.flush()
            
            # Add sale items and update stock
            for item_data in sale_data['items']:
                product = Product.query.get(item_data['product_id'])
                if not product:
                    raise Exception(f'المنتج غير موجود: {item_data["product_id"]}')
                
                if product.quantity < int(item_data['quantity']):
                    raise Exception(f'كمية غير كافية من المنتج: {product.name_ar}')
                
                # Create sale item
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=int(item_data['quantity']),
                    unit_price=float(item_data['unit_price']),
                    line_total=float(item_data['line_total'])
                )
                db.session.add(sale_item)
                
                # Update product stock
                product.quantity -= int(item_data['quantity'])
                
                # Create stock movement
                stock_movement = StockMovement(
                    product_id=product.id,
                    change_qty=-int(item_data['quantity']),
                    type='sale',
                    reference_id=sale.id,
                    user_id=get_current_user().id,
                    note=f'بيع فاتورة رقم {sale.invoice_no}'
                )
                db.session.add(stock_movement)
            
            db.session.commit()
            
            # Log audit
            log_audit('create_sale', f'تم إنشاء فاتورة بيع رقم: {sale.invoice_no}')
            
            flash('تم إنشاء الفاتورة بنجاح', 'success')
            return redirect(url_for('sales.view_sale', id=sale.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إنشاء الفاتورة: {str(e)}', 'error')
    
    # GET request
    return render_template('sales/form.html', sale=None)

@sales_bp.route('/view/<int:id>')
@login_required
@permission_required('sales')
def view_sale(id):
    """View sale details"""
    sale = Sale.query.get_or_404(id)
    return render_template('sales/view.html', sale=sale)

@sales_bp.route('/print/<int:id>')
@login_required
@permission_required('sales')
def print_sale(id):
    """Print sale invoice"""
    sale = Sale.query.get_or_404(id)
    
    # Generate PDF
    pdf_content = generate_invoice_pdf(sale)
    
    response = make_response(pdf_content)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=invoice_{sale.invoice_no}.pdf'
    
    return response

@sales_bp.route('/invoice/<int:id>')
@login_required
@permission_required('sales')
def invoice_template(id):
    """HTML invoice template for printing"""
    sale = Sale.query.get_or_404(id)
    return render_template('sales/invoice.html', sale=sale)

@sales_bp.route('/returns')
@login_required
@permission_required('sales')
def list_returns():
    """List all returns"""
    from models import Return
    
    page = request.args.get('page', 1, type=int)
    returns = Return.query.order_by(desc(Return.date))\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('sales/returns.html', returns=returns)

@sales_bp.route('/return/<int:sale_id>', methods=['GET', 'POST'])
@login_required
@permission_required('sales')
def process_return(sale_id):
    """Process product return"""
    from models import Return
    
    sale = Sale.query.get_or_404(sale_id)
    
    if request.method == 'POST':
        try:
            # Parse return data
            return_data = json.loads(request.form['return_data'])
            
            for item_data in return_data['items']:
                product = Product.query.get(item_data['product_id'])
                return_qty = int(item_data['quantity'])
                refund_amount = float(item_data['refund_amount'])
                
                # Create return record
                return_record = Return(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=return_qty,
                    reason=item_data.get('reason', ''),
                    refund_amount=refund_amount,
                    user_id=get_current_user().id
                )
                db.session.add(return_record)
                
                # Update product stock
                product.quantity += return_qty
                
                # Create stock movement
                stock_movement = StockMovement(
                    product_id=product.id,
                    change_qty=return_qty,
                    type='return',
                    reference_id=sale.id,
                    user_id=get_current_user().id,
                    note=f'مرتجع من فاتورة رقم {sale.invoice_no}'
                )
                db.session.add(stock_movement)
            
            db.session.commit()
            
            # Log audit
            log_audit('process_return', f'تم معالجة مرتجع للفاتورة: {sale.invoice_no}')
            
            flash('تم معالجة المرتجع بنجاح', 'success')
            return redirect(url_for('sales.list_returns'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في معالجة المرتجع: {str(e)}', 'error')
    
    return render_template('sales/return_form.html', sale=sale)

@sales_bp.route('/api/calculate-total', methods=['POST'])
@login_required
def calculate_total():
    """API endpoint to calculate sale total"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        discount = float(data.get('discount', 0))
        tax_rate = float(data.get('tax_rate', 0))
        
        subtotal = sum(float(item['quantity']) * float(item['unit_price']) for item in items)
        discount_amount = discount
        if discount <= 1:  # Percentage discount
            discount_amount = subtotal * discount
        
        taxable_amount = subtotal - discount_amount
        tax_amount = taxable_amount * tax_rate
        total = taxable_amount + tax_amount
        
        return jsonify({
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'tax_amount': tax_amount,
            'total': total
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
