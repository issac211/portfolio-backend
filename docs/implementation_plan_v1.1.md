# Backend Implementation Plan — v1.1


## Architectural Decisions (v1.1)

| Decision | Choice | Rationale |
|---|---|---|
| Database engine | PostgreSQL (via `psycopg2-binary`) | Production-grade concurrency, JSONB support, Full-Text Search; replaces SQLite. Synchronous SQLAlchemy (`Session`) strictly requires a synchronous driver; `asyncpg` is excluded. |
| Migration tooling | Alembic (existing) | Already integrated; generate new revisions for schema changes |
| Profile soft-delete strategy | `is_active` boolean column | Preserves data integrity; avoids cascading physical deletes on a singleton entity |
| Project description split | Two columns: `summary` (VARCHAR) + `content` (TEXT) | Supports card-level scanning vs. detail-page deep dives without over-fetching |
| Image deletion approach | Dedicated DELETE endpoints that unlink file + null DB column | Clean separation; reuses existing `upload.py` file-handling utilities |
| Profile data expansion | Add columns to `PersonalInfo` model | Single source of truth for hero/footer/navbar marketing data; eliminates frontend hardcoding |
| ETL migration script | One-time Python script (SQLite → PostgreSQL) | Preserves MVP data during database transition |
| Domain vocabulary refactoring | Rename `tech_stack_csv` → `tags_csv` (model) and `tech_stack` → `tags` (schemas/API) | Generalizes the concept beyond technologies to include status labels ("WIP", "Open Source") and categories |
| Availability indicator | `status_indicator` String column with semantic values (`success`, `warning`, `error`, `neutral`) | Drives the UI dot color/animation dynamically from the DB; avoids boolean flags that can't express multiple states |
| API contract-driven development | Export/update `api-contract.json` (OpenAPI) after every schema phase, **before** frontend work begins | Frontend has a machine-readable, reliable source of truth; prevents type drift between backend schemas and TS interfaces |

---

## Current Project State (Baseline v1.0)

```
backend/
├── .env                                  # Configured with PostgreSQL connection string (Phase 1)
├── .env.example
├── .python-version
├── alembic.ini
├── GEMINI.md
├── portfolio.db                          # SQLite database (v1.0)
├── pyproject.toml
├── README.md
├── uv.lock
├── alembic/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
│       ├── a999514ee9b4_initial_tables.py
│       ├── d086cbd3eed6_expand_personal_info_model.py
│       ├── 631310bbdef1_split_project_description_into_summary_.py
│       └── af22ec542233_rename_tech_stack_csv_to_tags_csv.py
├── docs/
│   └── implementation_plan_v1.1.md       # Implementation tracking
├── scripts/
│   ├── export_openapi.py                 # OpenAPI contract export script
│   └── migrate_sqlite_to_pg.py           # SQLite to PostgreSQL ETL script
├── src/app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── personal_info.py
│   │       └── projects.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── personal_info.py
│   │   └── projects.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── personal_info.py
│   │   └── projects.py
│   └── services/
│       ├── __init__.py
│       ├── personal_info.py
│       ├── projects.py
│       └── upload.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── api/
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           ├── test_personal_info.py
│           └── test_projects.py
└── uploads/
    ├── profile/
    └── projects/
```

### Current `PersonalInfo` Schema (v1.1)

| Column | Type | Nullable | Notes / Default |
|---|---|---|---|
| `id` | Integer (PK) | No | Auto-increment sequence |
| `first_name` | String(50) | No | |
| `last_name` | String(50) | No | |
| `birth_date` | Date | Yes | |
| `bio` | Text | Yes | Canonical full biography |
| `image_url` | String(255) | Yes | |
| `hero_title` | String(200) | Yes | Added in Phase 2 |
| `availability_status` | String(100) | Yes | Added in Phase 2 |
| `short_bio` | Text | Yes | Added in Phase 2 (elevator pitch/tagline) |
| `github_url` | String(255) | Yes | Added in Phase 2 |
| `linkedin_url` | String(255) | Yes | Added in Phase 2 |
| `email` | String(255) | Yes | Added in Phase 2 |
| `is_active` | Boolean | No | Added in Phase 2, `server_default=true` |
| `status_indicator` | String(20) | Yes | Added in Phase 2, `server_default="neutral"` |

