from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 1. Define the Data Schema (Contract)
class Project(BaseModel):
    id: int
    title: str
    description: str
    tech_stack: list[str]
    repo_url: str | None = None
    live_url: str | None = None

# 2. Initialize FastAPI app
app = FastAPI(title="Portfolio API")

# 3. Define the frontend origins that are allowed to make requests
origins = [
    "http://localhost:3000",      # React default port
    "http://127.0.0.1:5173",      # Vite default port
    "https://myfrontend.com", # Production domain
]

# Configure CORS (CRITICAL for local development with React)
# Do not use allow_origins=["*"] in real production if you have authentication, 
# but for a static portfolio frontend reading public data, it's acceptable.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Allows requests from specified origins
    allow_credentials=True,         # Allows cookies and authentication headers
    allow_methods=["*"],             # Allows all standard HTTP methods (GET, POST, etc.)
    allow_headers=["*"],             # Allows all request headers
)

# 4. Hardcoded Mock Data (Until we implement SQLite)
MOCK_PROJECTS: list[Project] = [
    Project(
        id=1,
        title="My Portfolio",
        description="A full-stack portfolio built with FastAPI and React.",
        tech_stack=["Python", "FastAPI", "React", "Vite"],
        repo_url="https://github.com/yourusername/my-portfolio"
    ),
    Project(
        id=2,
        title="Weather App",
        description="Simple weather dashboard using external APIs.",
        tech_stack=["JavaScript", "React", "CSS"],
        live_url="https://my-weather-app.com"
    )
]

# 5. Define Endpoints
@app.get("/api/projects", response_model=list[Project])
def get_projects() -> list[Project]:
    """
    Retrieve a list of all portfolio projects.
    """
    return MOCK_PROJECTS