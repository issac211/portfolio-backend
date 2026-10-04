from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate

from .upload import delete_old_file, save_upload_file, validate_upload_file


class ProjectService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def _map_db_to_schema(self, db_project: Project) -> Project:
        """Helper to prepare the SQLAlchemy model for Pydantic serialization"""
        # Convert CSV string back to Python list
        if db_project.tags_csv:
            db_project.tags = db_project.tags_csv.split(",")
        else:
            db_project.tags = []
        return db_project

    def get_all_projects(self) -> list[Project]:
        statement = select(Project).order_by(Project.display_order.asc())
        projects = self.db.scalars(statement).all()
        return [self._map_db_to_schema(p) for p in projects]

    def get_project_by_id(self, project_id: int) -> Project | None:
        statement = select(Project).where(Project.id == project_id)
        project = self.db.scalar(statement)
        if project:
            return self._map_db_to_schema(project)
        return None

    def create_project(self, project_data: ProjectCreate) -> Project:
        data_dict = project_data.model_dump()

        # 1. Handle Tags (List -> CSV)
        tags_list = data_dict.pop("tags", [])
        data_dict["tags_csv"] = (
            ",".join(tags_list) if tags_list else None
        )

        # 2. Handle HttpUrl conversion to string for SQLite
        for field in ["github_url", "live_url", "image_url"]:
            if data_dict.get(field):
                data_dict[field] = str(data_dict[field])

        # 3. Handle Auto-Ordering (If order wasn't explicitly provided)
        if data_dict.get("display_order") is None:
            # Query the max display_order currently in the DB
            max_order = self.db.scalar(select(func.max(Project.display_order))) or 0
            data_dict["display_order"] = max_order + 1

        # Create and save
        new_project = Project(**data_dict)
        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)

        return self._map_db_to_schema(new_project)

    def update_project(
        self, project_id: int, project_data: ProjectUpdate
    ) -> Project | None:
        statement = select(Project).where(Project.id == project_id)
        project = self.db.scalar(statement)
        if not project:
            return None

        # exclude_unset=True guarantees we only process fields the client actually sent
        update_data = project_data.model_dump(exclude_unset=True)

        # Handle Tags (List -> CSV)
        if "tags" in update_data:
            tags_list = update_data.pop("tags")
            update_data["tags_csv"] = (
                ",".join(tags_list) if tags_list else None
            )

        # Handle HttpUrl conversion
        for field in ["github_url", "live_url", "image_url"]:
            if field in update_data and update_data[field] is not None:
                update_data[field] = str(update_data[field])

        # Apply updates to the model dynamically
        for key, value in update_data.items():
            setattr(project, key, value)

        self.db.commit()
        self.db.refresh(project)

        return self._map_db_to_schema(project)

    def delete_project(self, project_id: int) -> bool:
        statement = select(Project).where(Project.id == project_id)
        project = self.db.scalar(statement)
        if not project:
            return False

        image_to_delete = project.image_url

        self.db.delete(project)
        self.db.commit()

        if image_to_delete:
            delete_old_file(image_to_delete)

        return True

    def update_image(self, project_id: int, image_url: str) -> Project | None:
        """Directly updates the image_url in the database."""
        project = self.get_project_by_id(project_id)
        if not project:
            return None

        project.image_url = image_url
        self.db.commit()
        self.db.refresh(project)
        return project

    def upload_image(self, project_id: int, file: UploadFile) -> Project | None:
        """Uploads and associates an image file with a project."""
        validate_upload_file(file)

        statement = select(Project).where(Project.id == project_id)
        project = self.db.scalar(statement)
        if not project:
            return None

        file_url = save_upload_file(file, "projects", old_file_url=project.image_url)
        project.image_url = file_url
        self.db.commit()
        self.db.refresh(project)
        return self._map_db_to_schema(project)
