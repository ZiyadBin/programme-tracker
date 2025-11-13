from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.api import auth, users, programmes

# Create the FastAPI app instance
app = FastAPI(
    title="SSF Programme Tracker API",
    description="API for managing SSF programmes, divisions, and users.",
    version="0.1.0"
)

# --- CORS Middleware ---
# This allows your React frontend (running on localhost:5173) 
# to communicate with your backend (running on localhost:8000)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- API Routers ---
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"]) 
app.include_router(programmes.router, prefix="/api/programmes", tags=["Programmes"])

# --- Health Check Endpoint ---
@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "message": "API is running"}

# --- Generic Exception Handler ---
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catches all unhandled exceptions and returns a 500 error.
    """
    # In a real app, you'd log the exception 'exc' here
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Catches SQLAlchemy-specific errors.
    """
    # Log the full error for debugging
    print(f"Database error: {exc}") 
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred."},
    )

# --- Application Startup Event ---
@app.on_event("startup")
async def startup_event():
    """
    Code to run on application startup.
    e.g., connect to database, seed initial data
    """
    # We don't need to explicitly connect, SQLAlchemy engine handles that.
    # But this is where you could add a seeding script check.
    print("FastAPI application starting up...")
    # Note: Don't run migrations here. 
    # Migrations should be run as a separate step before starting the app.
    # Railway can run 'alembic upgrade head && uvicorn ...'

@app.on_event("shutdown")
async def shutdown_event():
    """
    Code to run on application shutdown.
    """
    print("FastAPI application shutting down...")
