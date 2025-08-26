from datetime import datetime
from sqlalchemy.orm import sessionmaker
from config.database import SessionLocal
from models.sales import Sale, SaleItem, Customer
from models.product import Product
from services.inventory_service import InventoryService
from utils.logger import get_logger

class SalesService:
    """Service for sales management operations"""
    
    def __init__(self):
        self.inventory_service = InventoryService()
        self.logger = get_logger(__name__)
    
    def create_sale(self, sale_data, user_id):
        """Create new sale transaction"""
        db = SessionLocal()
        try:
            # Generate invoice number
            invoice_no = self.generate_invoice_number()
            
            # Create sale record
            sale = Sale(
                invoice_no=invoice_no,
                customer_id=sale_data.get('customer_id'),
                subtotal=sale_data['subtotal'],
                tax=sale_data.get('tax', 0),
                discount=sale_data.get('discount', 0),
                total=sale_data['total'],
                paid=sale_data['paid'],
                change=sale_data.get('change', 0),
                user_id=user_id,
                notes=sale_data.get('notes')
            )
            db.add(sale)
            db.flush()  # Get sale ID
            
            # Create sale items and update stock
            for item_data in sale_data['items']:
                # Verify product availability
                product = db.query(Product).filter(Product.id == item_data['product_id']).first()
                if not product:
                    raise ValueError(f"المنتج غير موجود")
                
                if product.quantity < item_data['quantity']:
                    raise ValueError(f"كمية غير كافية للمنتج: {product.name_ar}")
                
                # Create sale item
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=item_data['product_id'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    line_total=item_data['line_total']
                )
                db.add(sale_item)
                
                # Update product stock
                product.quantity -= item_data['quantity']
                
                # Create stock movement
                self.inventory_service.create_stock_movement({
                    'product_id': item_data['product_id'],
                    'change_qty': -item_data['quantity'],
                    'movement_type': 'sale',
                    'reference_id': invoice_no,
                    'user_id': user_id,
                    'note': f'بيع - فاتورة رقم {invoice_no}'
                })
            
            db.commit()
            self.logger.info(f"Created sale: {invoice_no}")
            return sale
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating sale: {str(e)}")
            raise e
        finally:
            db.close()
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        db = SessionLocal()
        try:
            # Get today's date
            today = datetime.now().strftime("%Y%m%d")
            
            # Count today's sales
            count = db.query(Sale).filter(
                Sale.invoice_no.like(f"{today}-%")
            ).count()
            
            return f"{today}-{count + 1:04d}"
            
        except Exception as e:
            self.logger.error(f"Error generating invoice number: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_sales(self, start_date=None, end_date=None, customer_id=None):
        """Get sales with optional filters"""
        db = SessionLocal()
        try:
            query = db.query(Sale)
            
            if start_date:
                query = query.filter(Sale.created_at >= start_date)
            if end_date:
                query = query.filter(Sale.created_at <= end_date)
            if customer_id:
                query = query.filter(Sale.customer_id == customer_id)
            
            return query.order_by(Sale.created_at.desc()).all()
            
        except Exception as e:
            self.logger.error(f"Error fetching sales: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_sale_by_id(self, sale_id):
        """Get sale by ID with items"""
        db = SessionLocal()
        try:
            return db.query(Sale).filter(Sale.id == sale_id).first()
        except Exception as e:
            self.logger.error(f"Error fetching sale {sale_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_sale_by_invoice(self, invoice_no):
        """Get sale by invoice number"""
        db = SessionLocal()
        try:
            return db.query(Sale).filter(Sale.invoice_no == invoice_no).first()
        except Exception as e:
            self.logger.error(f"Error fetching sale by invoice {invoice_no}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_customers(self):
        """Get all customers"""
        db = SessionLocal()
        try:
            return db.query(Customer).all()
        except Exception as e:
            self.logger.error(f"Error fetching customers: {str(e)}")
            raise e
        finally:
            db.close()
    
    def create_customer(self, customer_data):
        """Create new customer"""
        db = SessionLocal()
        try:
            customer = Customer(**customer_data)
            db.add(customer)
            db.commit()
            self.logger.info(f"Created customer: {customer.name}")
            return customer
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating customer: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_today_sales_total(self):
        """Get today's total sales amount"""
        db = SessionLocal()
        try:
            today = datetime.now().date()
            result = db.query(Sale).filter(
                Sale.created_at >= today,
                Sale.created_at < today + timedelta(days=1)
            ).all()
            
            return sum(sale.total for sale in result)
            
        except Exception as e:
            self.logger.error(f"Error calculating today's sales: {str(e)}")
            return 0
        finally:
            db.close()
