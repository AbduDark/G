from datetime import datetime
from sqlalchemy.orm import sessionmaker
from config.database import SessionLocal
from models.repair import Repair
from models.sales import Customer
from utils.logger import get_logger

class RepairService:
    """Service for repair management operations"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def create_repair(self, repair_data, user_id):
        """Create new repair ticket"""
        db = SessionLocal()
        try:
            # Generate ticket number
            ticket_no = self.generate_ticket_number()
            
            repair = Repair(
                ticket_no=ticket_no,
                customer_id=repair_data['customer_id'],
                device_model=repair_data['device_model'],
                problem_desc=repair_data['problem_desc'],
                status=repair_data.get('status', 'قيد الفحص'),
                parts_cost=repair_data.get('parts_cost', 0),
                labor_cost=repair_data.get('labor_cost', 0),
                total_cost=repair_data.get('parts_cost', 0) + repair_data.get('labor_cost', 0),
                notes=repair_data.get('notes'),
                user_id=user_id
            )
            db.add(repair)
            db.commit()
            
            self.logger.info(f"Created repair ticket: {ticket_no}")
            return repair
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating repair: {str(e)}")
            raise e
        finally:
            db.close()
    
    def generate_ticket_number(self):
        """Generate unique ticket number"""
        db = SessionLocal()
        try:
            today = datetime.now().strftime("%Y%m%d")
            count = db.query(Repair).filter(
                Repair.ticket_no.like(f"REP-{today}-%")
            ).count()
            
            return f"REP-{today}-{count + 1:04d}"
            
        except Exception as e:
            self.logger.error(f"Error generating ticket number: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_repairs(self, status=None, customer_id=None):
        """Get repairs with optional filters"""
        db = SessionLocal()
        try:
            query = db.query(Repair)
            
            if status:
                query = query.filter(Repair.status == status)
            if customer_id:
                query = query.filter(Repair.customer_id == customer_id)
            
            return query.order_by(Repair.entry_date.desc()).all()
            
        except Exception as e:
            self.logger.error(f"Error fetching repairs: {str(e)}")
            raise e
        finally:
            db.close()
    
    def get_repair_by_id(self, repair_id):
        """Get repair by ID"""
        db = SessionLocal()
        try:
            return db.query(Repair).filter(Repair.id == repair_id).first()
        except Exception as e:
            self.logger.error(f"Error fetching repair {repair_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def update_repair(self, repair_id, repair_data):
        """Update repair ticket"""
        db = SessionLocal()
        try:
            repair = db.query(Repair).filter(Repair.id == repair_id).first()
            if not repair:
                raise ValueError("تذكرة الصيانة غير موجودة")
            
            for key, value in repair_data.items():
                if hasattr(repair, key):
                    setattr(repair, key, value)
            
            # Update total cost
            repair.total_cost = repair.parts_cost + repair.labor_cost
            
            # Set exit date if status is completed
            if repair.status == "تم الإصلاح" and not repair.exit_date:
                repair.exit_date = datetime.now()
            
            db.commit()
            self.logger.info(f"Updated repair: {repair.ticket_no}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating repair {repair_id}: {str(e)}")
            raise e
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
    
    def search_repairs(self, query):
        """Search repairs by ticket number, customer name, or device model"""
        db = SessionLocal()
        try:
            return db.query(Repair).join(Customer).filter(
                (Repair.ticket_no.contains(query)) |
                (Customer.name.contains(query)) |
                (Repair.device_model.contains(query))
            ).all()
        except Exception as e:
            self.logger.error(f"Error searching repairs: {str(e)}")
            raise e
        finally:
            db.close()