### Current `Project` Schema (v1.1)

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | Integer (PK) | No | Auto-increment sequence |
| `title` | String(100) | No | Indexed |
| `summary` | String(300) | No | Split from description in Phase 3 |
| `content` | Text | Yes | Added in Phase 3 |
| `github_url` | String(255) | Yes | |
| `live_url` | String(255) | Yes | |
| `image_url` | String(255) | Yes | |
| `tags_csv` | String(255) | Yes | Comma-separated tags (renamed in Phase 4) |
| `display_order` | Integer | No (default 0) | |

### Current API Endpoints (v1.0)

| Method | Path | Auth |
|---|---|---|
| `GET` | `/api/profile/` | Public |
| `PUT` | `/api/profile/` | Admin |
| `POST` | `/api/profile/upload-image` | Admin |
| `GET` | `/api/projects/` | Public |
| `GET` | `/api/projects/{id}` | Public |
| `POST` | `/api/projects/` | Admin |
| `PATCH` | `/api/projects/{id}` | Admin |
| `DELETE` | `/api/projects/{id}` | Admin |
| `POST` | `/api/projects/{id}/upload-image` | Admin |
| `POST` | `/api/auth/login` | Public |

---

## Key Implementation Details

> [!IMPORTANT]
> **Database Migration (SQLite → PostgreSQL):** Cloud PostgreSQL instance provisioned on Neon, `psycopg2-binary` installed, and connection string saved to `.env`. `app.core.config.Settings` incorporates a Pydantic V2 validator that normalizes `postgres://` and `postgresql://` URIs to `postgresql+psycopg2://`. The SQLAlchemy engine in `app.core.database` enables `pool_pre_ping=True` for resilient cloud connection recovery. `scripts/migrate_sqlite_to_pg.py` provides an automated ETL pipeline that migrates SQLite rows and explicitly synchronizes PostgreSQL identity sequences (`setval(pg_get_serial_sequence(...))`).

> [!IMPORTANT]
> **`PersonalInfo` Model Expansion — New Columns:**
> ```
> hero_title        : String(200), nullable=True
> availability_status: String(100), nullable=True
> short_bio         : Text, nullable=True
> github_url        : String(255), nullable=True
> linkedin_url      : String(255), nullable=True
> email             : String(255), nullable=True
> ```
> The existing `bio` column is retained as the full biography (preserving existing data without migration drift), while `short_bio` serves as the concise hero/card tagline. `long_bio` was intentionally omitted to prevent data redundancy.
>
> **Server-Side Defaults for Pre-Existing Rows:** Adding `is_active` (`NOT NULL`) to a table already containing rows requires a database-level default (`server_default=sa.text("true")`). Python-level defaults (`default=True`) only apply to ORM-level inserts and trigger a PostgreSQL `NotNullViolation` during schema migration DDL. `status_indicator` similarly includes `server_default="neutral"`.

> [!IMPORTANT]
> **`PersonalInfo` Model — `status_indicator` Column:**
> ```
> status_indicator : String(20), nullable=True, default="neutral"
> ```
> Allowed semantic values: `success` | `warning` | `error` | `neutral`. This is stored as a plain String (not a DB-level Enum) to avoid Alembic migration complexity with PostgreSQL enum types. Validation is enforced at the **Pydantic schema level** using `Literal["success", "warning", "error", "neutral"]` or a custom validator. The frontend maps these values to Tailwind dot classes (e.g., `success` → pulsing green, `error` → solid red). Do NOT use a boolean flag — the four-state design is intentional.

> [!IMPORTANT]
> **API Contract-Driven Development:**
> After completing database + schema changes in each phase (Phases 2, 3, 4), the backend **must** export/regenerate the OpenAPI spec before frontend work begins:
> ```bash
> # Option A: Dedicated export script (Recommended)
> uv run python scripts/export_openapi.py
> # Option B: Python inline execution
> uv run python -c "import sys; sys.path.insert(0, 'src'); from app.main import app; import json; open('../frontend/api-contract.json', 'w', encoding='utf-8').write(json.dumps(app.openapi(), indent=2))"
> ```
> This file (`frontend/api-contract.json`) serves as the single source of truth for the frontend team. The frontend should validate its TypeScript interfaces against this contract.

