from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies import get_current_admin, get_personal_info_service
from app.models import PersonalInfo
from app.schemas import PersonalInfoCreate, PersonalInfoResponse, PersonalInfoUpdate
from app.services import PersonalInfoService

router = APIRouter(prefix="/profile", tags=["Personal Info"])


@router.get("/", response_model=PersonalInfoResponse)
def get_profile(
    service: PersonalInfoService = Depends(get_personal_info_service),
) -> PersonalInfo:
    return service.get_profile(active_only=True)


@router.put(
    "/", response_model=PersonalInfoResponse, dependencies=[Depends(get_current_admin)]
)
def upsert_profile(
    info_in: PersonalInfoCreate | PersonalInfoUpdate,
    service: PersonalInfoService = Depends(get_personal_info_service),
) -> PersonalInfo:
    """
    Creates the profile if it doesn't exist, updates it if it does.
    """
    return service.upsert_personal_info(info_in)


@router.post(
    "/upload-image",
    response_model=PersonalInfoResponse,
    dependencies=[Depends(get_current_admin)],
)
def upload_profile_image(
    # File(...) tells FastAPI this must come as multipart/form-data
    file: UploadFile = File(...),
    service: PersonalInfoService = Depends(get_personal_info_service),
) -> PersonalInfo:
    """
    Uploads an image, saves it, and updates the profile's image_url.
    """
    return service.upload_image(file)
