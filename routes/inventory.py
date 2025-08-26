from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import or_, desc
from models import db, Product, Category, Supplier, StockMovement
from auth import login_required, permission_required, get_current_user, log_audit
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
@login_required
@permission_required('inventory')
def list_products():
    """List all products with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', 0, type=int)
    low_stock_only = request.args.get('low_stock', False, type=bool)
    
    query = Product.query.filter(Product.active == True)
    
    # Apply filters
    if search:
        query = query.filter(or_(
            Product.name_ar.contains(search),
            Product.sku.contains(search),
            Product.barcode.contains(search)
        ))
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if low_stock_only:
        query = query.filter(Product.quantity <= Product.min_quantity)
    
    # Order by name
    query = query.order_by(Product.name_ar)
    
    # Paginate
    products = query.paginate(page=page, per_page=20, error_out=False)
    
    # Get categories for filter dropdown
    categories = Category.query.order_by(Category.name_ar).all()
    
    return render_template('inventory/list.html',
                         products=products,
                         categories=categories,
                         search=search,
                         category_id=category_id,
                         low_stock_only=low_stock_only)

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('inventory')
def add_product():
    """Add new product"""
    if request.method == 'POST':
        try:
            product = Product(
                sku=request.form['sku'],
                name_ar=request.form['name_ar'],
                description_ar=request.form.get('description_ar', ''),
                category_id=request.form['category_id'],
                cost_price=float(request.form['cost_price']),
                sale_price=float(request.form['sale_price']),
                quantity=int(request.form['quantity']),
                min_quantity=int(request.form['min_quantity']),
                barcode=request.form.get('barcode', ''),
                supplier_id=request.form.get('supplier_id') or None
            )
            
            db.session.add(product)
            db.session.flush()  # Get the product ID
            
            # Create initial stock movement
            if product.quantity > 0:
                stock_movement = StockMovement(
                    product_id=product.id,
                    change_qty=product.quantity,
                    type='adjustment',
                    user_id=get_current_user().id,
                    note='رصيد ابتدائي'
                )
                db.session.add(stock_movement)
            
            db.session.commit()
            
            # Log audit
            log_audit('add_product', f'تم إضافة المنتج: {product.name_ar}')
            
            flash('تم إضافة المنتج بنجاح', 'success')
            return redirect(url_for('inventory.list_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إضافة المنتج: {str(e)}', 'error')
    
    # GET request
    categories = Category.query.order_by(Category.name_ar).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()
    
    return render_template('inventory/form.html',
                         categories=categories,
                         suppliers=suppliers,
                         product=None)

@inventory_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('inventory')
def edit_product(id):
    """Edit existing product"""
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            old_quantity = product.quantity
            
            # Update product details
            product.sku = request.form['sku']
            product.name_ar = request.form['name_ar']
            product.description_ar = request.form.get('description_ar', '')
            product.category_id = request.form['category_id']
            product.cost_price = float(request.form['cost_price'])
            product.sale_price = float(request.form['sale_price'])
            new_quantity = int(request.form['quantity'])
            product.min_quantity = int(request.form['min_quantity'])
            product.barcode = request.form.get('barcode', '')
            product.supplier_id = request.form.get('supplier_id') or None
            
            # Handle quantity change
            if new_quantity != old_quantity:
                product.quantity = new_quantity
                change_qty = new_quantity - old_quantity
                
                # Create stock movement for quantity adjustment
                stock_movement = StockMovement(
                    product_id=product.id,
                    change_qty=change_qty,
                    type='adjustment',
                    user_id=get_current_user().id,
                    note=f'تعديل كمية: من {old_quantity} إلى {new_quantity}'
                )
                db.session.add(stock_movement)
            
            db.session.commit()
            
            # Log audit
            log_audit('edit_product', f'تم تعديل المنتج: {product.name_ar}')
            
            flash('تم تحديث المنتج بنجاح', 'success')
            return redirect(url_for('inventory.list_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في تحديث المنتج: {str(e)}', 'error')
    
    # GET request
    categories = Category.query.order_by(Category.name_ar).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()
    
    return render_template('inventory/form.html',
                         categories=categories,
                         suppliers=suppliers,
                         product=product)

@inventory_bp.route('/delete/<int:id>')
@login_required
@permission_required('inventory')
def delete_product(id):
    """Soft delete product"""
    product = Product.query.get_or_404(id)
    
    try:
        product.active = False
        db.session.commit()
        
        # Log audit
        log_audit('delete_product', f'تم حذف المنتج: {product.name_ar}')
        
        flash('تم حذف المنتج بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في حذف المنتج: {str(e)}', 'error')
    
    return redirect(url_for('inventory.list_products'))

@inventory_bp.route('/stock-movements/<int:product_id>')
@login_required
@permission_required('inventory')
def stock_movements(product_id):
    """View stock movements for a product"""
    product = Product.query.get_or_404(product_id)
    
    movements = StockMovement.query.filter_by(product_id=product_id)\
        .order_by(desc(StockMovement.date)).all()
    
    return render_template('inventory/stock_movements.html',
                         product=product,
                         movements=movements)

@inventory_bp.route('/categories')
@login_required
@permission_required('inventory')
def categories():
    """Manage product categories"""
    categories = Category.query.order_by(Category.name_ar).all()
    return render_template('inventory/categories.html', categories=categories)

@inventory_bp.route('/categories/add', methods=['POST'])
@login_required
@permission_required('inventory')
def add_category():
    """Add new category"""
    try:
        category = Category(name_ar=request.form['name_ar'])
        db.session.add(category)
        db.session.commit()
        
        log_audit('add_category', f'تم إضافة فئة جديدة: {category.name_ar}')
        
        flash('تم إضافة الفئة بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في إضافة الفئة: {str(e)}', 'error')
    
    return redirect(url_for('inventory.categories'))

@inventory_bp.route('/api/search-products')
@login_required
def search_products():
    """API endpoint for product search (used in sales forms)"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    products = Product.query.filter(
        Product.active == True,
        or_(
            Product.name_ar.contains(query),
            Product.sku.contains(query),
            Product.barcode.contains(query)
        )
    ).limit(10).all()
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'sku': product.sku,
            'name_ar': product.name_ar,
            'sale_price': float(product.sale_price),
            'quantity': product.quantity,
            'category': product.category.name_ar
        })
    
    return jsonify(results)
