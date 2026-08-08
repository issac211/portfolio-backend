from sqlalchemy.orm import Session

from app.models import PersonalInfo
from app.schemas import PersonalInfoCreate, PersonalInfoUpdate


class PersonalInfoService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_personal_info(self) -> PersonalInfo | None:
        return self.db.query(PersonalInfo).first()

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
