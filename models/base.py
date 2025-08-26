# Base model file - contains common base classes and mixins
# Individual models are defined in their respective files
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

# Import the actual models from their dedicated files
from models.audit import AuditLog, Backup
