import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models, schemas
from app.core.security import get_password_hash
from typing import List, Optional
from sqlalchemy.orm import selectinload
from app import models, schemas
from sqlalchemy.orm import selectinload, joinedload
from uuid import UUID

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

# --- Programme CRUD ---

async def create_programme(db: AsyncSession, programme: schemas.ProgrammeCreate, user_id: UUID) -> models.Programme:
    """
    Create a new programme.
    """
    db_programme = models.Programme(
        **programme.model_dump(),
        created_by_user=user_id
    )
    db.add(db_programme)
    await db.commit()
    await db.refresh(db_programme)
    return db_programme

async def get_programme_by_id(db: AsyncSession, programme_id: UUID) -> models.Programme | None:
    """
    Fetch a single programme by its ID, with related data.
    """
    result = await db.execute(
        select(models.Programme)
        .options(
            joinedload(models.Programme.creator),
            joinedload(models.Programme.portfolio)
        )
        .filter(models.Programme.id == programme_id)
    )
    return result.scalars().first()

async def get_programmes(
    db: AsyncSession, 
    user: schemas.UserRead,
    skip: int = 0, 
    limit: int = 100
    # TODO: Add filters for status, priority, portfolio, date range
) -> List[models.Programme]:
    """
    Fetch a list of programmes with role-based scoping.
    """
    query = select(models.Programme).options(
        joinedload(models.Programme.portfolio)
    )

    # --- Role-Based Scoping ---
    if user.role == "admin":
        # Admin sees all
        pass 
    elif user.role == "district":
        # District user sees programmes for their district OR their divisions
        query = query.filter(
            models.Programme.assigned_districts.contains([user.district_id]) |
            models.Programme.assigned_divisions.overlap(
                # This part would need a subquery to get divisions for the district
                # For now, let's keep it simple. A better way is needed here.
                # A simple filter for now:
                models.Programme.scope == 'district' # Just an example
            )
        )
    elif user.role == "division":
        # Division user sees only programmes assigned to their division
        query = query.filter(
            models.Programme.assigned_divisions.contains([user.division_id])
        )
    else:
        # No role? No programmes.
        return []

    query = query.order_by(models.Programme.due_date.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def update_programme(db: AsyncSession, programme: models.Programme, updates: schemas.ProgrammeUpdate) -> models.Programme:
    """
    Update a programme's details in the database.
    """
    update_data = updates.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(programme, key, value)
        
    await db.commit()
    await db.refresh(programme)
    return programme

async def create_programme_update(db: AsyncSession, update: schemas.ProgrammeUpdateCreate, user_id: UUID) -> models.ProgrammeUpdate:
    """
    Adds an activity/update to a programme (e.g., status change, comment).
    """
    db_update = models.ProgrammeUpdate(
        **update.model_dump(),
        user_id=user_id
    )
    db.add(db_update)
    
    # Also update the parent programme's status if included
    if update.type == 'status_change' and update.content:
        programme = await get_programme_by_id(db, update.programme_id)
        if programme:
            programme.status = update.content # e.g., content is "Completed"
    
    await db.commit()
    await db.refresh(db_update)
    return db_update

async def get_programme_updates(db: AsyncSession, programme_id: UUID) -> List[models.ProgrammeUpdate]:
    """
    Get all activity updates for a single programme.
    """
    result = await db.execute(
        select(models.ProgrammeUpdate)
        .options(joinedload(models.ProgrammeUpdate.user))
        .filter(models.ProgrammeUpdate.programme_id == programme_id)
        .order_by(models.ProgrammeUpdate.created_at.asc())
    )
    return result.scalars().all()