> [!IMPORTANT]
> **`Project` Model — Description Split (Safe Column Split - Zero NOT NULL Errors):**
> Splitting `description` into `summary` (VARCHAR(300), NOT NULL) and `content` (TEXT, nullable) was successfully executed in revision `631310bbdef1` using a strict 5-step zero-downtime migration sequence in Alembic to prevent NOT NULL constraint violations on existing rows:
> 1. **Add `summary` as nullable:** `op.add_column('projects', sa.Column('summary', sa.String(length=300), nullable=True))`
> 2. **Execute Data Migration:** `op.execute("UPDATE projects SET summary = LEFT(description, 300)")` to backfill existing data safely.
> 3. **Add `content` column:** `op.add_column('projects', sa.Column('content', sa.Text(), nullable=True))`
> 4. **Enforce NOT NULL constraint:** `op.alter_column('projects', 'summary', nullable=False)` once all rows are guaranteed populated.
> 5. **Drop obsolete column:** `op.drop_column('projects', 'description')`

> [!NOTE]
> **Profile Soft Delete & Singleton Upsert Logic:**
> - Add `is_active: Mapped[bool] = mapped_column(default=True)` to `PersonalInfo`.
> - The `DELETE /api/profile` endpoint sets `is_active = False`.
> - The `GET /api/profile/` endpoint must filter by `is_active == True`.
> - **Singleton Reactivation:** Because `PersonalInfo` is a singleton, if a Profile was soft-deleted (`is_active = False`) and the Admin performs a `PUT /api/profile/` (Upsert), the logic must reactivate the existing record (`is_active = True`) and update it, rather than attempting to insert a new row which would cause a Primary Key / Singleton violation.

> [!NOTE]
> **Image Deletion Endpoints (Resilient Deletion Order):** Both `DELETE /api/profile/image` and `DELETE /api/projects/{id}/image` must enforce transactional safety against race conditions and failures:
> 1. The DB transaction (`image_url = NULL`) must be committed FIRST.
> 2. The physical file `unlink()` in `services/upload.py` is executed ONLY AFTER the database commit succeeds, to prevent dangling pointers in case of a DB rollback.
> 3. If file unlinking fails post-commit (e.g., file not found or I/O error), log a warning rather than rolling back the database transaction (orphaned disk files can be swept via background cleanup, whereas dangling DB pointers cause user-facing broken images and 404s).
> 4. Return `204 No Content` on success.

> [!NOTE]
> **Domain Vocabulary Refactoring — `tech_stack` → `tags` (Alembic Rename Safety):**
> - **Model:** Renamed `tech_stack_csv` → `tags_csv` in the `Project` SQLAlchemy model. The underlying storage mechanism (comma-separated string) remains unchanged in v1.1.
> - **Schemas/API:** Renamed `tech_stack: list[str] | None` → `tags: list[str] | None` in `ProjectBase`, `ProjectCreate`, `ProjectUpdate`, and `ProjectResponse`. The CSV ↔ list serialization logic in the service layer references `tags_csv` / `tags`.
> - **Alembic Rename Safety:** Executed via revision `af22ec542233` explicitly using:
>   ```python
>   op.alter_column('projects', 'tech_stack_csv', new_column_name='tags_csv')
>   ```
>   This prevents Alembic `--autogenerate` from running a destructive drop/add operation that would lead to data loss.
> - **Rationale:** "Tags" generalizes the concept to include project status ("WIP", "Open Source"), categories, and technologies under a single vocabulary.

> [!NOTE]
> **PostgreSQL Unlocks (Future-Proofing):** After migration, `tags_csv` (comma-separated hack) can eventually be replaced with a native `JSONB` or `ARRAY(String)` column. This is **out of scope** for v1.1 but should be noted as a v1.2+ opportunity.

---

## Target Folder Structure (v1.1)

