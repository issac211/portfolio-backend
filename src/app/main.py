from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import personal_info, projects
from app.core import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Define the frontend origins that are allowed to make requests
origins = [
    "http://localhost:3000",  # React default port
    "http://127.0.0.1:5173",  # Vite default port
    "https://myfrontend.com",  # Production domain
]

# Configure CORS (CRITICAL for local development with React)
# Do not use allow_origins=["*"] in real production if you have authentication,
# but for a static portfolio frontend reading public data, it's acceptable.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows requests from specified origins
    allow_credentials=True,  # Allows cookies and authentication headers
    allow_methods=["*"],  # Allows all standard HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all request headers
)

# Include the routers
app.include_router(projects.router, prefix="/api/v1")
app.include_router(personal_info.router, prefix="/api/v1")
