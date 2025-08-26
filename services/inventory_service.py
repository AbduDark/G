from sqlalchemy.orm import sessionmaker
from config.database import SessionLocal
from models.product import Product, Category, Supplier, StockMovement
from utils.logger import get_logger

class InventoryService:
    """Service for inventory management operations"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def get_products(self, active_only=True):
        """Get all products"""
        db = SessionLocal()
        try:
            query = db.query(Product)
            if active_only:
                query = query.filter(Product.active == True)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error fetching products: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_product_by_id(self, product_id):
        """Get product by ID"""
        db = SessionLocal()
        try:
            return db.query(Product).filter(Product.id == product_id).first()
        except Exception as e:
            self.logger.error(f"Error fetching product {product_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_product_by_sku(self, sku):
        """Get product by SKU"""
        db = SessionLocal()
        try:
            return db.query(Product).filter(Product.sku == sku, Product.active == True).first()
        except Exception as e:
            self.logger.error(f"Error fetching product by SKU {sku}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def create_product(self, product_data):
        """Create new product"""
        db = SessionLocal()
        try:
            # Check if SKU already exists
            existing = db.query(Product).filter(Product.sku == product_data['sku']).first()
            if existing:
                raise ValueError(f"المنتج بالكود {product_data['sku']} موجود بالفعل")
            
            product = Product(**product_data)
            db.add(product)
            db.commit()
            
            # Create initial stock movement if quantity > 0
            if product.quantity > 0:
                self.create_stock_movement({
                    'product_id': product.id,
                    'change_qty': product.quantity,
                    'movement_type': 'initial',
                    'note': 'رصيد ابتدائي'
                })
            
            self.logger.info(f"Created new product: {product.name_ar}")
            return product
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating product: {str(e)}")
            raise e
        finally:
            db.close()
    
    def update_product(self, product_id, product_data):
        """Update existing product"""
        db = SessionLocal()
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError("المنتج غير موجود")
            
            # Check if SKU is being changed and already exists
            if 'sku' in product_data and product_data['sku'] != product.sku:
                existing = db.query(Product).filter(
                    Product.sku == product_data['sku'],
                    Product.id != product_id
                ).first()
                if existing:
                    raise ValueError(f"المنتج بالكود {product_data['sku']} موجود بالفعل")
            
            # Update product fields
            for key, value in product_data.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            
            db.commit()
            self.logger.info(f"Updated product: {product.name_ar}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating product {product_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def delete_product(self, product_id):
        """Soft delete product (mark as inactive)"""
        db = SessionLocal()
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError("المنتج غير موجود")
            
            product.active = False
            db.commit()
            self.logger.info(f"Deleted product: {product.name_ar}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error deleting product {product_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_categories(self):
        """Get all categories"""
        db = SessionLocal()
        try:
            return db.query(Category).all()
        except Exception as e:
            self.logger.error(f"Error fetching categories: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_suppliers(self):
        """Get all suppliers"""
        db = SessionLocal()
        try:
            return db.query(Supplier).all()
        except Exception as e:
            self.logger.error(f"Error fetching suppliers: {str(e)}")
            raise e
        finally:
            db.close()
    
    def create_stock_movement(self, movement_data):
        """Create stock movement and update product quantity"""
        db = SessionLocal()
        try:
            # Create movement record
            movement = StockMovement(**movement_data)
            db.add(movement)
            
            # Update product quantity
            product = db.query(Product).filter(Product.id == movement_data['product_id']).first()
            if product:
                product.quantity += movement_data['change_qty']
                if product.quantity < 0:
                    raise ValueError("الكمية لا يمكن أن تكون أقل من صفر")
            
            db.commit()
            self.logger.info(f"Created stock movement for product {product.name_ar}: {movement_data['change_qty']}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating stock movement: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_low_stock_products(self):
        """Get products with low stock"""
        db = SessionLocal()
        try:
            return db.query(Product).filter(
                Product.quantity <= Product.min_quantity,
                Product.active == True
            ).all()
        except Exception as e:
            self.logger.error(f"Error fetching low stock products: {str(e)}")
            raise e
        finally:
            db.close()
    
    def search_products(self, query):
        """Search products by name, SKU, or barcode"""
        db = SessionLocal()
        try:
            return db.query(Product).filter(
                (Product.name_ar.contains(query)) |
                (Product.sku.contains(query)) |
                (Product.barcode.contains(query)),
                Product.active == True
            ).all()
        except Exception as e:
            self.logger.error(f"Error searching products: {str(e)}")
            raise e
        finally:
            db.close()
