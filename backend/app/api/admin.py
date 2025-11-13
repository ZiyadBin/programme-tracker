from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.db import get_db_session
from app.schemas import (
    DistrictCreate, DistrictRead, DivisionCreate, DivisionRead,
    PortfolioCreate, PortfolioRead, UserRead
)
from app.crud import (
    create_district, get_districts, create_division, get_divisions,
    get_divisions_by_district, create_portfolio, get_portfolios
)
from app.deps import get_current_admin_user, get_current_user

router = APIRouter()

# --- Portfolios (Committees) ---

@router.post("/portfolios", response_model=PortfolioRead, status_code=status.HTTP_201_CREATED)
async def create_new_portfolio(
    portfolio_in: PortfolioCreate,
    db: AsyncSession = Depends(get_db_session),
    current_admin: UserRead = Depends(get_current_admin_user)
):
    """(Admin Only) Create a new portfolio/committee."""
    return await create_portfolio(db, portfolio_in)

@router.get("/portfolios", response_model=List[PortfolioRead])
async def read_all_portfolios(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user) # Any auth'd user
):
    """Get a list of all portfolios. (For dropdowns)"""
    return await get_portfolios(db)

# --- Districts ---

@router.post("/districts", response_model=DistrictRead, status_code=status.HTTP_201_CREATED)
async def create_new_district(
    district_in: DistrictCreate,
    db: AsyncSession = Depends(get_db_session),
    current_admin: UserRead = Depends(get_current_admin_user)
):
    """(Admin Only) Create a new district."""
    return await create_district(db, district_in)

@router.get("/districts", response_model=List[DistrictRead])
async def read_all_districts(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user) # Any auth'd user
):
    """Get a list of all districts. (For dropdowns)"""
    return await get_districts(db)

# --- Divisions ---

@router.post("/divisions", response_model=DivisionRead, status_code=status.HTTP_201_CREATED)
async def create_new_division(
    division_in: DivisionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_admin: UserRead = Depends(get_current_admin_user)
):
    """(Admin Only) Create a new division."""
    return await create_division(db, division_in)

@router.get("/divisions", response_model=List[DivisionRead])
async def read_all_divisions(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user) # Any auth'd user
):
    """Get a list of all divisions. (For dropdowns)"""
    return await get_divisions(db)

@router.get("/districts/{district_id}/divisions", response_model=List[DivisionRead])
async def read_divisions_for_district(
    district_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserRead = Depends(get_current_user) # Any auth'd user
):
    """Get a list of divisions for a specific district."""
    return await get_divisions_by_district(db, district_id)
