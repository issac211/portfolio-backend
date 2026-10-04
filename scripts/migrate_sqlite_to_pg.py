"""One-time ETL migration script: SQLite (portfolio.db) to PostgreSQL.

This script extracts existing PersonalInfo and Project records from local SQLite
and safely inserts them into the target PostgreSQL database configured in .env.
It also resets the PostgreSQL primary key sequences to prevent future INSERT conflicts.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

# Ensure 'src' is discoverable on pythonpath
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from app.core import settings
from app.models import PersonalInfo, Project

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def migrate_data(sqlite_path: Path) -> None:
    """Migrate data from SQLite database to PostgreSQL.

    Args:
        sqlite_path: Path to the source SQLite database file.
    """
    if not sqlite_path.exists():
        logger.warning(
            "No SQLite database found at '%s'. Skipping data migration.", sqlite_path
        )
        return

    if not settings.DATABASE_URL.startswith("postgresql"):
        logger.error(
            "Target DATABASE_URL is not PostgreSQL (got '%s'). Aborting migration.",
            settings.DATABASE_URL.split("://")[0] + "://***",
        )
        sys.exit(1)

    sqlite_url = f"sqlite:///{sqlite_path.as_posix()}"
    logger.info("Connecting to source SQLite: %s", sqlite_url)
    sqlite_engine = create_engine(sqlite_url)

    logger.info("Connecting to target PostgreSQL...")
    pg_engine = create_engine(settings.DATABASE_URL)

    with Session(sqlite_engine) as sqlite_session, Session(pg_engine) as pg_session:
        # 1. Migrate PersonalInfo
        personal_infos = sqlite_session.execute(select(PersonalInfo)).scalars().all()
        logger.info("Found %d PersonalInfo record(s) in SQLite.", len(personal_infos))
        for pi in personal_infos:
            existing = pg_session.get(PersonalInfo, pi.id)
            if existing is None:
                new_pi = PersonalInfo(
                    id=pi.id,
                    first_name=pi.first_name,
                    last_name=pi.last_name,
                    birth_date=pi.birth_date,
                    bio=pi.bio,
                    image_url=pi.image_url,
                )
                pg_session.add(new_pi)
                logger.info(
                    "  -> Staged PersonalInfo id=%s (%s %s)",
                    pi.id,
                    pi.first_name,
                    pi.last_name,
                )
            else:
                logger.info(
                    "  -> PersonalInfo id=%s already exists in PostgreSQL, skipping.",
                    pi.id,
                )

        # 2. Migrate Projects
        projects = sqlite_session.execute(select(Project)).scalars().all()
        logger.info("Found %d Project record(s) in SQLite.", len(projects))
        for prj in projects:
            existing_prj = pg_session.get(Project, prj.id)
            if existing_prj is None:
                new_prj = Project(
                    id=prj.id,
                    title=prj.title,
                    description=prj.description,
                    github_url=prj.github_url,
                    live_url=prj.live_url,
                    image_url=prj.image_url,
                    tech_stack_csv=prj.tech_stack_csv,
                    display_order=prj.display_order,
                )
                pg_session.add(new_prj)
                logger.info("  -> Staged Project id=%s ('%s')", prj.id, prj.title)
            else:
                logger.info(
                    "  -> Project id=%s already exists in PostgreSQL, skipping.", prj.id
                )

        # Commit all staged records
        pg_session.commit()
        logger.info("Successfully committed records to PostgreSQL.")

        # 3. Synchronize PostgreSQL primary key sequences
        logger.info("Synchronizing PostgreSQL primary key sequence counters...")
        for table_name in ("personal_info", "projects"):
            seq_sync_query = text(
                f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table_name}), 1));"
            )
            pg_session.execute(seq_sync_query)
        pg_session.commit()
        logger.info("Primary key sequences successfully synchronized.")


def main() -> None:
    """Entry point for the ETL migration."""
    archived_path = BASE_DIR / "archive" / "portfolio.db.bak"
    sqlite_db_path = (
        archived_path if archived_path.exists() else BASE_DIR / "portfolio.db"
    )
    migrate_data(sqlite_db_path)
    logger.info("ETL SQLite -> PostgreSQL migration process completed.")


if __name__ == "__main__":
    main()
