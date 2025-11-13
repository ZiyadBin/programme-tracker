import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models, schemas
from app.core.security import get_password_hash
from typing import List, Optional
from sqlalchemy.orm import selectinload

async def get_user_by_username(db: AsyncSession, username: str) -> models.User | None:
    """
    Fetch a single user by their username.
    """
    result = await db.execute(
        select(models.User).filter(models.User.username == username)
    )
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str | uuid.UUID) -> models.User | None:
    """
    Fetch a single user by their ID.
    """
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
        
    result = await db.execute(
        select(models.User).filter(models.User.id == user_id)
    )
    return result.scalars().first()

async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    """
    Create a new user in the database.
    """
    hashed_password = get_password_hash(user.password)
    
    db_user = models.User(
        username=user.username,
        name=user.name,
        password_hash=hashed_password,
        role=user.role,
        district_id=user.district_id,
        division_id=user.division_id
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.User]:
    """
    Fetch a list of users, with pagination.
    """
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.district), selectinload(models.User.division))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_user(db: AsyncSession, user: models.User, updates: schemas.UserUpdate) -> models.User:
    """
    Update a user's details in the database.
    """
    update_data = updates.model_dump(exclude_unset=True) # Get only fields that were set
    
    for key, value in update_data.items():
        setattr(user, key, value)
        
    await db.commit()
    await db.refresh(user)
    return user
