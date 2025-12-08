# CodioLive Backend

FastAPI backend service for CodioLive (Mock Interview Hub) - a collaborative coding interview platform.

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy with SQLite (dev) / PostgreSQL (prod)
- **Authentication**: bcrypt password hashing
- **Package Manager**: uv

## Setup

```bash
# Install dependencies
uv sync
```

## Database Configuration

By default, the backend uses **SQLite** for local development:
```bash
# Creates codiolive.db in backend directory
uv run uvicorn app.main:app --reload --port 8000
```

### Using PostgreSQL

Set the `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/codiolive"
uv run uvicorn app.main:app --reload --port 8000
```

### Database Initialization

The database is automatically initialized on startup:
1. Creates all tables if they don't exist
2. Seeds with sample users, problems, and a demo session

**Seeded Users** (password: `password` for all):
| Email | Username | Role |
|-------|----------|------|
| host@example.com | CodeMaster | host |
| dev@example.com | Pythonista | participant |
| algo@example.com | AlgoGuru | participant |
| frontend@example.com | FrontEndFan | spectator |

## Running the Server

```bash
# Development with hot reload
uv run uvicorn app.main:app --reload --port 8000

# Or using Makefile
make run
```

API available at http://localhost:8000  
Swagger docs at http://localhost:8000/docs

## Running Tests

```bash
uv run pytest           # All tests
uv run pytest -v        # Verbose output
uv run pytest tests/test_api.py  # Specific file
```

Tests use an in-memory SQLite database for isolation.

## Project Structure

```
backend/
├── app/
│   ├── database/       # SQLAlchemy models & service
│   │   ├── config.py   # DB configuration
│   │   ├── models.py   # ORM models
│   │   └── service.py  # CRUD operations
│   ├── models/         # Pydantic schemas
│   ├── routers/        # API endpoints
│   └── services/       # Business logic
├── tests/              # Pytest tests
└── pyproject.toml      # Dependencies
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | Login with email/password |
| POST | /auth/signup | Register new user |
| POST | /auth/guest | Guest login |
| GET | /sessions/ | List all sessions |
| POST | /sessions/ | Create new session |
| POST | /sessions/{id}/join | Join a session |
| POST | /execution/run | Execute code |
