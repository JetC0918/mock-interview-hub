import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # Load .env from project root

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import auth, sessions, execution, ai
from .database.config import init_db, verify_migrated_schema, SessionLocal
from .database.service import DatabaseService, seed_database
from .utils.rate_limit import limiter
from .middleware.body_limit import BodySizeLimitMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as DBSession
from .database.config import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    app_env = os.environ.get("APP_ENV", "development").lower()
    seed_demo_data = os.environ.get("SEED_DEMO_DATA", "").lower() == "true"
    if app_env == "production":
        verify_migrated_schema()
        if len(os.environ.get("IDEMPOTENCY_SECRET", "")) < 32:
            raise RuntimeError("IDEMPOTENCY_SECRET must be configured with at least 32 characters")
        if os.environ.get("COOKIE_SECURE", "").lower() != "true":
            raise RuntimeError("COOKIE_SECURE=true is required in production")
        if seed_demo_data:
            raise RuntimeError("SEED_DEMO_DATA must be false in production")
        db = SessionLocal()
        try:
            if DatabaseService(db).has_known_demo_accounts():
                raise RuntimeError(
                    "Known demo accounts exist in the production database; migrate or remove them before startup"
                )
        finally:
            db.close()
    elif app_env != "test":
        init_db()
    if app_env != "production" and seed_demo_data:
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()
    yield


app = FastAPI(
    title="CodioLive API",
    description="Backend API for CodioLive (Mock Interview Hub)",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=1_048_576)


@app.middleware("http")
async def prevent_dynamic_response_caching(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response

# CORS Configuration
# Get allowed origins from environment or use defaults for development
frontend_url = os.environ.get("FRONTEND_URL", "")
allowed_origins = [
    "http://localhost:8080",
    "http://localhost:8081", 
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://localhost:80",
    "http://localhost:5173",  # Vite dev server
]

# Add production frontend URL if configured
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(execution.router)
app.include_router(ai.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to CodioLive API"}


@app.get("/health")
def health_check(db: DBSession = Depends(get_db)):
    """Readiness check: the process is ready only when its database responds."""
    try:
        if db.bind and db.bind.dialect.name == "postgresql":
            db.execute(text("SET LOCAL statement_timeout = '3000ms'"))
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "healthy", "database": "ready"}
