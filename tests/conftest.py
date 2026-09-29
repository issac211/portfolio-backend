import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core import Base, settings
from app.main import app

# CRITICAL: We must import the models here so SQLAlchemy's Base knows about them
# before we call create_all().
from app.models import PersonalInfo, Project  # noqa: F401

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


@pytest.fixture()
def admin_client(client):
    """
    Logs in using the hardcoded test password and returns an authorized client.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD},
    )
    assert response.status_code == 200, "Failed to authenticate test client"
    token = response.json()["access_token"]

    # Set the authorization header for all future requests using this client
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


@pytest.fixture(autouse=True, scope="session")
def setup_test_uploads_dir():
    """
    Creates a temporary directory for file uploads during tests.
    Only overrides MEDIA_ROOT. MEDIA_URL stays '/uploads' for consistent API responses.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override the physical path
        original_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = temp_dir

        yield

        # Restore the physical path
        settings.MEDIA_ROOT = original_media_root
