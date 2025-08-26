from datetime import datetime
from sqlalchemy.orm import sessionmaker
from config.database import SessionLocal
from models.transfer import Transfer
from utils.logger import get_logger

class TransferService:
    """Service for balance transfer operations"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def create_transfer(self, transfer_data, user_id):
        """Create new balance transfer"""
        db = SessionLocal()
        try:
            # Generate reference number
            reference_no = self.generate_reference_number()
            
            transfer = Transfer(
                reference_no=reference_no,
                transfer_type=transfer_data['transfer_type'],
                from_account=transfer_data['from_account'],
                to_account=transfer_data['to_account'],
                amount=transfer_data['amount'],
                commission=transfer_data.get('commission', 0),
                note=transfer_data.get('note'),
                user_id=user_id
            )
            db.add(transfer)
            db.commit()
            
            self.logger.info(f"Transfer created: {reference_no}")
            return transfer
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating transfer: {str(e)}")
            raise e
        finally:
            db.close()
    
    def generate_reference_number(self):
        """Generate unique reference number"""
        db = SessionLocal()
        try:
            last_transfer = db.query(Transfer).order_by(Transfer.id.desc()).first()
            if last_transfer and last_transfer.reference_no:
                last_num = int(last_transfer.reference_no.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            return f"TRF-{datetime.now().strftime('%Y%m%d')}-{new_num:04d}"
            
        except Exception:
            # Fallback to timestamp-based number
            return f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        finally:
            db.close()
    
    def get_all_transfers(self):
        """Get all transfers"""
        db = SessionLocal()
        try:
            transfers = db.query(Transfer).order_by(Transfer.date.desc()).all()
            return transfers
        except Exception as e:
            self.logger.error(f"Error fetching transfers: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_transfer_by_id(self, transfer_id):
        """Get transfer by ID"""
        db = SessionLocal()
        try:
            transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
            return transfer
        except Exception as e:
            self.logger.error(f"Error fetching transfer {transfer_id}: {str(e)}")
            return None
        finally:
            db.close()
    
    def update_transfer(self, transfer_id, update_data):
        """Update transfer"""
        db = SessionLocal()
        try:
            transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
            if not transfer:
                raise ValueError("Transfer not found")
            
            for key, value in update_data.items():
                if hasattr(transfer, key):
                    setattr(transfer, key, value)
            
            db.commit()
            self.logger.info(f"Transfer updated: {transfer_id}")
            return transfer
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating transfer {transfer_id}: {str(e)}")
            raise e
        finally:
            db.close()
    
    def delete_transfer(self, transfer_id):
        """Delete transfer"""
        db = SessionLocal()
        try:
            transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
            if not transfer:
                raise ValueError("Transfer not found")
            
            db.delete(transfer)
            db.commit()
            self.logger.info(f"Transfer deleted: {transfer_id}")
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error deleting transfer {transfer_id}: {str(e)}")
            raise e
        finally:
            db.close()