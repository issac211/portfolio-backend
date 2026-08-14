import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import get_db
from app.core import Base
from app.main import app

# CRITICAL: We must import the models here so SQLAlchemy's Base knows about them
# before we call create_all().
from app.models import PersonalInfo, Project

# Use an in-memory SQLite database for blazing fast, isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# StaticPool is required for in-memory SQLite to work safely across threads in tests
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def test_db():
    """
    Creates a fresh database before EACH test, and drops it after.
    This guarantees 100% test isolation.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_db):
    """
    Overrides the FastAPI dependency injection to use the test database
    instead of the real development database.
    """

    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)

    # Clean up overrides after the test finishes
    app.dependency_overrides.clear()
