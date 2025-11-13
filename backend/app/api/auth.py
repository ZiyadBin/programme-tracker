from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.db import get_db_session
from app.schemas import Token, LoginRequest, UserRead
from app.core.security import verify_password, jwt_manager
from app.crud import get_user_by_username

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_for_access_token(
    # Use our schema instead of OAuth2PasswordRequestForm to allow JSON
    form_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Logs in a user and returns access and refresh tokens.
    """
    # Find the user in the database
    user = await get_user_by_username(db, username=form_data.username)
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # Update last_login time
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    # Create the data to be stored in the JWT
    token_data = {
        "sub": user.username,
        "id": str(user.id),
        "role": user.role
    }
    
    # Generate tokens
    access_token = jwt_manager.create_access_token(data=token_data)
    refresh_token = jwt_manager.create_refresh_token(data=token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserRead.model_validate(user) # Return user details
    }
