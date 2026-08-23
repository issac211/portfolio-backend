from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api import get_current_admin, get_personal_info_service
from app.schemas import PersonalInfoCreate, PersonalInfoResponse, PersonalInfoUpdate
from app.services import PersonalInfoService, save_upload_file

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


@router.put(
    "/", response_model=PersonalInfoResponse, dependencies=[Depends(get_current_admin)]
)
def upsert_profile(
    info_in: PersonalInfoCreate | PersonalInfoUpdate,
    service: PersonalInfoService = Depends(get_personal_info_service),
):
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
):
    """
    Uploads an image, saves it, and updates the profile's image_url.
    """
    current_profile = service.get_personal_info()
    old_url = current_profile.image_url if current_profile else None
    file_url = save_upload_file(file, "profile", old_file_url=old_url)
    return service.update_image(file_url)
