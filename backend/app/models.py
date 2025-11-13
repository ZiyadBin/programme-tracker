import uuid
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, ForeignKey,
    Integer, JSON
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

# Using TEXT for check constraints for portability, though Enum is also an option
# 'admin', 'district', 'division'
# 'low', 'medium', 'high', 'critical'
# 'one-time', 'weekly', 'monthly', 'quarterly', 'yearly', 'tenure'
# 'district', 'all_divisions', 'specific_list'
# 'received', 'assigned', 'in_progress', 'completed', 'blocked'
# 'status_change', 'comment', 'attachment'

class District(Base):
    __tablename__ = "districts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(50), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    divisions = relationship("Division", back_populates="district", cascade="all, delete-orphan")
    users = relationship("User", back_populates="district")

class Division(Base):
    __tablename__ = "divisions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), index=True)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    district = relationship("District", back_populates="divisions")
    users = relationship("User", back_populates="division")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(Text, nullable=False, index=True) # admin, district, division
    active = Column(Boolean, default=True)
    
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)
    division_id = Column(UUID(as_uuid=True), ForeignKey("divisions.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    district = relationship("District", back_populates="users")
    division = relationship("Division", back_populates="users")

class Programme(Base):
    __tablename__ = "programmes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    created_by_user = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    priority = Column(Text, default='medium', index=True) # low, medium, high, critical
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=True)
    
    frequency = Column(Text, default='one-time') # one-time, weekly, etc.
    scope = Column(Text, default='district') # district, all_divisions, specific_list
    
    # Using PostgreSQL's ARRAY type for UUIDs
    assigned_districts = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    assigned_divisions = Column(ARRAY(UUID(as_uuid=True)), nullable=True, index=True)
    
    status = Column(Text, default='received', index=True) # received, assigned, in_progress, completed, blocked
    is_active = Column(Boolean, default=True)
    remarks = Column(Text, nullable=True)
    
    # attachments will store a list of file info objects (e.g., {'key': 's3-key', 'name': 'file.pdf'})
    attachments = Column(JSON, nullable=True) 
    
    # Relationships
    portfolio = relationship("Portfolio")
    creator = relationship("User")
    updates = relationship("ProgrammeUpdate", back_populates="programme", cascade="all, delete-orphan")

class ProgrammeUpdate(Base):
    __tablename__ = "programme_updates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    programme_id = Column(UUID(as_uuid=True), ForeignKey("programmes.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    type = Column(Text, nullable=False) # status_change, comment, attachment
    content = Column(Text, nullable=True) # e.g., "Status changed to Completed", or a comment
    attachments = Column(JSON, nullable=True) # List of file info objects
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    programme = relationship("Programme", back_populates="updates")
    user = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    entity_type = Column(String(100), nullable=False, index=True) # e.g., 'programme', 'user'
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    action = Column(String(100), nullable=False, index=True) # e.g., 'create', 'update', 'delete'
    details = Column(JSON, nullable=True) # Stores 'old_value' and 'new_value'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    actor = relationship("User")
