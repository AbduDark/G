from flask import Blueprint, render_template, request, jsonify, make_response
from sqlalchemy import func, desc, extract
from models import db, Sale, SaleItem, Product, Category, Repair, Transfer, StockMovement
from auth import login_required, permission_required
from datetime import datetime, timedelta
import json
from io import StringIO
import csv

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@reports_bp.route('/dashboard')
@login_required
@permission_required('reports')
def dashboard():
    """Reports dashboard with overview charts"""
    # Default to current month
    today = datetime.utcnow().date()
    month_start = datetime(today.year, today.month, 1)
    
    # Sales statistics
    sales_stats = get_sales_statistics(month_start, datetime.utcnow())
    
    # Top selling products
    top_products = get_top_selling_products(month_start, datetime.utcnow(), limit=10)
    
    # Category sales distribution
    category_sales = get_category_sales_distribution(month_start, datetime.utcnow())
    
    # Daily sales chart for last 30 days
    daily_sales = get_daily_sales_chart(30)
    
    # Low stock products
    low_stock = Product.query.filter(
        Product.quantity <= Product.min_quantity,
        Product.active == True
    ).limit(10).all()
    
    # Recent repairs summary
    repairs_summary = get_repairs_summary(month_start, datetime.utcnow())
    
    return render_template('reports/dashboard.html',
                         sales_stats=sales_stats,
                         top_products=top_products,
                         category_sales=category_sales,
                         daily_sales=daily_sales,
                         low_stock=low_stock,
                         repairs_summary=repairs_summary)

@reports_bp.route('/sales')
@login_required
@permission_required('reports')
def sales_report():
    """Detailed sales report"""
    # Get filter parameters
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    category_id = request.args.get('category', 0, type=int)
    user_id = request.args.get('user_id', 0, type=int)
    
    # Set default date range if not provided
    if not date_from:
        date_from = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Parse dates
    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    
    # Build query
    query = db.session.query(
        Sale.invoice_no,
        Sale.created_at,
        Sale.total,
        Sale.tax,
        Sale.discount,
        func.count(SaleItem.id).label('items_count'),
        func.sum(SaleItem.quantity).label('total_quantity')
    ).join(SaleItem).filter(
        Sale.created_at >= date_from_obj,
        Sale.created_at <= date_to_obj
    )
    
    # Apply additional filters
    if user_id:
        query = query.filter(Sale.user_id == user_id)
    
    if category_id:
        query = query.join(Product).filter(Product.category_id == category_id)
    
    # Group and order
    query = query.group_by(Sale.id).order_by(desc(Sale.created_at))
    
    sales_data = query.all()
    
    # Calculate summary statistics
    total_sales = sum(sale.total for sale in sales_data)
    total_tax = sum(sale.tax for sale in sales_data)
    total_discount = sum(sale.discount for sale in sales_data)
    total_items = sum(sale.total_quantity for sale in sales_data)
    
    summary = {
        'total_sales': total_sales,
        'total_tax': total_tax,
        'total_discount': total_discount,
        'total_items': total_items,
        'average_sale': total_sales / len(sales_data) if sales_data else 0,
        'sales_count': len(sales_data)
    }
    
    # Get categories for filter
    categories = Category.query.order_by(Category.name_ar).all()
    
    # Get users for filter
    from models import User
    users = User.query.filter(User.active == True).order_by(User.name).all()
    
    return render_template('reports/sales.html',
                         sales_data=sales_data,
                         summary=summary,
                         categories=categories,
                         users=users,
                         date_from=date_from,
                         date_to=date_to,
                         category_id=category_id,
                         user_id=user_id)

@reports_bp.route('/inventory')
@login_required
@permission_required('reports')
def inventory_report():
    """Inventory status report"""
    # Get filter parameters
    category_id = request.args.get('category', 0, type=int)
    stock_status = request.args.get('stock_status', '')  # low, out, normal
    
    query = Product.query.filter(Product.active == True)
    
    # Apply filters
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if stock_status == 'low':
        query = query.filter(Product.quantity <= Product.min_quantity)
    elif stock_status == 'out':
        query = query.filter(Product.quantity == 0)
    elif stock_status == 'normal':
        query = query.filter(Product.quantity > Product.min_quantity)
    
    products = query.order_by(Product.name_ar).all()
    
    # Calculate summary
    total_products = len(products)
    total_value = sum(p.quantity * p.sale_price for p in products)
    low_stock_count = sum(1 for p in products if p.is_low_stock)
    out_of_stock_count = sum(1 for p in products if p.quantity == 0)
    
    summary = {
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count
    }
    
    # Get categories for filter
    categories = Category.query.order_by(Category.name_ar).all()
    
    return render_template('reports/inventory.html',
                         products=products,
                         summary=summary,
                         categories=categories,
                         category_id=category_id,
                         stock_status=stock_status)

