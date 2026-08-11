"""Integration test configuration with file-based SQLite database."""
import os
os.environ["APP_ENV"] = "test"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use file-based SQLite for integration tests
TEST_DB_PATH = "./test_integration.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test engine that persists for the entire test session."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    yield engine
    engine.dispose()
    # Cleanup: remove the test database file
    # Note: On Windows, this may fail if the file is still locked
    try:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    except PermissionError:
        pass


@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    """Create a session factory bound to the test engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def setup_database(test_engine):
    """Create all tables once per test session."""
    from app.database.config import Base
    from app.database import models  # noqa: F401 - Register models
    
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_engine, TestingSessionLocal, setup_database):
    """Create a test client with database session for each test function."""
    from app.database.config import get_db
    from app.main import app
    from app.utils.rate_limit import limiter

    # The limiter is process-global, while integration tests are isolated cases.
    # Reset request history so one test cannot consume another test's quota.
    with limiter._lock:
        limiter._windows.clear()
        limiter._checks = 0
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db_session(TestingSessionLocal, setup_database):
    """Provide a database session for direct database operations in tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
