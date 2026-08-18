from fastapi import APIRouter, Depends, HTTPException, status

from app.api import get_current_admin, get_project_service
from app.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectResponse])
def get_all_projects(service: ProjectService = Depends(get_project_service)):
    return service.get_all_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int, service: ProjectService = Depends(get_project_service)
):
    project = service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
    current_admin: str = Depends(get_current_admin),
):
    return service.create_project(project_in)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
    current_admin: str = Depends(get_current_admin),
):
    # Using PATCH instead of PUT because fields in ProjectUpdate are optional
    project = service.update_project(project_id, project_in)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
    current_admin: str = Depends(get_current_admin),
):
    success = service.delete_project(project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return None
