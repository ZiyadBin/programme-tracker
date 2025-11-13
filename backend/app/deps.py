from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.db import get_db_session
from app.core.security import jwt_manager
from app.schemas import TokenData, UserRead
from app.crud import get_user_by_id

# This tells FastAPI to look for a token in the "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_session)
) -> UserRead:
    """
    Dependency to get the current user from a JWT token.
    Enforces authentication on any endpoint that uses it.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify the token
    token_data = jwt_manager.verify_access_token(token)
    if not token_data:
        raise credentials_exception
    
    # Get the user from the database
    user = await get_user_by_id(db, user_id=token_data.user_id)
    if user is None or not user.active:
        raise credentials_exception
    
    # Return the Pydantic model of the user
    return UserRead.model_validate(user)

def get_current_admin_user(
    current_user: UserRead = Depends(get_current_user)
) -> UserRead:
    """
    Dependency to ensure the current user is an admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have administrative privileges",
        )
    return current_user
