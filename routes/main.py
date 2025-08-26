from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from models import db, Product, Sale, SaleItem, Repair, Transfer, StockMovement
from auth import login_required, get_current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with overview statistics"""
    user = get_current_user()
    
    # Today's statistics
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Sales statistics
    today_sales = Sale.query.filter(
        Sale.created_at >= today_start,
        Sale.created_at <= today_end
    ).all()
    
    today_revenue = sum(sale.total for sale in today_sales)
    today_sales_count = len(today_sales)
    
    # This month statistics
    month_start = datetime(today.year, today.month, 1)
    month_sales = Sale.query.filter(Sale.created_at >= month_start).all()
    month_revenue = sum(sale.total for sale in month_sales)
    
    # Low stock products
    low_stock_products = Product.query.filter(
        Product.quantity <= Product.min_quantity,
        Product.active == True
    ).all()
    
    # Recent repairs
    recent_repairs = Repair.query.filter(
        Repair.status.notin_(['تم التسليم', 'غير قابل للإصلاح'])
    ).order_by(desc(Repair.entry_date)).limit(5).all()
    
    # Top selling products this month
    top_products_query = db.session.query(
        Product.name_ar,
        func.sum(SaleItem.quantity).label('total_sold')
    ).join(SaleItem).join(Sale).filter(
        Sale.created_at >= month_start
    ).group_by(Product.id).order_by(desc('total_sold')).limit(5).all()
    
    # Recent transfers
    recent_transfers = Transfer.query.order_by(
        desc(Transfer.date)
    ).limit(5).all()
    
    # Chart data for last 7 days
    chart_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        day_sales = Sale.query.filter(
            Sale.created_at >= date_start,
            Sale.created_at <= date_end
        ).all()
        
        day_revenue = sum(sale.total for sale in day_sales)
        
        chart_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'date_ar': date.strftime('%d/%m'),
            'revenue': float(day_revenue),
            'sales_count': len(day_sales)
        })
    
    dashboard_data = {
        'today_revenue': today_revenue,
        'today_sales_count': today_sales_count,
        'month_revenue': month_revenue,
        'low_stock_count': len(low_stock_products),
        'low_stock_products': low_stock_products[:5],  # Show top 5
        'recent_repairs': recent_repairs,
        'top_products': top_products_query,
        'recent_transfers': recent_transfers,
        'chart_data': chart_data,
        'user': user
    }
    
    return render_template('dashboard.html', **dashboard_data)

@main_bp.route('/api/dashboard-stats')
@login_required
def dashboard_stats_api():
    """API endpoint for dashboard statistics (for AJAX updates)"""
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Today's sales
    today_sales = Sale.query.filter(
        Sale.created_at >= today_start,
        Sale.created_at <= today_end
    ).all()
    
    stats = {
        'today_revenue': float(sum(sale.total for sale in today_sales)),
        'today_sales_count': len(today_sales),
        'pending_repairs': Repair.query.filter(
            Repair.status.notin_(['تم التسليم', 'غير قابل للإصلاح'])
        ).count(),
        'low_stock_count': Product.query.filter(
            Product.quantity <= Product.min_quantity,
            Product.active == True
        ).count()
    }
    
    return jsonify(stats)
