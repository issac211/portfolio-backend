from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import auth, personal_info, projects
from app.core import settings

# Create uploads directory if it doesn't exist
Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)

# Configure CORS
# Reads allowed origins dynamically from ALLOWED_ORIGINS environment variable via settings
# Falls back to ["http://localhost:5173"] for local development if not set.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,  # Allows cookies and authentication headers
    allow_methods=["*"],  # Allows all standard HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all request headers
)

app.mount(
    settings.MEDIA_URL,
    StaticFiles(directory=settings.MEDIA_ROOT),
    name="uploads",
)

# Include the routers
app.include_router(projects.router, prefix="/api/v1")
app.include_router(personal_info.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
