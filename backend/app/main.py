from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, sessions, execution, leaderboard

app = FastAPI(
    title="CodioLive API",
    description="Backend API for CodioLive (Mock Interview Hub)",
    version="1.0.0"
)

# CORS (Allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
