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
* **Database:** PostgreSQL (Neon Cloud via `psycopg2-binary`) / SQLite (Fallback & In-Memory Tests)
* **ORM:** SQLAlchemy 2.0
* **Migrations:** Alembic
* **Validation:** Pydantic V2
* **Testing:** Pytest, HTTPX
* **Linter & Formatter:** Ruff

## Project Structure

```text
backend/
├── alembic/              # Database migration versions
├── docs/                 # Implementation roadmap and specifications
├── scripts/              # Data ETL and maintenance scripts
│   └── migrate_sqlite_to_pg.py
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
Create a `.env` file in the root of the `backend` directory (refer to `.env.example`):
```env
ENVIRONMENT="development"
MEDIA_ROOT="uploads"
MEDIA_URL="/uploads"
MAX_IMAGE_SIZE_BYTES=5242880

# Database Connection (Neon Cloud PostgreSQL)
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<host>.neon.tech/<dbname>?sslmode=require"

# Security - Change these!
SECRET_KEY="your-super-secret-crypto-key"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="your-secure-password"
```

### 3. Database Setup & Migration (PostgreSQL)

The application uses PostgreSQL (hosted on [Neon](https://neon.tech)) in production and development, driven by SQLAlchemy 2.0 with the synchronous `psycopg2-binary` adapter.

#### A. Database Provisioning & Connection URL

Configure your `DATABASE_URL` in `.env`. Ensure that the connection string uses the `postgresql+psycopg2://` driver scheme and includes `?sslmode=require`.

> [!WARNING]
> **Neon Serverless Connections (Alembic Requirement):**
> Neon provides connection pooling via PgBouncer by default (indicated by `-pooler` in the host domain). **Alembic migrations will fail** with `server closed the connection unexpectedly` or transaction errors when run through a connection pooler, because DDL migrations and transactional advisory locks require direct session-level capabilities.
> 
> **Action Required:** In the Neon console, uncheck **Pooled connection** and copy the **Direct Connection** URI for your `DATABASE_URL`.

#### B. Applying Schema Migrations

Run Alembic to create or upgrade database tables to the latest revision:

```bash
uv run alembic upgrade head
```

> [!NOTE]
> **Windows Execution Policies (`os error 4551` Fallback):**
> On Windows workstations, running `uv run alembic upgrade head` may fail with `os error 4551` or `Access is denied` if Windows Defender Application Control (WDAC) or endpoint security restricts execution of the generated `.venv\Scripts\alembic.exe` wrapper binary.
> 
> If you encounter this error, execute Alembic directly via Python's module runner:
> ```bash
> uv run python -m alembic upgrade head
> ```

#### C. Data Migration & Sequence Synchronization (One-Time ETL)

If you are migrating existing data from a local SQLite database (`portfolio.db`) to PostgreSQL, execute the automated ETL script **after** applying the baseline Alembic migrations:

```bash
uv run python scripts/migrate_sqlite_to_pg.py
```

> [!IMPORTANT]
> **Primary Key Sequence Synchronization:**
> When rows with explicit IDs (`id=1, 2, ...`) are transferred into PostgreSQL, the underlying `SERIAL`/`IDENTITY` sequence counters do not automatically advance. The ETL script executes `SELECT setval(pg_get_serial_sequence(...))` for every table, ensuring that subsequent `POST` requests create new records without encountering `UniqueViolation` primary key collisions.

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

## Code Quality & Linting (Ruff)

This project enforces modern Python syntax, strict type checking, and clean architecture practices using [Ruff](https://docs.astral.sh/ruff/).

### 1. Essential Commands

* **Run linter checks:**
  ```bash
  uv run ruff check .
  ```
* **Format the codebase:**
  ```bash
  uv run ruff format .
  ```
* **Apply safe automated fixes (syntax & modern typing):**
  ```bash
  uv run ruff check . --fix
  ```

### 2. Architectural Guidelines & Best Practices

To preserve framework idioms and clean separation of concerns, adhere to the following rules:

* **Step-by-Step Hygiene:** Run `uv run ruff check .` alongside `uv run pytest -v` after completing every endpoint, service, or model slice before committing.
* **No Blind Deletions:** Never delete lines or blindly run `--fix` to silence linter warnings without evaluating their architectural purpose.
* **FastAPI Dependency Injection (`B008`):** Route parameter defaults using `Depends()`, `File()`, `Query()`, or `Path()` are configured under `[tool.ruff.lint.flake8-bugbear]` in `pyproject.toml` via `extend-immutable-calls`. Never refactor route signatures to bypass B008.
* **Side-Effect & Discovery Imports (`F401`):** SQLAlchemy models imported for `Base.metadata` discovery in `tests/conftest.py` and `alembic/env.py` must be guarded with `# noqa: F401`. Module `__init__.py` files must declare explicit public exports using `__all__`.
* **Defensive Error Handling (`BLE001`, `S110`):** Avoid broad exception clauses (`except Exception: pass`). Catch concrete errors (e.g., `OSError as e`) and log them using module-level loggers (`logger = logging.getLogger(__name__)`).
