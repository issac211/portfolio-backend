from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def _map_db_to_schema(self, db_project: Project) -> Project:
        """Helper to prepare the SQLAlchemy model for Pydantic serialization"""
        # Convert CSV string back to Python list
        if db_project.tech_stack_csv:
            db_project.tech_stack = db_project.tech_stack_csv.split(",")
        else:
            db_project.tech_stack = []
        return db_project

    def get_all_projects(self) -> list[Project]:
        projects = self.db.query(Project).order_by(Project.display_order.asc()).all()
        return [self._map_db_to_schema(p) for p in projects]

    def get_project_by_id(self, project_id: int) -> Project | None:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project:
            return self._map_db_to_schema(project)
        return None

    def create_project(self, project_data: ProjectCreate) -> Project:
        data_dict = project_data.model_dump()

        # 1. Handle Tech Stack (List -> CSV)
        tech_stack_list = data_dict.pop("tech_stack", [])
        data_dict["tech_stack_csv"] = (
            ",".join(tech_stack_list) if tech_stack_list else None
        )

        # 2. Handle HttpUrl conversion to string for SQLite
        for field in ["github_url", "live_url", "image_url"]:
            if data_dict.get(field):
                data_dict[field] = str(data_dict[field])

        # 3. Handle Auto-Ordering (If order wasn't explicitly provided)
        if data_dict.get("display_order") is None:
            # Query the max display_order currently in the DB
            max_order = self.db.query(func.max(Project.display_order)).scalar() or 0
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
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        # exclude_unset=True guarantees we only process fields the client actually sent
        update_data = project_data.model_dump(exclude_unset=True)

        # Handle Tech Stack (List -> CSV)
        if "tech_stack" in update_data:
            tech_stack_list = update_data.pop("tech_stack")
            update_data["tech_stack_csv"] = (
                ",".join(tech_stack_list) if tech_stack_list else None
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
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        self.db.delete(project)
        self.db.commit()
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