```
backend/
├── .env                                  ✅ Done — PostgreSQL DATABASE_URL configured
├── .env.example                          ✅ Done — documented PostgreSQL connection template
├── .python-version
├── alembic.ini                           ✅ Done — dynamic override via settings.DATABASE_URL
├── GEMINI.md                             [UPDATE] — SOP Section 7 file reference
├── pyproject.toml                        ✅ Done — added psycopg2-binary dependency
├── README.md                             ✅ Done — PostgreSQL & ETL instructions
├── uv.lock                              ✅ Done — lockfile refreshed
├── alembic/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
│       ├── a999514ee9b4_initial_tables.py
│       ├── d086cbd3eed6_expand_personal_info_model.py ✅ Done — hero_title, availability, short_bio, socials, is_active, status_indicator
│       ├── 631310bbdef1_split_project_description_into_summary_.py ✅ Done — description → summary + content
│       └── af22ec542233_rename_tech_stack_csv_to_tags_csv.py ✅ Done — tech_stack_csv → tags_csv
├── docs/
│   └── implementation_plan_v1.1.md       ✅ Done — updated roadmap
├── scripts/
│   ├── export_openapi.py                 ✅ Done — OpenAPI schema export utility
│   └── migrate_sqlite_to_pg.py           ✅ Done — one-time ETL script
├── src/app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── personal_info.py          [UPDATE] — DELETE /profile, DELETE /profile/image
│   │       └── projects.py              [UPDATE] — DELETE /projects/{id}/image
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    ✅ Done — DATABASE_URL normalizer
│   │   ├── database.py                  ✅ Done — pool_pre_ping enabled
│   │   └── security.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── personal_info.py             ✅ Done — expanded model with marketing, social, and state columns
│   │   └── projects.py                 ✅ Done — summary + content
│   ├── schemas/
│   │   ├── __init__.py                  ✅ Done — export concrete schemas
│   │   ├── auth.py
│   │   ├── personal_info.py             ✅ Done — new fields, Literal validation, is_active restricted to Response
│   │   └── projects.py                 ✅ Done — summary + content fields
│   └── services/
│       ├── __init__.py                  [UPDATE] — export new service methods
│       ├── personal_info.py             [UPDATE] — soft delete, image delete logic
│       ├── projects.py                 [UPDATE] — image delete logic
│       └── upload.py                   [UPDATE] — add delete_file utility
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      [UPDATE] — PostgreSQL test setup if needed
│   └── api/
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           ├── test_personal_info.py     ✅ Done — tests for new fields, Literal validation, and soft-delete filtering
│           └── test_projects.py         [UPDATE] — tests for image deletion + split fields
└── uploads/
    ├── profile/
    └── projects/
```

### Target `PersonalInfo` Schema (v1.1)

| Column | Type | Nullable | Status |
|---|---|---|---|
| `id` | Integer (PK) | No | Existing |
| `first_name` | String(50) | No | Existing |
| `last_name` | String(50) | No | Existing |
| `birth_date` | Date | Yes | Existing |
| `bio` | Text | Yes | Existing (evaluate deprecation) |
| `image_url` | String(255) | Yes | Existing |
| `hero_title` | String(200) | Yes | **NEW** |
| `availability_status` | String(100) | Yes | **NEW** |
| `short_bio` | Text | Yes | **NEW** |
| `long_bio` | Text | Yes | **NEW** |
| `github_url` | String(255) | Yes | **NEW** |
| `linkedin_url` | String(255) | Yes | **NEW** |
| `email` | String(255) | Yes | **NEW** |
| `is_active` | Boolean | No (default True) | **NEW** |
| `status_indicator` | String(20) | Yes (default `"neutral"`) | **NEW** |

### Target `Project` Schema (v1.1)

| Column | Type | Nullable | Status |
|---|---|---|---|
| `id` | Integer (PK) | No | Existing |
| `title` | String(100) | No | Existing |
| `summary` | String(300) | No | ✅ Done — RENAMED (was `description`) |
| `content` | Text | Yes | ✅ Done — NEW |
| `github_url` | String(255) | Yes | Existing |
| `live_url` | String(255) | Yes | Existing |
| `image_url` | String(255) | Yes | Existing |
| `tags_csv` | String(255) | Yes | ✅ Done — RENAMED (was `tech_stack_csv`) |
| `display_order` | Integer | No (default 0) | Existing |

### Target API Endpoints (v1.1)

