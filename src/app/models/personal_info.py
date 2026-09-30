from datetime import date

from sqlalchemy import Boolean, Date, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core import Base


class PersonalInfo(Base):
    __tablename__ = "personal_info"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Expanded Marketing & Global State Fields ---
    hero_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    availability_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    short_bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Soft Delete & Status Indicator ---
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    status_indicator: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default="neutral", server_default="neutral"
    )
