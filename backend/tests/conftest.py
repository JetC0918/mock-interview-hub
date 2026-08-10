import os
os.environ["APP_ENV"] = "test"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use in-memory SQLite for tests with StaticPool to share connection
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with StaticPool to share the same connection
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # This ensures all connections use the same in-memory db
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def client():
    """Create a fresh test client with isolated database for each test function."""
    from app.database.config import get_db, Base
    from app.database.service import seed_database
    from app.main import app
    
    # Import models to register them with Base  
    from app.database import models  # noqa: F401
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create all tables using the test engine
    Base.metadata.create_all(bind=test_engine)
    
    # Seed test data
    db = TestingSessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    
    with TestClient(app) as c:
        yield c
    
    # Cleanup - drop all tables
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()
