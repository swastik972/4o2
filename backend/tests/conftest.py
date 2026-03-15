"""
Pytest fixtures for backend testing.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Force a SQLite in-memory database for tests
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.core.database import Base  # noqa: E402
from app.api.deps import get_db  # noqa: E402
from main import app  # noqa: E402


# ── Test database ───────────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    # Clean up test database file
    try:
        if os.path.exists("./test.db"):
            os.remove("./test.db")
    except PermissionError:
        pass  # Windows file-lock — file will be cleaned up on next run


@pytest.fixture()
def db_session():
    """Yield a fresh DB session per test, rolled back after."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with test DB session injected."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
