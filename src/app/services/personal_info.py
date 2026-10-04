from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PersonalInfo
from app.schemas import PersonalInfoCreate, PersonalInfoUpdate

from .upload import delete_file, save_upload_file, validate_upload_file


class PersonalInfoService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def _get_personal_info(self, active_only: bool = False) -> PersonalInfo | None:
        """Fetch the singleton PersonalInfo profile from the database.

        Args:
            active_only: If True, only queries active profiles (is_active == True).
        """
        stmt = select(PersonalInfo)
        if active_only:
            stmt = stmt.where(PersonalInfo.is_active.is_(True))
        return self.db.scalar(stmt)

    def get_profile(self, active_only: bool = True) -> PersonalInfo:
        """Retrieve the personal profile or raise HTTP 404 if not found.

        Args:
            active_only: If True, restricts retrieval to active profiles.

        Raises:
            HTTPException: 404 NOT FOUND if the profile does not exist or is inactive.
        """
        info = self._get_personal_info(active_only=active_only)
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile info not found. Please create one.",
            )
        return info

    def upsert_personal_info(
        self, info_data: PersonalInfoCreate | PersonalInfoUpdate
    ) -> PersonalInfo:
        """Creates the record if it doesn't exist, updates it if it does.

        Reactivates soft-deleted profiles if updated.
        """
        info = self._get_personal_info(active_only=False)
        update_data = info_data.model_dump(exclude_unset=True)

        # Convert HttpUrl object to standard string for SQLAlchemy
        if "image_url" in update_data and update_data["image_url"] is not None:
            update_data["image_url"] = str(update_data["image_url"])

        if not info:
            # Create mode
            info = PersonalInfo(**update_data)
            self.db.add(info)
        else:
            # Update mode: reactivate if previously soft-deleted
            if not info.is_active:
                info.is_active = True
            for key, value in update_data.items():
                setattr(info, key, value)

        self.db.commit()
        self.db.refresh(info)
        return info

    def soft_delete(self) -> PersonalInfo:
        """Deactivates the personal profile (soft delete)."""
        profile = self.get_profile(active_only=False)
        profile.is_active = False
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update_image(self, image_url: str) -> PersonalInfo:
        """Directly updates the profile image_url."""
        profile = self.get_profile(active_only=False)
        profile.image_url = image_url
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def upload_image(self, file: UploadFile) -> PersonalInfo:
        """Uploads and associates an image file with the personal profile."""
        validate_upload_file(file)

        profile = self.get_profile(active_only=False)
        file_url = save_upload_file(file, "profile", old_file_url=profile.image_url)
        profile.image_url = file_url
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def delete_image(self) -> PersonalInfo:
        """Removes the profile image with resilient post-commit file cleanup.

        1. Fetches the profile (active_only=False).
        2. Sets image_url = None and commits DB transaction FIRST.
        3. Calls delete_file only AFTER DB commit succeeds.
        """
        profile = self.get_profile(active_only=False)
        old_image_url = profile.image_url
        if not old_image_url:
            return profile

        profile.image_url = None
        self.db.commit()
        self.db.refresh(profile)

        delete_file(old_image_url)
        return profile
