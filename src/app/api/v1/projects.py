from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.dependencies import get_current_admin, get_project_service
from app.models import Project
from app.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectResponse])
def get_all_projects(
    service: ProjectService = Depends(get_project_service),
) -> list[Project]:
    return service.get_all_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int, service: ProjectService = Depends(get_project_service)
) -> Project:
    return service.get_project_by_id(project_id)


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
def create_project(
    project_in: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    return service.create_project(project_in)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[Depends(get_current_admin)],
)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    # Using PATCH instead of PUT because fields in ProjectUpdate are optional
    return service.update_project(project_id, project_in)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
def delete_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
) -> None:
    service.delete_project(project_id)


@router.post(
    "/{project_id}/upload-image",
    response_model=ProjectResponse,
    dependencies=[Depends(get_current_admin)],
)
def upload_project_image(
    project_id: int,
    file: UploadFile = File(...),
    service: ProjectService = Depends(get_project_service),
) -> Project:
    """
    Uploads an image and assigns it to a specific project.
    """
    return service.upload_image(project_id, file)


@router.delete(
    "/{project_id}/image",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
def delete_project_image(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
) -> None:
    """
    Removes an image associated with a specific project.
    """
    service.delete_image(project_id)
