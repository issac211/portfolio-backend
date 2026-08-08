from fastapi import APIRouter, Depends, HTTPException, status

from app.api import get_personal_info_service
from app.schemas import PersonalInfoCreate, PersonalInfoResponse, PersonalInfoUpdate
from app.services import PersonalInfoService

router = APIRouter(prefix="/profile", tags=["Personal Info"])


@router.get("/", response_model=PersonalInfoResponse)
def get_profile(service: PersonalInfoService = Depends(get_personal_info_service)):
    info = service.get_personal_info()
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile info not found. Please create one.",
        )
    return info


@router.put("/", response_model=PersonalInfoResponse)
def upsert_profile(
    info_in: PersonalInfoCreate | PersonalInfoUpdate,
    service: PersonalInfoService = Depends(get_personal_info_service),
):
    """
    Creates the profile if it doesn't exist, updates it if it does.
    """
    return service.upsert_personal_info(info_in)
