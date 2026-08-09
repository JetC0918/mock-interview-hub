"""Database configuration for SQLAlchemy with SQLite/PostgreSQL support."""
import os
from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import sessionmaker, declarative_base

# Get database URL from environment variable, default to SQLite for development
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./codiolive.db")

# Handle SQLite-specific configurations
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}  # SQLite requires this for FastAPI
    )
    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()
else:
    # PostgreSQL or other databases
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_timeout=5,
        connect_args={"connect_timeout": 5},
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Upgrade a fresh or already-adopted local database through Alembic."""
    from alembic import command
    from alembic.config import Config

    tables = set(inspect(engine).get_table_names())
    application_tables = tables & {"users", "sessions", "participants"}
    if application_tables and "alembic_version" not in tables:
        raise RuntimeError(
            "Legacy development database is unversioned. Run "
            "`python scripts/adopt_existing_database.py` then `alembic upgrade head`, "
            "or recreate the local database."
        )
    command.upgrade(Config("alembic.ini"), "head")


def verify_migrated_schema():
    """Fail closed when a production instance starts before pre-deploy migrations."""
    with engine.connect() as connection:
        tables = set(inspect(connection).get_table_names())
        if "alembic_version" not in tables:
            raise RuntimeError("Database is not Alembic-managed; run the reviewed adoption/pre-deploy migration")
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
        if version != "0002_secure_collaboration":
            raise RuntimeError(f"Database migration is not at the reviewed head: {version!r}")
        inspector = inspect(connection)
        required_tables = {
            "users", "auth_sessions", "problems", "examples", "sessions",
            "participants", "chat_messages", "guest_admission_attempts", "ai_requests",
        }
        missing_tables = required_tables - tables
        if missing_tables:
            raise RuntimeError(f"Database migration is missing required tables: {sorted(missing_tables)}")
        session_column_rows = {column["name"]: column for column in inspector.get_columns("sessions")}
        session_columns = set(session_column_rows)
        required = {"join_secret_created_at", "code_revision"}
        if not required.issubset(session_columns):
            raise RuntimeError("Database migrations are incomplete")
        if session_column_rows["join_secret_created_at"].get("nullable") or session_column_rows["code_revision"].get("nullable"):
            raise RuntimeError("Database collaboration columns are unexpectedly nullable")
        message_columns = {column["name"]: column for column in inspector.get_columns("chat_messages")}
        if "author_type" not in message_columns or message_columns["author_type"].get("nullable"):
            raise RuntimeError("Database transcript author type is missing or nullable")
        system_user = connection.execute(text(
            "SELECT 1 FROM users WHERE id = 'system:ai-assistant'"
        )).first()
        if not system_user:
            raise RuntimeError("Reserved system AI user is missing")
        participant_unique = {
            item.get("name") for item in inspector.get_indexes("participants") if item.get("unique")
        } | {item.get("name") for item in inspector.get_unique_constraints("participants")}
        pin_unique = {
            item.get("name") for item in inspector.get_indexes("sessions") if item.get("unique")
        } | {item.get("name") for item in inspector.get_unique_constraints("sessions")}
        if "uq_participants_session_user" not in participant_unique or "uq_sessions_pin" not in pin_unique:
            raise RuntimeError("Database collaboration uniqueness constraints are missing")
        index_names = {
            index.get("name")
            for table in ("chat_messages", "participants", "sessions", "guest_admission_attempts", "ai_requests")
            for index in inspector.get_indexes(table)
        }
        required_indexes = {
            "ix_chat_messages_session_timestamp_id", "ix_participants_user_session",
            "ix_sessions_status_created", "ix_guest_admission_attempts_expires",
            "ix_ai_requests_updated_at",
        }
        if not required_indexes.issubset(index_names):
            raise RuntimeError("Database bounded-query indexes are missing")
        if engine.dialect.name == "postgresql":
            trigger = connection.execute(text(
                "SELECT 1 FROM pg_trigger WHERE tgname = 'bump_session_code_revision' AND NOT tgisinternal"
            )).first()
        else:
            trigger = connection.execute(text(
                "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name='bump_session_code_revision'"
            )).first()
        if not trigger:
            raise RuntimeError("Database revision compatibility trigger is missing")
