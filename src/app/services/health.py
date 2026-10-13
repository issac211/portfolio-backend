import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class HealthService:
    """Service providing infrastructure and dependency connectivity verification."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def check_database(self) -> bool:
        """Executes a low-overhead query to verify database reachability.

        Returns:
            True if database query succeeds, False otherwise.
        """
        try:
            self.db.execute(text("SELECT 1"))
            return True
        except (SQLAlchemyError, OSError) as e:
            logger.error("Database health check probe failed: %s", e)
            return False