@reports_bp.route('/repairs')
@login_required
@permission_required('reports')
def repairs_report():
    """Repairs summary report"""
    # Get filter parameters
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    status = request.args.get('status', '')
    
    # Set default date range if not provided
    if not date_from:
        date_from = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Parse dates
    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    
    query = Repair.query.filter(
        Repair.entry_date >= date_from_obj,
        Repair.entry_date <= date_to_obj
    )
    
    if status:
        query = query.filter(Repair.status == status)
    
    repairs = query.order_by(desc(Repair.entry_date)).all()
    
    # Calculate summary
    total_repairs = len(repairs)
    completed_repairs = sum(1 for r in repairs if r.is_completed)
    total_revenue = sum(r.total_cost for r in repairs if r.is_completed)
    avg_completion_time = 0
    
    if completed_repairs > 0:
        completion_times = []
        for repair in repairs:
            if repair.is_completed and repair.exit_date:
                delta = repair.exit_date - repair.entry_date
                completion_times.append(delta.days)
        
        if completion_times:
            avg_completion_time = sum(completion_times) / len(completion_times)
    
    summary = {
        'total_repairs': total_repairs,
        'completed_repairs': completed_repairs,
        'pending_repairs': total_repairs - completed_repairs,
        'total_revenue': total_revenue,
        'avg_completion_time': avg_completion_time
    }
    
    # Status distribution
    status_distribution = db.session.query(
        Repair.status,
        func.count(Repair.id).label('count')
    ).filter(
        Repair.entry_date >= date_from_obj,
        Repair.entry_date <= date_to_obj
    ).group_by(Repair.status).all()
    
    # Get repair statuses for filter
    from config import Config
    repair_statuses = Config.REPAIR_STATUSES
    
    return render_template('reports/repairs.html',
                         repairs=repairs,
                         summary=summary,
                         status_distribution=status_distribution,
                         repair_statuses=repair_statuses,
                         date_from=date_from,
                         date_to=date_to,
                         status=status)

@reports_bp.route('/transfers')
@login_required
@permission_required('reports')
def transfers_report():
    """Balance transfers report"""
    # Get filter parameters
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    transfer_type = request.args.get('type', '')
    
    # Set default date range if not provided
    if not date_from:
        date_from = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Parse dates
    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    
    query = Transfer.query.filter(
        Transfer.date >= date_from_obj,
        Transfer.date <= date_to_obj
    )
    
    if transfer_type:
        query = query.filter(Transfer.type == transfer_type)
    
    transfers = query.order_by(desc(Transfer.date)).all()
    
    # Calculate summary
    total_amount = sum(t.amount for t in transfers)
    total_count = len(transfers)
    
    # Type distribution
    type_distribution = db.session.query(
        Transfer.type,
        func.count(Transfer.id).label('count'),
        func.sum(Transfer.amount).label('total_amount')
    ).filter(
        Transfer.date >= date_from_obj,
        Transfer.date <= date_to_obj
    ).group_by(Transfer.type).all()
    
    summary = {
        'total_amount': total_amount,
        'total_count': total_count,
        'average_amount': total_amount / total_count if total_count > 0 else 0
    }
    
    # Get transfer types for filter
    from config import Config
    transfer_types = Config.TRANSFER_TYPES
    
    return render_template('reports/transfers.html',
                         transfers=transfers,
                         summary=summary,
                         type_distribution=type_distribution,
                         transfer_types=transfer_types,
                         date_from=date_from,
                         date_to=date_to,
                         transfer_type=transfer_type)

@reports_bp.route('/export/csv/<report_type>')
@login_required
@permission_required('reports')
def export_csv(report_type):
    """Export report data to CSV"""
    # Get filter parameters from query string
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    if report_type == 'sales':
        data = get_sales_export_data(date_from, date_to)
        filename = f'sales_report_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    elif report_type == 'inventory':
        data = get_inventory_export_data()
        filename = f'inventory_report_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    elif report_type == 'repairs':
        data = get_repairs_export_data(date_from, date_to)
        filename = f'repairs_report_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    else:
        flash('نوع تقرير غير صحيح', 'error')
        return redirect(url_for('reports.dashboard'))
    
    # Create CSV content
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data['headers'])
    writer.writeheader()
    writer.writerows(data['rows'])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

# Helper functions for statistics and data processing

def get_sales_statistics(date_from, date_to):
    """Get sales statistics for date range"""
    sales = Sale.query.filter(
        Sale.created_at >= date_from,
        Sale.created_at <= date_to
    ).all()
    
    total_revenue = sum(sale.total for sale in sales)
    total_cost = 0
    
    # Calculate total cost from sale items
    for sale in sales:
        for item in sale.sale_items:
            total_cost += item.product.cost_price * item.quantity
    
    profit = total_revenue - total_cost
    
    return {
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'profit': profit,
        'profit_margin': (profit / total_revenue * 100) if total_revenue > 0 else 0,
        'sales_count': len(sales)
    }

