from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PersonalInfo
from app.schemas import PersonalInfoCreate, PersonalInfoUpdate

from .upload import save_upload_file, validate_upload_file


class PersonalInfoService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_personal_info(self) -> PersonalInfo | None:
        return self.db.scalar(select(PersonalInfo))

    def upsert_personal_info(
        self, info_data: PersonalInfoCreate | PersonalInfoUpdate
    ) -> PersonalInfo:
        """
        Creates the record if it doesn't exist, updates it if it does.
        """
        info = self.get_personal_info()
        update_data = info_data.model_dump(exclude_unset=True)

        # Convert HttpUrl object to standard string for SQLAlchemy
        if "image_url" in update_data and update_data["image_url"] is not None:
            update_data["image_url"] = str(update_data["image_url"])

        if not info:
            # Create mode
            info = PersonalInfo(**update_data)
            self.db.add(info)
        else:
            # Update mode
            for key, value in update_data.items():
                setattr(info, key, value)

        self.db.commit()
        self.db.refresh(info)
        return info

    def update_image(self, image_url: str) -> PersonalInfo:
        """Directly updates the profile image_url."""
        profile = self.get_personal_info()
        if not profile:
            # We enforce that a text profile must exist before uploading an image
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please create a profile first before uploading an image.",
            )

        profile.image_url = image_url
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def upload_image(self, file: UploadFile) -> PersonalInfo:
        """Uploads and associates an image file with the personal profile."""
        validate_upload_file(file)

        profile = self.get_personal_info()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please create a profile first before uploading an image.",
            )

        file_url = save_upload_file(file, "profile", old_file_url=profile.image_url)
        profile.image_url = file_url
        self.db.commit()
        self.db.refresh(profile)
        return profile