| Method | Path | Auth | Status |
|---|---|---|---|
| `GET` | `/api/profile/` | Public | Existing — [UPDATE] filter `is_active` |
| `PUT` | `/api/profile/` | Admin | Existing — [UPDATE] accept new fields |
| `POST` | `/api/profile/upload-image` | Admin | Existing |
| `DELETE` | `/api/profile/` | Admin | **NEW** — soft delete |
| `DELETE` | `/api/profile/image` | Admin | **NEW** — remove profile image |
| `GET` | `/api/projects/` | Public | Existing |
| `GET` | `/api/projects/{id}` | Public | Existing |
| `POST` | `/api/projects/` | Admin | Existing — ✅ Done (accepts summary+content) |
| `PATCH` | `/api/projects/{id}` | Admin | Existing — ✅ Done (accepts summary+content) |
| `DELETE` | `/api/projects/{id}` | Admin | Existing |
| `POST` | `/api/projects/{id}/upload-image` | Admin | Existing |
| `DELETE` | `/api/projects/{id}/image` | Admin | **NEW** — remove project image |
| `POST` | `/api/auth/login` | Public | Existing |

---

## Step-by-Step Roadmap

### Phase 1: Database Migration (SQLite → PostgreSQL)

- [x] Provision a cloud PostgreSQL database instance
- [x] Add `psycopg2-binary` to `pyproject.toml` via `uv add psycopg2-binary` (strictly lock to synchronous driver; `asyncpg` is excluded)
- [x] Update `core/config.py` — change `DATABASE_URL` default or document the new `.env` variable
- [x] Update `core/database.py` — ensure PostgreSQL driver compatibility (remove SQLite-only `connect_args` guard if no longer needed, or keep it for dev fallback)
- [x] Update `alembic.ini` — ensure `sqlalchemy.url` reads from env / `config.py`
- [x] Write `scripts/migrate_sqlite_to_pg.py` — one-time ETL script to extract data from `portfolio.db` and load into PostgreSQL
- [x] Run Alembic migrations against PostgreSQL to create the baseline schema
- [x] Execute ETL script to migrate existing data
- [x] Verify all existing endpoints work against PostgreSQL (run `uv run pytest -v`)
- [x] Update `.env.example` with PostgreSQL connection string template
- [x] Update `README.md` with PostgreSQL setup instructions

### Phase 2: PersonalInfo Model Expansion (Global State Backend)

- [x] Add new columns to `models/personal_info.py`: `hero_title`, `availability_status`, `short_bio`, `github_url`, `linkedin_url`, `email`
- [x] Add `is_active` boolean column to `models/personal_info.py` (default `True`, for Phase 5 soft delete)
- [x] Add `status_indicator` column to `models/personal_info.py`: `String(20)`, nullable, default `"neutral"` — drives the UI availability dot color/animation
- [x] Generate Alembic migration: `uv run alembic revision --autogenerate -m "expand personal_info model"`
- [x] Apply migration: `uv run alembic upgrade head`
- [x] Update `schemas/personal_info.py` — add new fields to `PersonalInfoBase`, `PersonalInfoCreate`, `PersonalInfoUpdate`, `PersonalInfoResponse`
- [x] Add Pydantic validation for `status_indicator`: use `Literal["success", "warning", "error", "neutral"] | None` to enforce allowed semantic values at the schema level
- [x] Update `services/personal_info.py` — ensure `upsert_personal_info` handles new fields
- [x] Update `api/v1/personal_info.py` — `GET /profile/` must filter by `is_active == True`
- [x] Update `schemas/__init__.py` — export any new schemas
- [x] Add/update tests in `tests/api/v1/test_personal_info.py` for new fields (including `status_indicator` validation — reject invalid values like `"banana"`)
- [x] Verify: `uv run pytest -v`
- [x] **API Contract Sync:** Export updated OpenAPI spec to `frontend/api-contract.json` — this must happen before any frontend Phase 2 work begins

### Phase 3: Project Description Split (Summary vs. Content)

- [x] Update `models/projects.py`: rename `description` to `summary` (`Mapped[str] = mapped_column(String(300), nullable=False)`) and add `content` (`Mapped[str | None] = mapped_column(Text, nullable=True)`)
- [x] Generate Alembic revision: `uv run alembic revision -m "split project description into summary and content"`
- [x] Implement the safe 5-step Alembic migration sequence in the revision to prevent NOT NULL errors:
  1. `op.add_column('projects', sa.Column('summary', sa.String(length=300), nullable=True))`
  2. Data migration: `op.execute("UPDATE projects SET summary = LEFT(description, 300)")`
  3. `op.add_column('projects', sa.Column('content', sa.Text(), nullable=True))`
  4. `op.alter_column('projects', 'summary', nullable=False)`
  5. `op.drop_column('projects', 'description')`
