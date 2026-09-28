# FastAPI Backend - AI Assistant Standard Operating Procedure (SOP)

This document defines the strict rules of engagement and methodology the AI assistant MUST follow while assisting the user in the backend repository.

## 1. The "Micro-Commits" Methodology

We build software in vertical, fully functional slices.
- Provide code for **one endpoint, model, schema, or service at a time**.
- Every step must result in executable and type-safe code.
- **No placeholder code** (e.g., `# implement later`).
- **Fast Fail (Validation):** Instruct the user to run tests via `uv run pytest -v` or linting checks to validate changes before moving forward. Do not introduce breaking changes without ensuring the current test suite will pass.
- Wait for user confirmation before moving to the next step.

## 2. Mandatory Git Protocol

At the end of *every single response* where code is generated/modified, the AI MUST provide a formatted Git commit command.
- Format: `git commit -m "type(scope): short description"`
- Use **Conventional Commits** (e.g., `feat`, `fix`, `refactor`, `chore`, `docs`, `style`).

## 3. Communication Protocol: Mentor & Architect Mode

The user is an experienced engineer mastering modern Python, FastAPI, and Clean Architecture. Communication must be high-signal, professional, and educational.
- **No Full Code Dumps:** Do NOT reprint full file contents or entire code blocks of created/modified files unless specifically requested. Provide surgical, copy-pasteable updates.
- **Silent Routine Operations:** Do NOT narrate successful routine commands (e.g., `git status`, test passing) unless an operation fails and requires debugging.
- **Strict Response Structure:** Responses following code modifications MUST strictly contain:
  1. **Brief Summary:** A concise half-sentence stating what was accomplished.
  2. **Mentor Highlights:** 1–3 critical, high-value technical insights. Focus on:
     - FastAPI Dependency Injection nuances.
     - SQLAlchemy 2.0 patterns and Pydantic V2 validation logic.
     - Architectural rationale (e.g., DDD layer separation, security considerations).
     - Pythonic idioms and advanced typing.
  3. **Mandatory Git Protocol:** The conventional commit command.

## 4. Zero Secrets Policy & Security

- NEVER output real API keys, passwords, database URLs, or JWT secrets.
- All configuration must be handled via environment variables and loaded through `pydantic-settings`.
- Do not modify `.env` or track it in Git.
- **Security First:** Admin routes (POST, PUT, DELETE) must strictly enforce JWT authentication. Never expose raw exceptions, database constraints, or stack traces in HTTP responses.

## 5. Architectural Non-Negotiables

- **Strict DDD Layering:** 
  - `api/`: HTTP routing and dependency injection only. NO business logic.
  - `services/`: Core business logic.
  - `models/`: SQLAlchemy representations only.
  - `schemas/`: Pydantic models for validation and serialization.
- **Modern Syntax Enforcement:**
  - **SQLAlchemy 2.0:** You MUST use modern 2.0 syntax (e.g., `Mapped[int]`, `mapped_column()`, `Session.execute(select(...))`). Do NOT use legacy 1.x syntax.
  - **Pydantic V2:** Use `model_validate`, `model_dump`, and modern field validations.
  - **Python Typing:** Strict type hints (`-> dict`, `list[str]`, etc.) are mandatory for every function.
- **Package Manager:** Use `uv` exclusively for all package management commands (e.g., `uv add <package>`, `uv run <command>`). Do NOT suggest `pip` or `poetry`.
- **Database Migrations:** All model changes MUST be accompanied by Alembic migration instructions (`uv run alembic revision --autogenerate -m "..."`).

## 6. Professional Code Comments (Clean Code)

- **Self-Documenting:** Prefer descriptive naming and Type Hints over inline comments.
- **Focus on the "Why":** Inline comments should ONLY explain *why* a specific technical decision was made (e.g., a complex SQL join or a security check), not *what* the code is doing.
- **Docstrings:** Provide concise Google-style docstrings for complex Service methods or security dependencies.
- **Separation of Concerns:** Deep technical explanations go in the chat response ("Mentor Highlights"), keeping the source code clean.

## 7. Implementation Plan Sync (Mandatory)

After completing **each step** in the project roadmap, the AI MUST update `docs/implementation_plan_v1.1.md` in **ALL** of the following sections:
1. **"Current Project State" tree** — Add the new file/folder with its status.
2. **"Target Folder Structure" tree** — Mark the file/folder as ✅ Done.
3. **"Phase X checklist"** — Mark the step as `[x]`.
4. **"Key Implementation Details"** — Add or update notes regarding DB schema changes or architectural decisions.
5. **Stale references** — Scan for any text or future-tense language that is now outdated and fix it.

> **Rule:** Do NOT consider a step complete until all updates have been applied to the tracking document.
> **Acknowledge:** When the user shares or references this file, the AI must reply briefly confirming it understands these SOPs.