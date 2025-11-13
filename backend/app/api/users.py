from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.db import get_db_session
from app.schemas import UserCreate, UserRead, UserUpdate
from app.crud import create_user, get_user_by_id, get_users, update_user, get_user_by_username
from app.deps import get_current_admin_user, get_current_user

router = APIRouter()

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    current_admin: UserRead = Depends(get_current_admin_user)
):
    """
    (Admin Only) Create a new user.
    """
    existing_user = await get_user_by_username(db, user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists.",
        )
    
    user = await create_user(db, user_in)
    return user

@router.get("/", response_model=List[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_admin: UserRead = Depends(get_current_admin_user)
):
    """
    (Admin Only) Retrieve a list of all users.
    """
    users = await get_users(db, skip=skip, limit=limit)
    return users

@router.get("/me", response_model=UserRead)
async def read_user_me(
    current_user: UserRead = Depends(get_current_user)
):
    """
    Get the details for the currently logged-in user.
    """
    return current_user

@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_admin: UserRead = Depends(get_current_admin_user)
):
    """
    (Admin Only) Get details for a specific user by ID.
    """
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

@router.put("/{user_id}", response_model=UserRead)
async def update_existing_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_admin: UserRead = Depends(get_current_admin_user)
):
    """
    (Admin Only) Update a user's details.
    """
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user = await update_user(db, user=user, updates=user_in)
    return user
