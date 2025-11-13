from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create the async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Log SQL queries - disable in production
    future=True
)

# Create a session maker
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base class for our SQLAlchemy models
Base = declarative_base()

async def get_db_session() -> AsyncSession:
    """
    FastAPI dependency to get a database session.
    Yields a session and ensures it's closed.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
