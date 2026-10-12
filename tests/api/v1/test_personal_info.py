from pathlib import Path

from sqlalchemy import select

from app.core import settings
from app.models import PersonalInfo


def test_get_profile_not_found(client):
    response = client.get("/api/v1/profile/")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_upsert_profile_create(admin_client):
    # Using Fake/Mock Data instead of real PII
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "bio": "Anonymous Software Developer testing the system.",
        "birth_date": "1990-01-01",
        "hero_title": "Full Stack Cloud Engineer",
        "availability_status": "Available for contract",
        "short_bio": "Crafting resilient microservices and distributed systems.",
        "github_url": "https://github.com/johndoe",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "email": "john@example.com",
        "status_indicator": "success",
    }
    response = admin_client.put("/api/v1/profile/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["hero_title"] == "Full Stack Cloud Engineer"
    assert data["availability_status"] == "Available for contract"
    assert (
        data["short_bio"] == "Crafting resilient microservices and distributed systems."
    )
    assert data["github_url"] == "https://github.com/johndoe"
    assert data["linkedin_url"] == "https://linkedin.com/in/johndoe"
    assert data["email"] == "john@example.com"
    assert data["status_indicator"] == "success"
    assert data["is_active"] is True
    assert "id" in data


def test_upsert_profile_update(admin_client):
    # 1. Create initial anonymous profile
    admin_client.put(
        "/api/v1/profile/",
        json={"first_name": "Jane", "last_name": "Smith", "bio": "Initial Mock Bio"},
    )

    # 2. Update the bio
    update_payload = {"bio": "Updated Mock Bio"}

    response = admin_client.put("/api/v1/profile/", json=update_payload)
    assert response.status_code == 200
    data = response.json()

    # Verify the bio changed, but the names stayed the same
    assert data["bio"] == "Updated Mock Bio"
    assert data["first_name"] == "Jane"


def test_upsert_profile_create_unauthorized(client):
    payload = {
        "first_name": "Hacked",
        "last_name": "Hacked",
        "bio": "Hacked",
        "birth_date": "1990-01-01",
    }
    response = client.put("/api/v1/profile/", json=payload)
    assert response.status_code == 401


def test_upload_profile_image(admin_client):
    # Ensure profile exists first
    admin_client.put(
        "/api/v1/profile/", json={"first_name": "Test", "last_name": "User"}
    )

    # Mock a file upload (simulate an image file in memory)
    file_content = b"fake image bytes"
    # Format: {"field_name": ("filename", file_content, "content_type")}
    files = {"file": ("test_pic.jpg", file_content, "image/jpeg")}

    response = admin_client.post("/api/v1/profile/upload-image", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["image_url"] is not None
    assert f"{settings.MEDIA_URL}/profile/" in data["image_url"]
    assert data["image_url"].endswith(".jpg")


def test_upload_profile_image_too_large(admin_client):
    # Create a fake file that is just 1 byte larger than the maximum allowed
    oversized_content = b"0" * (settings.MAX_IMAGE_SIZE_BYTES + 1)
    files = {"file": ("huge_pic.jpg", oversized_content, "image/jpeg")}

    response = admin_client.post("/api/v1/profile/upload-image", files=files)

    # Must be 413 Payload Too Large
    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_status_indicator_validation(admin_client):
    # Valid semantic values
    for val in ("success", "warning", "error", "neutral"):
        res = admin_client.put(
            "/api/v1/profile/",
            json={"first_name": "A", "last_name": "B", "status_indicator": val},
        )
        assert res.status_code == 200
        assert res.json()["status_indicator"] == val

    # Invalid value should trigger 422 Unprocessable Entity
    invalid_res = admin_client.put(
        "/api/v1/profile/",
        json={"first_name": "A", "last_name": "B", "status_indicator": "banana"},
    )
    assert invalid_res.status_code == 422


def test_get_profile_inactive_filtered(admin_client, client, test_db):
    # 1. Create profile
    admin_client.put(
        "/api/v1/profile/",
        json={"first_name": "Hidden", "last_name": "User"},
    )
    # 2. Deactivate profile (simulate soft delete)
    profile = test_db.scalar(select(PersonalInfo))
    assert profile is not None
    profile.is_active = False
    test_db.commit()

    # 3. Public GET should filter out inactive profiles and return 404
    response = client.get("/api/v1/profile/")
    assert response.status_code == 404


def test_upsert_profile_reactivates_inactive_singleton(admin_client, client, test_db):
    # 1. Create and deactivate profile
    admin_client.put(
        "/api/v1/profile/",
        json={"first_name": "Reactivated", "last_name": "User"},
    )
    profile = test_db.scalar(select(PersonalInfo))
    assert profile is not None
    profile.is_active = False
    test_db.commit()

    assert client.get("/api/v1/profile/").status_code == 404

    # 2. Upserting automatically reactivates the singleton
    admin_client.put(
        "/api/v1/profile/",
        json={
            "first_name": "Reactivated",
            "last_name": "User",
            "hero_title": "Back online",
        },
    )
    res = client.get("/api/v1/profile/")
    assert res.status_code == 200
    assert res.json()["is_active"] is True
    assert res.json()["hero_title"] == "Back online"


def test_upsert_profile_cannot_manually_deactivate(admin_client):
    # Attempting to pass is_active: false in payload must NOT deactivate profile
    admin_client.put(
        "/api/v1/profile/",
        json={"first_name": "Active", "last_name": "User", "is_active": False},
    )
    res = admin_client.get("/api/v1/profile/")
    assert res.status_code == 200
    assert res.json()["is_active"] is True


def test_delete_profile_soft_delete(admin_client, client):
    # 1. Create profile
    admin_client.put(
        "/api/v1/profile/",
        json={"first_name": "Soft", "last_name": "Delete"},
    )
    assert client.get("/api/v1/profile/").status_code == 200

    # 2. Soft delete via DELETE /api/v1/profile/
    delete_res = admin_client.delete("/api/v1/profile/")
    assert delete_res.status_code == 204

    # 3. Public GET returns 404
    assert client.get("/api/v1/profile/").status_code == 404

    # 4. Upsert reactivates singleton
    upsert_res = admin_client.put(
        "/api/v1/profile/",
        json={"first_name": "Soft", "last_name": "Delete", "hero_title": "Reborn"},
    )
    assert upsert_res.status_code == 200
    assert upsert_res.json()["is_active"] is True
    assert client.get("/api/v1/profile/").status_code == 200


def test_delete_profile_unauthorized(client):
    assert client.delete("/api/v1/profile/").status_code == 401


def test_delete_profile_not_found(admin_client):
    # No profile created yet
    res = admin_client.delete("/api/v1/profile/")
    assert res.status_code == 404


def test_delete_profile_image(admin_client):
    # 1. Create profile and upload image
    admin_client.put(
        "/api/v1/profile/", json={"first_name": "Test", "last_name": "User"}
    )
    files = {"file": ("test_pic.jpg", b"fake image bytes", "image/jpeg")}
    upload_res = admin_client.post("/api/v1/profile/upload-image", files=files)
    assert upload_res.status_code == 200
    img_url = upload_res.json()["image_url"]
    assert img_url is not None

    # Check file exists on disk
    rel_path = img_url[len(settings.MEDIA_URL) :].lstrip("/")
    file_on_disk = Path(settings.MEDIA_ROOT) / rel_path
    assert file_on_disk.exists()

    # 2. Delete profile image
    del_res = admin_client.delete("/api/v1/profile/image")
    assert del_res.status_code == 204

    # 3. Verify DB image_url is None and file was unlinked
    get_res = admin_client.get("/api/v1/profile/")
    assert get_res.status_code == 200
    assert get_res.json()["image_url"] is None
    assert not file_on_disk.exists()

    # 4. Idempotent deletion on profile with no image returns 204
    second_del = admin_client.delete("/api/v1/profile/image")
    assert second_del.status_code == 204


def test_delete_profile_image_unauthorized(client):
    assert client.delete("/api/v1/profile/image").status_code == 401


def test_delete_profile_image_not_found(admin_client):
    # No profile created yet
    res = admin_client.delete("/api/v1/profile/image")
    assert res.status_code == 404
