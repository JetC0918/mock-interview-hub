from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, sessions, execution, leaderboard

app = FastAPI(
    title="CodioLive API",
    description="Backend API for CodioLive (Mock Interview Hub)",
    version="1.0.0"
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
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(execution.router)
app.include_router(leaderboard.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to CodioLive API"}
