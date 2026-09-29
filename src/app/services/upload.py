import logging
import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4"}


def delete_old_file(file_url: str | None):
    """
    Deletes the old file from disk to prevent storage leaks.
    Example file_url: "/uploads/profile/1234.jpg"
    """
    if not file_url:
        return

    if settings.ENVIRONMENT == "production":
        # FUTURE: Cloudinary delete logic goes here
        pass
    else:
        # Local delete logic
        # Check if the URL starts with our expected prefix (e.g. "/uploads")
        if file_url.startswith(settings.MEDIA_URL):
            # Extract just the relative part: "profile/1234.jpg"
            relative_path = file_url[len(settings.MEDIA_URL) :].lstrip("/")
            # Map it to the physical disk: "uploads/profile/1234.jpg" (or Temp dir in tests)
            local_path = Path(settings.MEDIA_ROOT) / relative_path

            if local_path.exists() and local_path.is_file():
                try:
                    local_path.unlink()
                except OSError as e:
                    logging.warning(e)


def save_upload_file(
    upload_file: UploadFile, subfolder: str, old_file_url: str | None = None
) -> str:
    """
    Saves an uploaded file safely and returns the relative URL path.
    """
    # Validate File Size
    if upload_file.size and upload_file.size > settings.MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File is too large. Maximum allowed size is {settings.MAX_IMAGE_SIZE_BYTES / 1024 / 1024}MB.",
        )

    # Validate Extension
    extension = Path(upload_file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {extension} is not allowed.",
        )

    if old_file_url:
        delete_old_file(old_file_url)

    if settings.ENVIRONMENT == "production":
        return _save_to_cloud(upload_file, subfolder)
    return _save_to_local_disk(upload_file, subfolder, extension)


def _save_to_local_disk(upload_file: UploadFile, subfolder: str, extension: str) -> str:
    """Saves the file to the local hard drive (Development)."""
    target_dir = Path(settings.MEDIA_ROOT) / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    # Secure random filename to prevent overwriting and path traversal attacks
    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = target_dir / unique_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file to disk.",
        )

    return f"{settings.MEDIA_URL}/{subfolder}/{unique_filename}"


def _save_to_cloud(upload_file: UploadFile, subfolder: str) -> str:
    """
    FUTURE IMPLEMENTATION: Saves to Cloudinary/AWS (Production).
    """
    raise NotImplementedError(
        "Cloud storage is not implemented yet. Set ENVIRONMENT='development'."
    )
