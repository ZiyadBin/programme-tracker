from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.core.config import settings
from app.schemas import TokenData

# --- Password Hashing ---

# Create a CryptContext for password hashing
# We use bcrypt as the scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain-text password."""
    return pwd_context.hash(password)

# --- JSON Web Tokens (JWT) ---

class JWTManager:
    """
    Utility class for creating and verifying JWT tokens.
    """
    def __init__(self, secret_key: str, refresh_secret: str, algorithm: str):
        self.SECRET_KEY = secret_key
        self.REFRESH_SECRET_KEY = refresh_secret
        self.ALGORITHM = algorithm

    def _create_token(self, data: dict, expires_delta: timedelta, secret_key: str) -> str:
        """Helper to create a token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=self.ALGORITHM)
        return encoded_jwt

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Creates a new access token."""
        if expires_delta:
            delta = expires_delta
        else:
            delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        return self._create_token(data, delta, self.SECRET_KEY)

    def create_refresh_token(self, data: dict) -> str:
        """Creates a new refresh token."""
        delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return self._create_token(data, delta, self.REFRESH_SECRET_KEY)

    def verify_token(self, token: str, secret_key: str) -> TokenData | None:
        """
        Verifies a token and returns its payload (TokenData) on success.
        Returns None if verification fails.
        """
        try:
            payload = jwt.decode(token, secret_key, algorithms=[self.ALGORITHM])
            
            username: str | None = payload.get("sub")
            user_id: str | None = payload.get("id")
            role: str | None = payload.get("role")

            if user_id is None or role is None:
                return None # Invalid payload structure
            
            return TokenData(username=username, user_id=user_id, role=role)
        
        except JWTError:
            return None # Token is invalid or expired

    def verify_access_token(self, token: str) -> TokenData | None:
        """Verifies an access token."""
        return self.verify_token(token, self.SECRET_KEY)

    def verify_refresh_token(self, token: str) -> TokenData | None:
        """Verifies a refresh token."""
        return self.verify_token(token, self.REFRESH_SECRET_KEY)


# Create a single, importable instance of the manager
jwt_manager = JWTManager(
    secret_key=settings.JWT_SECRET_KEY,
    refresh_secret=settings.JWT_REFRESH_SECRET_KEY,
    algorithm=settings.ALGORITHM
)
