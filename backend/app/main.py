from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import auth, sessions, execution
from .database.config import init_db, SessionLocal
from .database.service import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    # Seed with initial data
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

# CORS (Allow all for development)
# Logging Middleware
from fastapi import Request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"DEBUG LOG: Incoming Request path: {request.url.path}")
    response = await call_next(request)
    print(f"DEBUG LOG: Response status: {response.status_code}")
    return response

app.add_middleware(
    CORSMiddleware,
    # Allow localhost for development, and all origins for production (behind nginx proxy)
    allow_origins=["http://localhost:8080", "http://localhost:8081", "http://127.0.0.1:8080", "http://127.0.0.1:8081", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(execution.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to CodioLive API"}


@app.get("/health")
def health_check():
    """Health check endpoint for Render and load balancers."""
    return {"status": "healthy"}
