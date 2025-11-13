import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from datetime import datetime
from typing import List, Optional, Any, Dict

# --- Base Models ---

class BaseSchema(BaseModel):
    # Common configuration for all schemas
    model_config = ConfigDict(
        from_attributes=True,  # Replaces orm_mode=True
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

# --- Attachment Schemas ---
# Defines the structure for a file attachment
class AttachmentSchema(BaseSchema):
    file_key: str  # S3 key
    file_name: str # Original file name
    file_type: str
    file_size: int

# --- Portfolio Schemas ---

class PortfolioBase(BaseSchema):
    name: str
    description: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioRead(PortfolioBase):
    id: uuid.UUID

# --- District Schemas ---

class DistrictBase(BaseSchema):
    name: str
    code: Optional[str] = None

class DistrictCreate(DistrictBase):
    pass

class DistrictRead(DistrictBase):
    id: uuid.UUID

# --- Division Schemas ---

class DivisionBase(BaseSchema):
    name: str
    code: Optional[str] = None
    district_id: uuid.UUID

class DivisionCreate(DivisionBase):
    pass

class DivisionRead(DivisionBase):
    id: uuid.UUID

# --- User Schemas ---

class UserBase(BaseSchema):
    username: str
    name: str
    role: str # admin, district, division
    active: bool = True
    district_id: Optional[uuid.UUID] = None
    division_id: Optional[uuid.UUID] = None

class UserCreate(UserBase):
    password: str # Plain text password, will be hashed
    
    @field_validator('role')
    def validate_role(cls, v):
        if v not in ['admin', 'district', 'division']:
            raise ValueError('Invalid role')
        return v

class UserUpdate(BaseSchema):
    name: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None
    district_id: Optional[uuid.UUID] = None
    division_id: Optional[uuid.UUID] = None

    @field_validator('role')
    def validate_role(cls, v):
        if v is not None and v not in ['admin', 'district', 'division']:
            raise ValueError('Invalid role')
        return v

class UserRead(UserBase):
    id: uuid.UUID
    created_at: datetime
    last_login: Optional[datetime] = None
    
    # Optionally include related objects
    district: Optional[DistrictRead] = None
    division: Optional[DivisionRead] = None

class UserInDB(UserBase):
    """Schema for user data stored in the database, including hash"""
    password_hash: str

# --- Auth Schemas ---

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserRead # Send user details back on login

class TokenData(BaseModel):
    """Schema for data stored inside the JWT"""
    username: Optional[str] = None
    user_id: str
    role: str

# --- Programme Schemas ---

class ProgrammeBase(BaseSchema):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = 'medium'
    portfolio_id: Optional[uuid.UUID] = None
    frequency: str = 'one-time'
    scope: str = 'district'
    assigned_districts: Optional[List[uuid.UUID]] = []
    assigned_divisions: Optional[List[uuid.UUID]] = []
    status: str = 'received'
    remarks: Optional[str] = None
    attachments: Optional[List[AttachmentSchema]] = []

class ProgrammeCreate(ProgrammeBase):
    # created_by_user will be added from the current user in the endpoint
    pass

class ProgrammeRead(ProgrammeBase):
    id: uuid.UUID
    created_by_user: uuid.UUID
    created_at: datetime
    last_updated_at: datetime
    is_active: bool

    # Include nested data for easier frontend consumption
    creator: UserRead
    portfolio: Optional[PortfolioRead] = None
    # We might add division/district full objects later if needed
    
class ProgrammeUpdate(BaseSchema):
    # For a PUT/PATCH, all fields are optional
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    portfolio_id: Optional[uuid.UUID] = None
    frequency: Optional[str] = None
    scope: Optional[str] = None
    assigned_districts: Optional[List[uuid.UUID]] = None
    assigned_divisions: Optional[List[uuid.UUID]] = None
    status: Optional[str] = None
    remarks: Optional[str] = None
    attachments: Optional[List[AttachmentSchema]] = None

# --- ProgrammeUpdate (Activity) Schemas ---

class ProgrammeUpdateBase(BaseSchema):
    type: str # status_change, comment, attachment
    content: Optional[str] = None
    attachments: Optional[List[AttachmentSchema]] = []

class ProgrammeUpdateCreate(ProgrammeUpdateBase):
    programme_id: uuid.UUID
    # user_id will be added from the current user in the endpoint
    pass

class ProgrammeUpdateRead(ProgrammeUpdateBase):
    id: uuid.UUID
    programme_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    
    # Include the user who made the update
    user: UserRead

# --- AuditLog Schemas ---

class AuditLogRead(BaseSchema):
    id: uuid.UUID
    actor_user_id: uuid.UUID
    entity_type: str
    entity_id: Optional[uuid.UUID] = None
    action: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    actor: UserRead
