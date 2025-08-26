from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from config.database import SessionLocal
from models.sales import Sale, SaleItem
from models.product import Product
from models.repair import Repair
from models.transfer import Transfer
from utils.logger import get_logger

class ReportService:
    """Service for generating reports and analytics"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def get_today_sales_total(self):
        """Get today's total sales"""
        db = SessionLocal()
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            result = db.query(func.sum(Sale.total)).filter(
                Sale.created_at >= today,
                Sale.created_at < tomorrow
            ).scalar()
            
            return result or 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating today's sales: {str(e)}")
            return 0.0
        finally:
            db.close()
    
    def get_low_stock_count(self):
        """Get count of products with low stock"""
        db = SessionLocal()
        try:
            return db.query(Product).filter(
                Product.quantity <= Product.min_quantity,
                Product.active == True
            ).count()
        except Exception as e:
            self.logger.error(f"Error counting low stock: {str(e)}")
            return 0
        finally:
            db.close()
    
    def get_pending_repairs_count(self):
        """Get count of pending repairs"""
        db = SessionLocal()
        try:
            return db.query(Repair).filter(
                Repair.status.in_(["قيد الفحص", "قيد الانتظار"])
            ).count()
        except Exception as e:
            self.logger.error(f"Error counting pending repairs: {str(e)}")
            return 0
        finally:
            db.close()
    
    def get_total_products_count(self):
        """Get total products count"""
        db = SessionLocal()
        try:
            return db.query(Product).filter(Product.active == True).count()
        except Exception as e:
            self.logger.error(f"Error counting products: {str(e)}")
            return 0
        finally:
            db.close()
    
    def get_sales_report(self, start_date, end_date):
        """Get sales report for date range"""
        db = SessionLocal()
        try:
            sales = db.query(Sale).filter(
                Sale.created_at >= start_date,
                Sale.created_at <= end_date
            ).all()
            
            total_sales = sum(sale.total for sale in sales)
            total_transactions = len(sales)
            average_transaction = total_sales / total_transactions if total_transactions > 0 else 0
            
            return {
                'sales': sales,
                'total_sales': total_sales,
                'total_transactions': total_transactions,
                'average_transaction': average_transaction
            }
            
        except Exception as e:
            self.logger.error(f"Error generating sales report: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_profit_report(self, start_date, end_date):
        """Get profit/loss report"""
        db = SessionLocal()
        try:
            # Get sales items with product cost
            sales_items = db.query(SaleItem, Product).join(Product).filter(
                SaleItem.sale.has(Sale.created_at.between(start_date, end_date))
            ).all()
            
            total_revenue = 0
            total_cost = 0
            
            for sale_item, product in sales_items:
                revenue = sale_item.line_total
                cost = product.cost_price * sale_item.quantity
                
                total_revenue += revenue
                total_cost += cost
            
            profit = total_revenue - total_cost
            margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
            
            return {
                'total_revenue': total_revenue,
                'total_cost': total_cost,
                'profit': profit,
                'margin': margin
            }
            
        except Exception as e:
            self.logger.error(f"Error generating profit report: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_top_selling_products(self, limit=10, start_date=None, end_date=None):
        """Get top selling products"""
        db = SessionLocal()
        try:
            query = db.query(
                Product.name_ar,
                func.sum(SaleItem.quantity).label('total_sold'),
                func.sum(SaleItem.line_total).label('total_revenue')
            ).join(SaleItem).join(Sale)
            
            if start_date and end_date:
                query = query.filter(Sale.created_at.between(start_date, end_date))
            
            products = query.group_by(Product.id).order_by(
                func.sum(SaleItem.quantity).desc()
            ).limit(limit).all()
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error getting top selling products: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_daily_sales_chart_data(self, days=30):
        """Get daily sales data for chart"""
        db = SessionLocal()
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            sales_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                daily_total = db.query(func.sum(Sale.total)).filter(
                    Sale.created_at >= current_date,
                    Sale.created_at < next_date
                ).scalar() or 0
                
                sales_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'total': float(daily_total)
                })
                
                current_date = next_date
            
            return sales_data
            
        except Exception as e:
            self.logger.error(f"Error getting daily sales data: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_inventory_report(self):
        """Get inventory status report"""
        db = SessionLocal()
        try:
            products = db.query(Product).filter(Product.active == True).all()
            
            total_products = len(products)
            low_stock = sum(1 for p in products if p.quantity <= p.min_quantity)
            out_of_stock = sum(1 for p in products if p.quantity <= 0)
            total_value = sum(p.cost_price * p.quantity for p in products)
            
            return {
                'total_products': total_products,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock,
                'total_value': total_value,
                'products': products
            }
            
        except Exception as e:
            self.logger.error(f"Error generating inventory report: {str(e)}")
            raise e
        finally:
            db.close()
