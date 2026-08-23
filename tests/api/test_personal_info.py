from app.core import settings


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
    }
    response = admin_client.put("/api/v1/profile/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
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
