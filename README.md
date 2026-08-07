# CodioLive - Mock Interview Hub

A real-time collaborative coding interview platform where interviewers and candidates can code together, with AI-powered assistance and in-browser code execution.

![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)

## Features

- **Real-time Collaboration** - Multiple users edit code together with live cursor tracking
- **In-Browser Execution** - Run JavaScript and Python directly in the browser via WebAssembly (no server needed)
- **AI Assistant** - Type `@AI` in chat to get help with problem-solving approaches
- **PIN-based Joining** - Share a simple PIN to let participants join your session
- **Guest Access** - Join sessions without creating an account
- **Monaco Editor** - Full-featured code editor with syntax highlighting
- **Problem Challenges** - Built-in coding problems (Two Sum, Reverse String, etc.)

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React, TypeScript, Vite, TailwindCSS, shadcn/ui, Monaco Editor |
| **Backend** | FastAPI, SQLAlchemy, bcrypt, Pydantic |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **AI** | DeepSeek V4 Flash API |
| **Package Managers** | npm (frontend), uv (backend) |

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### 1. Clone & Setup Backend

```bash
cd backend
uv sync                  # Install Python dependencies
```

### 2. Setup Frontend

```bash
cd frontend
npm install              # Install frontend dependencies
```

### 3. Configure Environment

Create a `.env` file in the project root:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 4. Run Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Open http://localhost:8080 in your browser.

## Docker Deployment

Run the full stack with Docker Compose:

```bash
docker compose up
```

This starts:
- PostgreSQL database on port 5432
- FastAPI backend on port 8000
- React frontend on port 8080

## Project Structure

```
mock-interview-hub/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── database/        # SQLAlchemy models & service
│   │   ├── models/          # Pydantic schemas
│   │   ├── routers/         # API endpoints (auth, sessions, chat, AI)
│   │   └── services/        # Business logic
│   ├── tests/               # Unit tests
│   └── tests_integration/   # Integration tests
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # UI components (CodeEditor, ChatPanel, etc.)
│   │   ├── contexts/        # React contexts (AuthContext)
│   │   ├── lib/             # API client & utilities
│   │   └── pages/           # Page components (Lobby, Session)
│   └── public/
├── docker-compose.yml       # Docker orchestration
└── README.md
```

## Usage

### Creating a Session

1. Sign up or log in at `/signup` or `/login`
2. Go to the Lobby and click **Create Session**
3. Enter a title and select a programming language
4. Share the **PIN** with participants

### Joining a Session

1. Get the session PIN from the host
2. Go to the Lobby and click **Join Session**
3. Enter the PIN to join
4. (Or join as a guest directly from a session link)

### Using AI Assistant

In the chat panel, type `@AI` followed by your question:
```
@AI How should I approach finding two numbers that sum to a target?
```

The AI will respond with hints and guidance without giving away the solution.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login with email/password |
| POST | `/auth/signup` | Register new user |
| POST | `/auth/guest` | Join as guest |
| GET | `/auth/me` | Get current user |
| GET | `/sessions/` | List all sessions |
| POST | `/sessions/` | Create new session |
| POST | `/sessions/join-by-pin` | Join using PIN |
| POST | `/sessions/{id}/messages` | Send chat message |
| POST | `/ai/assist` | Get AI guidance |

Full API docs available at http://localhost:8000/docs when backend is running.

## Testing

```bash
# Backend tests
cd backend
uv run pytest -v

# Frontend tests
cd frontend
npm run test
```

## Default Users (Development)

The database is seeded with test accounts:

| Email | Username | Password |
|-------|----------|----------|
| host@example.com | CodeMaster | password |
| dev@example.com | Pythonista | password |
| algo@example.com | AlgoGuru | password |
| frontend@example.com | FrontEndFan | password |

## License

MIT
