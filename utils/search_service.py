from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_, func
from config.database import SessionLocal
from models.product import Product, Category, Supplier
from models.sales import Sale, Customer
from models.repair import Repair
from models.transfer import Transfer
from models.user import User
from utils.logger import get_logger

class SearchService:
    """Global search service for the application"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def global_search(self, query, limit=50):
        """
        Perform global search across all relevant tables
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of search results with type and data
        """
        if not query or len(query.strip()) < 2:
            return []
        
        query = query.strip()
        results = []
        
        db = SessionLocal()
        try:
            # Search products
            product_results = self._search_products(db, query, limit // 5)
            results.extend(product_results)
            
            # Search sales/invoices
            sales_results = self._search_sales(db, query, limit // 5)
            results.extend(sales_results)
            
            # Search customers
            customer_results = self._search_customers(db, query, limit // 5)
            results.extend(customer_results)
            
            # Search repairs
            repair_results = self._search_repairs(db, query, limit // 5)
            results.extend(repair_results)
            
            # Search transfers
            transfer_results = self._search_transfers(db, query, limit // 5)
            results.extend(transfer_results)
            
            # Sort results by relevance (exact matches first)
            results.sort(key=lambda x: self._calculate_relevance(x, query), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Error in global search: {str(e)}")
            return []
        finally:
            db.close()
    
    def _search_products(self, db, query, limit):
        """Search products by name, SKU, barcode, or description"""
        try:
            products = db.query(Product).filter(
                Product.active == True,
                or_(
                    Product.name_ar.contains(query),
                    Product.sku.contains(query),
                    Product.barcode.contains(query),
                    Product.description_ar.contains(query)
                )
            ).limit(limit).all()
            
            results = []
            for product in products:
                results.append({
                    'type': 'product',
                    'id': product.id,
                    'title': product.name_ar,
                    'subtitle': f"الكود: {product.sku} - الكمية: {product.quantity}",
                    'description': f"السعر: {product.sale_price:.2f} جنيه",
                    'data': product,
                    'category': product.category.name_ar if product.category else 'غير محدد',
                    'icon': '📦'
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching products: {str(e)}")
            return []
    
    def _search_sales(self, db, query, limit):
        """Search sales by invoice number, customer name, or notes"""
        try:
            sales = db.query(Sale).join(Customer, isouter=True).filter(
                or_(
                    Sale.invoice_no.contains(query),
                    Customer.name.contains(query),
                    Sale.notes.contains(query)
                )
            ).limit(limit).all()
            
            results = []
            for sale in sales:
                customer_name = sale.customer.name if sale.customer else "عميل نقدي"
                results.append({
                    'type': 'sale',
                    'id': sale.id,
                    'title': f"فاتورة {sale.invoice_no}",
                    'subtitle': f"العميل: {customer_name}",
                    'description': f"الإجمالي: {sale.total:.2f} جنيه - {sale.created_at.strftime('%Y-%m-%d')}",
                    'data': sale,
                    'date': sale.created_at,
                    'icon': '🧾'
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching sales: {str(e)}")
            return []
    
    def _search_customers(self, db, query, limit):
        """Search customers by name or phone"""
        try:
            customers = db.query(Customer).filter(
                or_(
                    Customer.name.contains(query),
                    Customer.phone.contains(query)
                )
            ).limit(limit).all()
            
            results = []
            for customer in customers:
                phone = customer.phone or "غير محدد"
                results.append({
                    'type': 'customer',
                    'id': customer.id,
                    'title': customer.name,
                    'subtitle': f"الهاتف: {phone}",
                    'description': customer.address or "لا يوجد عنوان",
                    'data': customer,
                    'icon': '👤'
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching customers: {str(e)}")
            return []
    
    def _search_repairs(self, db, query, limit):
        """Search repairs by ticket number, customer name, or device model"""
        try:
            repairs = db.query(Repair).join(Customer, isouter=True).filter(
                or_(
                    Repair.ticket_no.contains(query),
                    Customer.name.contains(query),
                    Repair.device_model.contains(query),
                    Repair.problem_desc.contains(query)
                )
            ).limit(limit).all()
            
            results = []
            for repair in repairs:
                customer_name = repair.customer.name if repair.customer else "غير محدد"
                results.append({
                    'type': 'repair',
                    'id': repair.id,
                    'title': f"صيانة {repair.ticket_no}",
                    'subtitle': f"{repair.device_model} - {customer_name}",
                    'description': f"الحالة: {repair.status} - {repair.entry_date.strftime('%Y-%m-%d')}",
                    'data': repair,
                    'status': repair.status,
                    'icon': '🔧'
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching repairs: {str(e)}")
            return []
    
    def _search_transfers(self, db, query, limit):
        """Search transfers by reference number, account, or type"""
        try:
            transfers = db.query(Transfer).filter(
                or_(
                    Transfer.reference_no.contains(query),
                    Transfer.from_account.contains(query),
                    Transfer.to_account.contains(query),
                    Transfer.transfer_type.contains(query),
                    Transfer.note.contains(query)
                )
            ).limit(limit).all()
            
            results = []
            for transfer in transfers:
                ref_no = transfer.reference_no or "غير محدد"
                results.append({
                    'type': 'transfer',
                    'id': transfer.id,
                    'title': f"{transfer.transfer_type}",
                    'subtitle': f"المرجع: {ref_no}",
                    'description': f"المبلغ: {transfer.amount:.2f} جنيه - {transfer.date.strftime('%Y-%m-%d')}",
                    'data': transfer,
                    'amount': transfer.amount,
                    'icon': '💸'
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching transfers: {str(e)}")
            return []
    
    def _calculate_relevance(self, result, query):
        """Calculate search result relevance score"""
        score = 0
        query_lower = query.lower()
        title_lower = result['title'].lower()
        subtitle_lower = result['subtitle'].lower()
        
        # Exact match in title gets highest score
        if query_lower == title_lower:
            score += 100
        elif query_lower in title_lower:
            # Match at beginning of title
            if title_lower.startswith(query_lower):
                score += 80
            else:
                score += 60
        
        # Match in subtitle
        if query_lower in subtitle_lower:
            score += 30
        
        # Match in description
        if query_lower in result['description'].lower():
            score += 10
        
        # Boost recent items (for dated items)
        if 'date' in result:
            from datetime import datetime, timedelta
            if result['date'] > datetime.now() - timedelta(days=30):
                score += 5
        
        return score
    
    def search_products_by_category(self, category_id, query=None, limit=20):
        """Search products by category with optional text filter"""
        db = SessionLocal()
        try:
            query_filter = Product.category_id == category_id
            
            if query and len(query.strip()) >= 2:
                query_filter = query_filter & or_(
                    Product.name_ar.contains(query.strip()),
                    Product.sku.contains(query.strip()),
                    Product.barcode.contains(query.strip())
                )
            
            products = db.query(Product).filter(
                Product.active == True,
                query_filter
            ).limit(limit).all()
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error searching products by category: {str(e)}")
            return []
        finally:
            db.close()
    
    def search_by_barcode(self, barcode):
        """Search product by exact barcode match"""
        if not barcode or not barcode.strip():
            return None
        
        db = SessionLocal()
        try:
            product = db.query(Product).filter(
                Product.barcode == barcode.strip(),
                Product.active == True
            ).first()
            
            return product
            
        except Exception as e:
            self.logger.error(f"Error searching by barcode: {str(e)}")
            return None
        finally:
            db.close()
    
    def search_low_stock_products(self, limit=20):
        """Search for products with low stock"""
        db = SessionLocal()
        try:
            products = db.query(Product).filter(
                Product.active == True,
                Product.quantity <= Product.min_quantity
            ).order_by(Product.quantity.asc()).limit(limit).all()
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error searching low stock products: {str(e)}")
            return []
        finally:
            db.close()
    
    def search_recent_sales(self, days=7, limit=20):
        """Search for recent sales within specified days"""
        from datetime import datetime, timedelta
        
        db = SessionLocal()
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            sales = db.query(Sale).filter(
                Sale.created_at >= since_date
            ).order_by(Sale.created_at.desc()).limit(limit).all()
            
            return sales
            
        except Exception as e:
            self.logger.error(f"Error searching recent sales: {str(e)}")
            return []
        finally:
            db.close()
    
    def quick_search_suggestions(self, query):
        """Get quick search suggestions for autocomplete"""
        if not query or len(query.strip()) < 2:
            return []
        
        query = query.strip()
        suggestions = []
        
        db = SessionLocal()
        try:
            # Product names
            products = db.query(Product.name_ar).filter(
                Product.name_ar.contains(query),
                Product.active == True
            ).distinct().limit(5).all()
            
            for product in products:
                suggestions.append({
                    'text': product.name_ar,
                    'type': 'product',
                    'icon': '📦'
                })
            
            # Customer names
            customers = db.query(Customer.name).filter(
                Customer.name.contains(query)
            ).distinct().limit(3).all()
            
            for customer in customers:
                suggestions.append({
                    'text': customer.name,
                    'type': 'customer',
                    'icon': '👤'
                })
            
            # Invoice numbers
            invoices = db.query(Sale.invoice_no).filter(
                Sale.invoice_no.contains(query)
            ).distinct().limit(3).all()
            
            for invoice in invoices:
                suggestions.append({
                    'text': invoice.invoice_no,
                    'type': 'invoice',
                    'icon': '🧾'
                })
            
            return suggestions[:10]
            
        except Exception as e:
            self.logger.error(f"Error getting search suggestions: {str(e)}")
            return []
        finally:
            db.close()
