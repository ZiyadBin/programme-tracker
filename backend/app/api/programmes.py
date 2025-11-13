from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.db import get_db_session
from app.schemas import (
    ProgrammeCreate, ProgrammeRead, ProgrammeUpdate, 
    ProgrammeUpdateCreate, ProgrammeUpdateRead, UserRead
)
from app.crud import (
    create_programme, get_programme_by_id, get_programmes, 
    update_programme, create_programme_update, get_programme_updates
)
from app.deps import get_current_admin_user, get_current_user

router = APIRouter()

@router.post("/", response_model=ProgrammeRead, status_code=status.HTTP_201_CREATED)
async def create_new_programme(
    programme_in: ProgrammeCreate,
    db: AsyncSession = Depends(get_db_session),
    current_admin: UserRead = Depends(get_current_admin_user)
):
    """
    (Admin Only) Create a new programme.
    """
    programme = await create_programme(db, programme_in, user_id=current_admin.id)
    # We fetch it again to get the joined data (creator, portfolio)
    return await get_programme_by_id(db, programme.id)

@router.get("/", response_model=List[ProgrammeRead])
async def read_programmes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Get a list of programmes based on the user's role.
    (Admin sees all, District/Division see assigned)
    """
    programmes = await get_programmes(db, user=current_user, skip=skip, limit=limit)
    
    # Re-validate with ProgrammeRead to ensure joined data is loaded
    # This is a bit inefficient, but ensures schema compliance
    return [ProgrammeRead.model_validate(p) for p in programmes]

@router.get("/{programme_id}", response_model=ProgrammeRead)
async def read_programme(
    programme_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Get a single programme by ID.
    TODO: Add role-based access check
    """
    programme = await get_programme_by_id(db, programme_id)
    if programme is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme not found",
        )
    # TODO: Check if user (if not admin) has access to this programme
    return programme

@router.put("/{programme_id}", response_model=ProgrammeRead)
async def update_existing_programme(
    programme_id: uuid.UUID,
    programme_in: ProgrammeUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_admin: UserRead = Depends(get_current_admin_user)
):
    """
    (Admin Only) Update a programme's details.
    """
    programme = await get_programme_by_id(db, programme_id)
    if programme is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme not found",
        )
    
    updated_programme = await update_programme(db, programme=programme, updates=programme_in)
    return updated_programme

# --- Programme Updates (Activity) ---

@router.post("/{programme_id}/updates", response_model=ProgrammeUpdateRead, status_code=status.HTTP_201_CREATED)
async def add_programme_update(
    programme_id: uuid.UUID,
    update_in: ProgrammeUpdateCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Add an update (status change, comment, attachment) to a programme.
    (Accessible by Admin, District, Division)
    """
    if programme_id != update_in.programme_id:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Programme ID in URL and body do not match.",
        )
         
    # TODO: Check if user has permission to update this programme
    
    update = await create_programme_update(db, update=update_in, user_id=current_user.id)
    
    # Load the user data for the response
    await db.refresh(update, relationship_names=["user"])
    return update

@router.get("/{programme_id}/updates", response_model=List[ProgrammeUpdateRead])
async def read_programme_updates(
    programme_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Get the activity feed (all updates) for a programme.
    """
    # TODO: Check if user has permission to view this programme
    updates = await get_programme_updates(db, programme_id)
    return updates
