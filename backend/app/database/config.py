"""Database configuration for SQLAlchemy with SQLite/PostgreSQL support."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Get database URL from environment variable, default to SQLite for development
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./codiolive.db")

# Handle SQLite-specific configurations
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}  # SQLite requires this for FastAPI
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(DATABASE_URL)

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
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
