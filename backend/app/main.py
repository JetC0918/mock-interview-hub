import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # Load .env from project root

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import auth, sessions, execution, ai
from .database.config import init_db, SessionLocal
from .database.service import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    
    # Only seed if not explicitly disabled (for production)
    if os.environ.get("DISABLE_SEED", "").lower() != "true":
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
def health_check():
    """Health check endpoint for load balancers and container orchestration."""
    return {"status": "healthy"}