def get_top_selling_products(date_from, date_to, limit=10):
    """Get top selling products for date range"""
    return db.session.query(
        Product.name_ar,
        func.sum(SaleItem.quantity).label('total_sold'),
        func.sum(SaleItem.line_total).label('total_revenue')
    ).join(SaleItem).join(Sale).filter(
        Sale.created_at >= date_from,
        Sale.created_at <= date_to
    ).group_by(Product.id).order_by(desc('total_sold')).limit(limit).all()

def get_category_sales_distribution(date_from, date_to):
    """Get sales distribution by category"""
    return db.session.query(
        Category.name_ar,
        func.sum(SaleItem.line_total).label('total_revenue'),
        func.sum(SaleItem.quantity).label('total_quantity')
    ).join(Product).join(SaleItem).join(Sale).filter(
        Sale.created_at >= date_from,
        Sale.created_at <= date_to
    ).group_by(Category.id).all()

def get_daily_sales_chart(days=30):
    """Get daily sales data for chart"""
    today = datetime.utcnow().date()
    chart_data = []
    
    for i in range(days, 0, -1):
        date = today - timedelta(days=i)
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        day_sales = Sale.query.filter(
            Sale.created_at >= date_start,
            Sale.created_at <= date_end
        ).all()
        
        revenue = sum(sale.total for sale in day_sales)
        
        chart_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'date_ar': date.strftime('%d/%m'),
            'revenue': float(revenue),
            'sales_count': len(day_sales)
        })
    
    return chart_data

def get_repairs_summary(date_from, date_to):
    """Get repairs summary statistics"""
    repairs = Repair.query.filter(
        Repair.entry_date >= date_from,
        Repair.entry_date <= date_to
    ).all()
    
    completed = sum(1 for r in repairs if r.is_completed)
    total_revenue = sum(r.total_cost for r in repairs if r.is_completed)
    
    return {
        'total_repairs': len(repairs),
        'completed_repairs': completed,
        'pending_repairs': len(repairs) - completed,
        'total_revenue': total_revenue
    }

def get_sales_export_data(date_from, date_to):
    """Get sales data for CSV export"""
    # Parse dates if provided
    query = Sale.query
    if date_from and date_to:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        query = query.filter(Sale.created_at >= date_from_obj, Sale.created_at <= date_to_obj)
    
    sales = query.order_by(desc(Sale.created_at)).all()
    
    headers = ['رقم الفاتورة', 'التاريخ', 'العميل', 'المجموع', 'الضريبة', 'الخصم', 'المبلغ المدفوع', 'الباقي']
    rows = []
    
    for sale in sales:
        rows.append({
            'رقم الفاتورة': sale.invoice_no,
            'التاريخ': sale.created_at.strftime('%Y-%m-%d %H:%M'),
            'العميل': sale.customer.name if sale.customer else '',
            'المجموع': float(sale.total),
            'الضريبة': float(sale.tax),
            'الخصم': float(sale.discount),
            'المبلغ المدفوع': float(sale.paid),
            'الباقي': float(sale.change)
        })
    
    return {'headers': headers, 'rows': rows}

def get_inventory_export_data():
    """Get inventory data for CSV export"""
    products = Product.query.filter(Product.active == True).order_by(Product.name_ar).all()
    
    headers = ['كود المنتج', 'اسم المنتج', 'الفئة', 'الكمية', 'الحد الأدنى', 'سعر الشراء', 'سعر البيع', 'الربحية']
    rows = []
    
    for product in products:
        rows.append({
            'كود المنتج': product.sku,
            'اسم المنتج': product.name_ar,
            'الفئة': product.category.name_ar,
            'الكمية': product.quantity,
            'الحد الأدنى': product.min_quantity,
            'سعر الشراء': float(product.cost_price),
            'سعر البيع': float(product.sale_price),
            'الربحية': f"{product.profit_margin:.2f}%"
        })
    
    return {'headers': headers, 'rows': rows}

def get_repairs_export_data(date_from, date_to):
    """Get repairs data for CSV export"""
    query = Repair.query
    if date_from and date_to:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        query = query.filter(Repair.entry_date >= date_from_obj, Repair.entry_date <= date_to_obj)
    
    repairs = query.order_by(desc(Repair.entry_date)).all()
    
    headers = ['رقم التذكرة', 'العميل', 'الجهاز', 'المشكلة', 'الحالة', 'تاريخ الدخول', 'تاريخ الخروج', 'التكلفة الإجمالية']
    rows = []
    
    for repair in repairs:
        rows.append({
            'رقم التذكرة': repair.ticket_no,
            'العميل': repair.customer.name if repair.customer else '',
            'الجهاز': repair.device_model,
            'المشكلة': repair.problem_desc,
            'الحالة': repair.status,
            'تاريخ الدخول': repair.entry_date.strftime('%Y-%m-%d'),
            'تاريخ الخروج': repair.exit_date.strftime('%Y-%m-%d') if repair.exit_date else '',
            'التكلفة الإجمالية': float(repair.total_cost)
        })
    
    return {'headers': headers, 'rows': rows}
