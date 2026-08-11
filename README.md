# CodioLive — Mock Interview Hub

CodioLive is a shared workspace for practicing technical interviews. Interviewers and candidates can work through a problem in one room with a synchronized Monaco editor, participant cursors, chat, AI coaching, and a spectator view for active sessions.

### [Open the live preview](https://mock-interview-hub.onrender.com/)

![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

> Code execution is intentionally disabled until the project has an isolated runner. CodioLive currently focuses on interview collaboration, shared code, discussion, and guided problem solving.

## Why CodioLive exists

Mock interviews often happen across a video call, a separate editor, chat, and a collection of copied links. That fragmentation makes it harder to focus on the candidate's reasoning.

CodioLive brings the interview workspace together. The host controls the session lifecycle, the candidate can join without creating a permanent account, and both people see the same code and conversation. AI acts as a coach that offers hints and questions rather than replacing the interview with a generated answer.

## Who it is for

- **Interviewers** who want one place to present a problem, observe the candidate's approach, and guide the discussion.
- **Candidates** who want realistic practice with shared code, time pressure, and collaborative feedback.
- **Study partners** who want to solve algorithm problems together without passing code snippets back and forth.
- **Observers and mentors** who want to follow active sessions through a privacy-limited spectator view.

## Core experience

- Create a private interview room and choose its language or coding problem.
- Invite a registered participant or a guest with an expiring join secret.
- Edit the same code while participant cursors and language changes stay synchronized.
- Keep interview discussion and AI coaching in one shared transcript.
- Ask Gemini for Socratic hints tied to the current problem context.
- Publish only active sessions to the live spectator area.
- End the interview cleanly and preserve the workspace as read-only.

## How a session works

1. A host creates a session in the waiting state.
2. The host shares the session link and high-entropy join secret.
3. The candidate joins with an account or a temporary guest identity.
4. The host starts the session, enabling collaboration and public discovery.
5. Participants edit, chat, move cursors, and request AI guidance.
6. The host ends the session, which blocks further mutations.

## What to expect from the preview

The production preview has no deterministic demo accounts or seeded live rooms. Create an account, open a session, and use its share action to test the participant flow in a second browser or private window.

CodioLive is an interview-practice application, not a sandboxed code judge. Shared code can be written and reviewed, but the browser and application server do not execute it. A future runner would need a separately isolated service with explicit resource limits.

## Technical overview

### Stack

| Layer | Technologies |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, React Router, TanStack Query |
| UI system | Tailwind CSS, shadcn/ui, Radix UI, Lucide icons |
| Editor | Monaco Editor with same-origin production assets |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy |
| Data | SQLite locally, PostgreSQL 16 in production, Alembic migrations |
| Authentication | Opaque database-backed sessions and bcrypt password hashing |
| AI | Gemini 3.6 Flash over bounded asynchronous HTTP |
| API contract | OpenAPI schema and generated TypeScript client |
| Quality | Pytest, Vitest, Testing Library, ESLint, TypeScript |
| Delivery | Docker, Nginx, Supervisor, Render Blueprint |
| Package management | npm and uv |

### Production architecture

~~~mermaid
flowchart LR
    B["Browser"] -->|"HTTPS"| N["Nginx"]
    N -->|"React, Monaco, static assets"| B
    N -->|"/api/*"| F["FastAPI on 127.0.0.1:8000"]
    F --> P["Render PostgreSQL"]
    F -->|"Bounded async request"| D["Gemini API"]
    S["Supervisor"] --> N
    S --> F
~~~

The multi-stage image builds React with Node 20, then copies the SPA and Monaco runtime into a Python 3.12 image. Nginx serves the frontend and proxies /api to FastAPI on the container loopback interface. This keeps authentication cookies, API calls, and editor workers on one origin.

### Engineering choices

- **Revisioned collaboration:** code and language writes carry a monotonic revision, so stale updates conflict instead of overwriting newer work.
- **Safe polling:** the client preserves dirty local edits and ignores stale responses while polling bounded session and transcript data.
- **Scoped identity:** protected mutations resolve the user from an opaque session_token cookie, never from a body-supplied user ID.
- **Public/private DTOs:** spectator responses omit join secrets, host IDs, internal participant IDs, and private session fields.
- **Retry safety:** guest admission and paid AI requests use stable identifiers to prevent duplicate identities, provider calls, or transcript rows.
- **Lifecycle rules:** waiting, active, and ended transitions are serialized; ended sessions reject collaboration mutations.
- **Bounded work:** request bodies, fields, transcript pages, local rate-limit storage, and provider responses have explicit limits.
- **Execution boundary:** compatibility execution endpoints return 503 until an isolated runner exists.

## Run locally

### Prerequisites

- Node.js 20+
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### 1. Clone and configure

~~~bash
git clone https://github.com/JetC0918/mock-interview-hub.git
cd mock-interview-hub
cp .env.example .env
~~~

Add a Gemini key to .env if you want AI coaching:

~~~env
GEMINI_API_KEY=your_gemini_api_key
~~~

Without DATABASE_URL, local development uses SQLite at backend/codiolive.db. Demo records remain off unless SEED_DEMO_DATA=true is explicitly set.

### 2. Start FastAPI

~~~bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
~~~

The API runs at http://localhost:8000 and Swagger UI is available at http://localhost:8000/docs.

### 3. Start React

In a second terminal:

~~~bash
cd frontend
npm ci
npm run dev
~~~

Open http://localhost:8080. Vite proxies /api requests to the local FastAPI server.

### Environment variables

| Variable | Purpose | Local behavior |
| --- | --- | --- |
| DATABASE_URL | SQLAlchemy connection URL | Defaults to SQLite |
| GEMINI_API_KEY | Enables AI coaching | AI requests are unavailable when omitted |
| FRONTEND_URL | Adds an allowed CORS origin | Localhost origins are built in |
| APP_ENV | Selects development, test, or production rules | development |
| COOKIE_SECURE | Restricts auth cookies to HTTPS | Required in production |
| IDEMPOTENCY_SECRET | Signs retry-safe guest and AI operations | Must be 32+ characters in production |
| SEED_DEMO_DATA | Opts into development demo records | false |
| POSTGRES_PASSWORD | Supplies the development Compose database password | No default |

Never commit .env or provider and database credentials.

## API and verification

FastAPI's Pydantic models are the runtime contract for backend/openapi.yaml and the generated client in frontend/src/lib/api-client. Update the schema and regenerate the client when an endpoint changes; avoid ad hoc browser requests that bypass those contracts.

- Local API docs: http://localhost:8000/docs
- Live API docs: https://mock-interview-hub.onrender.com/api/docs
- Production readiness: /api/health

~~~bash
# Backend
cd backend
uv run pytest -q

# Frontend
cd ../frontend
npx vitest run
npm run typecheck
npm run lint
npm run build

# Patch hygiene
cd ..
git diff --check
~~~

## Deployment

Production is defined by render.yaml as one same-origin Docker Web Service and one private Render PostgreSQL database in Singapore.

- Alembic migrations run as a pre-deploy command.
- Nginx binds to Render's runtime PORT and proxies API traffic internally.
- The health endpoint verifies database connectivity.
- Monaco and its workers ship inside the immutable image, with no runtime editor CDN.
- Render stores GEMINI_API_KEY privately and generates IDEMPOTENCY_SECRET.
- Production startup rejects demo seeding and insecure cookie configuration.

The Compose files are for development. The root Dockerfile and Render Blueprint are the production source of truth.

## Project structure

~~~text
mock-interview-hub/
├── backend/
│   ├── app/                 # FastAPI routes, services, models, and persistence
│   ├── migrations/          # Alembic schema history
│   ├── tests/               # Unit tests
│   └── tests_integration/   # API and database integration tests
├── frontend/
│   ├── src/components/      # Interview workspace and shared UI
│   ├── src/lib/             # API adapter and generated client
│   └── src/pages/           # Lobby, session, auth, and spectator screens
├── Dockerfile               # Combined production image
├── render.yaml              # Render infrastructure contract
└── README.md
~~~