- [x] Apply migration: `uv run alembic upgrade head`
- [x] Update `schemas/projects.py` — replace `description` with `summary` + `content` in all schema classes
- [x] Update `services/projects.py` — adjust create/update logic for new fields
- [x] Update `api/v1/projects.py` — no route changes needed (schemas handle it)
- [x] Update `schemas/__init__.py` — verify exports
- [x] Update tests in `tests/api/v1/test_projects.py` for `summary` + `content`
- [x] Verify: `uv run pytest -v`
- [x] **API Contract Sync:** Export updated OpenAPI spec to `frontend/api-contract.json` — reflects `summary` + `content` fields

### Phase 4: Domain Vocabulary Refactoring (Tech Stack → Tags)

- [x] Rename `tech_stack_csv` → `tags_csv` in `models/projects.py`
- [x] Generate Alembic migration: `uv run alembic revision -m "rename tech_stack_csv to tags_csv"`
- [x] Explicitly implement `op.alter_column('projects', 'tech_stack_csv', new_column_name='tags_csv')` to prevent Alembic from executing a destructive drop/add operation
- [x] Apply migration: `uv run alembic upgrade head`
- [x] Update `schemas/projects.py` — rename `tech_stack` → `tags` in `ProjectBase`, `ProjectCreate`, `ProjectUpdate`, `ProjectResponse`
- [x] Update `services/projects.py` — adjust CSV ↔ list serialization to reference `tags_csv` / `tags` instead of `tech_stack_csv` / `tech_stack`
- [x] Update `schemas/__init__.py` — verify exports (no new schemas, just field renames)
- [x] Update tests in `tests/api/v1/test_projects.py` — replace all `tech_stack` references with `tags`
- [x] Verify: `uv run pytest -v`
- [x] **API Contract Sync:** Export updated OpenAPI spec to `frontend/api-contract.json` — reflects `tags` rename

### Phase 5: Image Deletion & Profile Deletion Endpoints

- [ ] Add `delete_file` utility function to `services/upload.py` — physically unlinks a file given its URL path
- [ ] **Profile Image Deletion (Resilient Deletion):**
  - [ ] Add `delete_image` method to `services/personal_info.py` — commits DB transaction (`image_url = NULL`) FIRST; calls `delete_file` ONLY AFTER database commit succeeds (prevents dangling pointers on DB rollback)
  - [ ] Add `DELETE /api/profile/image` endpoint in `api/v1/personal_info.py` (Admin-only, returns 204)
- [ ] **Project Image Deletion (Resilient Deletion):**
  - [ ] Add `delete_image` method to `services/projects.py` — commits DB transaction (`image_url = NULL`) FIRST; calls `delete_file` ONLY AFTER database commit succeeds
  - [ ] Add `DELETE /api/projects/{id}/image` endpoint in `api/v1/projects.py` (Admin-only, returns 204)
- [ ] **Profile Soft Delete & Singleton Upsert:**
  - [ ] Add `soft_delete` method to `services/personal_info.py` — sets `is_active = False`
  - [ ] Update `upsert_personal_info` in `services/personal_info.py` — handle singleton reactivation: if profile was soft-deleted (`is_active = False`) and Admin performs `PUT /api/profile/`, reactivate (`is_active = True`) and update existing record rather than inserting a new row (prevents PK/singleton violation)
  - [ ] Add `DELETE /api/profile/` endpoint in `api/v1/personal_info.py` (Admin-only, returns 204)
- [ ] Update `services/__init__.py` — export new methods
- [ ] Add tests for `DELETE /api/profile/image` in `test_personal_info.py` (verify commit happens before unlink)
- [ ] Add tests for `DELETE /api/projects/{id}/image` in `test_projects.py`
- [ ] Add tests for `DELETE /api/profile/` (soft delete) and subsequent `PUT /api/profile/` (singleton reactivation) in `test_personal_info.py`
- [ ] Verify: `uv run pytest -v`

### Phase 6: Final Verification & Documentation

- [ ] Run full test suite against PostgreSQL: `uv run pytest -v`
- [ ] Verify all new endpoints in Swagger UI (`/docs`)
- [ ] Update `README.md` with v1.1 API changes
- [ ] Update `.env.example` with any new environment variables
- [ ] Archive `portfolio.db` (SQLite) — it is no longer the primary database

