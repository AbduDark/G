from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import json
import logging
from config import Config
from models import db, User, Role, Product, Category, Sale, SaleItem, Repair, Transfer, StockMovement
from auth import login_required, admin_required
from utils.database import init_database
from utils.pdf_generator import generate_invoice_pdf
from utils.backup import create_backup, restore_backup

# Import route blueprints
from routes.main import main_bp
from routes.inventory import inventory_bp
from routes.sales import sales_bp
from routes.repairs import repairs_bp
from routes.reports import reports_bp
from routes.users import users_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(repairs_bp, url_prefix='/repairs')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(users_bp, url_prefix='/users')
    
    @app.before_first_request
    def initialize_database():
        """Initialize database and create default admin user on first run"""
        init_database(app, db)
    
    @app.route('/')
    def index():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return redirect(url_for('main.dashboard'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            user = User.query.filter_by(email=email, active=True).first()
            
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_role'] = user.role.name
                
                # Update last login
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Log successful login
                logger.info(f"User {user.email} logged in successfully")
                
                return redirect(url_for('main.dashboard'))
            else:
                flash('بيانات تسجيل الدخول غير صحيحة', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        user_email = session.get('user_email', 'Unknown')
        session.clear()
        logger.info(f"User {user_email} logged out")
        flash('تم تسجيل الخروج بنجاح', 'success')
        return redirect(url_for('login'))
    
    @app.route('/api/search')
    @login_required
    def global_search():
        """Global search API endpoint"""
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify([])
        
        results = []
        
        # Search products
        products = Product.query.filter(
            Product.name_ar.contains(query) | 
            Product.sku.contains(query) |
            Product.barcode.contains(query)
        ).limit(5).all()
        
        for product in products:
            results.append({
                'type': 'منتج',
                'title': product.name_ar,
                'subtitle': f'SKU: {product.sku}',
                'url': url_for('inventory.edit_product', id=product.id)
            })
        
        # Search sales
        sales = Sale.query.filter(
            Sale.invoice_no.contains(query)
        ).limit(5).all()
        
        for sale in sales:
            results.append({
                'type': 'فاتورة',
                'title': f'فاتورة رقم {sale.invoice_no}',
                'subtitle': f'التاريخ: {sale.created_at.strftime("%Y-%m-%d")}',
                'url': url_for('sales.view_sale', id=sale.id)
            })
        
        # Search repairs
        repairs = Repair.query.filter(
            Repair.ticket_no.contains(query) |
            Repair.device_model.contains(query) |
            Repair.problem_desc.contains(query)
        ).limit(5).all()
        
        for repair in repairs:
            results.append({
                'type': 'صيانة',
                'title': f'تذكرة رقم {repair.ticket_no}',
                'subtitle': repair.device_model,
                'url': url_for('repairs.edit_repair', id=repair.id)
            })
        
        return jsonify(results)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
