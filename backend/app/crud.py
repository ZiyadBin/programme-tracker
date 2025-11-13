import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models, schemas
from app.core.security import get_password_hash

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

# We will add functions for programmes, divisions, etc. here later
