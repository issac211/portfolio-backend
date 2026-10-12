import logging
import re
import shutil
import uuid
from pathlib import Path

import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from fastapi import HTTPException, UploadFile, status

from app.core import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4"}


def _extract_cloudinary_public_id(file_url: str) -> str | None:
    """Extracts the public_id (including folder path, excluding extension) from a Cloudinary URL."""
    if "/upload/" not in file_url:
        return None

    # Strip query parameters if present
    after_upload = file_url.split("/upload/", 1)[1].split("?")[0]
    segments = after_upload.split("/")

    # Skip transformation segments and version tag (e.g. 'v1712345678')
    start_idx = 0
    for idx, segment in enumerate(segments):
        if re.match(r"^v\d+$", segment):
            start_idx = idx + 1
            break
        if "," in segment or "_" in segment:
            start_idx = idx + 1

    target_path = "/".join(segments[start_idx:])
    public_id = re.sub(r"\.[a-zA-Z0-9]+$", "", target_path)
    return public_id if public_id else None


def delete_file(file_url: str | None) -> None:
    """Deletes a file from local disk or Cloudinary to prevent storage leaks.

    Example local file_url: "/uploads/profile/1234.jpg"
    Example cloud file_url: "https://res.cloudinary.com/.../portfolio/profile/1234.jpg"
    """
    if not file_url:
        return

    if settings.ENVIRONMENT == "production":
        if not settings.CLOUDINARY_URL:
            logger.warning("Cannot delete file: CLOUDINARY_URL is not configured.")
            return

        if "res.cloudinary.com" in file_url:
            public_id = _extract_cloudinary_public_id(file_url)
            if public_id:
                try:
                    cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL)
                    cloudinary.uploader.destroy(public_id, invalidate=True)
                    logger.info("Successfully deleted cloud asset: %s", public_id)
                except (CloudinaryError, OSError) as e:
                    logger.warning("Failed to delete asset from Cloudinary: %s", e)
    else:
        # Local delete logic (Development)
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
                    logger.warning(e)


def delete_old_file(file_url: str | None) -> None:
    """Alias for delete_file for backwards compatibility."""
    delete_file(file_url)


def validate_upload_file(upload_file: UploadFile) -> str:
    """Validates file size and allowed extension before any processing.

    Returns the lowercase file extension.
    """
    if upload_file.size and upload_file.size > settings.MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File is too large. Maximum allowed size is {settings.MAX_IMAGE_SIZE_BYTES / 1024 / 1024}MB.",
        )

    extension = Path(upload_file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {extension} is not allowed.",
        )

    return extension


def save_upload_file(
    upload_file: UploadFile, subfolder: str, old_file_url: str | None = None
) -> str:
    """Saves an uploaded file safely and returns the relative or cloud URL path."""
    extension = validate_upload_file(upload_file)

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
    except OSError as e:
        logger.error(f"Failed to write file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file to disk.",
        ) from e

    return f"{settings.MEDIA_URL}/{subfolder}/{unique_filename}"


def _save_to_cloud(upload_file: UploadFile, subfolder: str) -> str:
    """Uploads the file directly from memory buffer to Cloudinary (Production)."""
    if not settings.CLOUDINARY_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary is not configured. Missing CLOUDINARY_URL in environment.",
        )

    try:
        cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL)
        upload_file.file.seek(0)
        response = cloudinary.uploader.upload(
            upload_file.file,
            folder=f"portfolio/{subfolder}",
            resource_type="auto",
            use_filename=True,
            unique_filename=True,
        )
        return response["secure_url"]
    except Exception as e:
        logger.error(f"Failed to upload file to Cloudinary: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not save file to cloud storage.",
        ) from e
