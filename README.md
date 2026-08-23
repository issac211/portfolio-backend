# Portfolio API Backend

A robust RESTful API built with **FastAPI** to manage a personal developer portfolio. 

## Project Motivation (Why a Backend?)
Typically, a personal portfolio is built as a static website. However, this project was deliberately designed as a **Full-Stack application** to serve as a practical playground for implementing advanced backend engineering concepts. 

The goal was not just to display projects, but to demonstrate proficiency in system design, database management, security, and clean architecture.

## Architecture & Engineering Highlights

This backend is designed with a strong focus on clean architecture, security, and scalability, demonstrating enterprise-grade engineering practices:

* **Domain-Driven Design (DDD) / Layered Architecture:** Clear separation of concerns between Routers (`api`), Business Logic (`services`), Data Access (`models`), and Data Validation (`schemas`).
* **Strategy Pattern for File Uploads:** A dynamic upload service that currently writes to a local temporary/static directory, but is architecturally prepared to switch to Cloud Storage (e.g., Cloudinary/AWS S3) via environment variables without changing business logic.
* **Stateless Authentication:** Secured admin endpoints using **JWT (JSON Web Tokens)**. Secrets are strictly managed via environment variables.
* **Defensive Programming:** Implemented file size limits (HTTP 413) and UUID-based file naming to prevent Path Traversal attacks and storage exhaustion. Read-only image fields in standard CRUD endpoints to prevent orphaned files.
* **Database Migrations:** Full schema version control using **Alembic**.

## Tech Stack

* **Framework:** FastAPI
* **Language:** Python 3.12+
* **Package Manager:** `uv` (Blazing fast Python package manager)
* **Database:** SQLite (Development) / Ready for PostgreSQL
* **ORM:** SQLAlchemy 2.0
* **Migrations:** Alembic
* **Validation:** Pydantic V2
* **Testing:** Pytest, HTTPX

## Project Structure

```text
backend/
├── alembic/              # Database migration versions
├── src/
│   └── app/
│       ├── api/          # Route handlers (Controllers)
│       ├── core/         # App configuration & Security setup
│       ├── models/       # SQLAlchemy database models
│       ├── schemas/      # Pydantic validation schemas
│       └── services/     # Business logic (Services)
├── tests/                # Pytest integration tests
├── .env                  # Environment variables (Ignored in Git)
├── pyproject.toml        # Dependencies and project metadata
└── README.md
```

## Getting Started

### 1. Prerequisites
Ensure you have Python installed and [uv](https://github.com/astral-sh/uv) configured on your machine.

### 2. Environment Setup
Create a `.env` file in the root of the `backend` directory:
```env
ENVIRONMENT="development"
MEDIA_ROOT="uploads"
MEDIA_URL="/uploads"
MAX_IMAGE_SIZE_BYTES=5242880

# Security - Change these!
SECRET_KEY="your-super-secret-crypto-key"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="your-secure-password"
```

### 3. Database Migrations
Run Alembic to create the database tables:
```bash
uv run alembic upgrade head
```

### 4. Run the Development Server
Start the FastAPI application:
```bash
uv run uvicorn app.main:app --app-dir src --reload
```
The API will be available at `http://localhost:8000`.

## API Documentation

FastAPI automatically generates interactive API documentation. 
Once the server is running, navigate to:
* **Swagger UI:** `http://localhost:8000/docs`

*Note: To test protected endpoints (POST, PUT, DELETE), use the "Authorize" button in Swagger UI and log in using the credentials defined in your `.env` file.*

## Testing

The project maintains high test coverage using Pytest. Tests run on an isolated, in-memory SQLite database and use a temporary directory for file uploads to prevent test pollution.

To run the test suite:
```bash
uv run pytest -v
```