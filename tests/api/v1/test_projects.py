from pathlib import Path

from app.core import settings


def test_get_empty_projects(client):
    response = client.get("/api/v1/projects/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_project(admin_client):
    payload = {
        "title": "Portfolio Web App",
        "summary": "My personal portfolio built with React and FastAPI",
        "content": "# Deep Dive\nDetailed markdown case study.",
        "tags": ["React", "FastAPI", "PostgreSQL"],
        "github_url": "https://github.com/itzik/portfolio",
    }
    response = admin_client.post("/api/v1/projects/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Portfolio Web App"
    assert data["summary"] == "My personal portfolio built with React and FastAPI"
    assert data["content"] == "# Deep Dive\nDetailed markdown case study."
    assert data["tags"] == ["React", "FastAPI", "PostgreSQL"]
    assert data["display_order"] == 1  # Should auto-increment to 1
    assert "id" in data


def test_create_project_summary_too_long(admin_client):
    payload = {
        "title": "Invalid Project",
        "summary": "A" * 301,  # Max length is 300
    }
    response = admin_client.post("/api/v1/projects/", json=payload)
    assert response.status_code == 422


def test_get_project_by_id(client, admin_client):
    # Create project first
    create_res = admin_client.post(
        "/api/v1/projects/",
        json={
            "title": "Test Project",
            "summary": "Project summary",
            "content": "Rich content description",
        },
    )
    project_id = create_res.json()["id"]

    # Fetch it
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Project"
    assert data["summary"] == "Project summary"
    assert data["content"] == "Rich content description"


def test_update_project(admin_client):
    # Create project
    create_res = admin_client.post(
        "/api/v1/projects/",
        json={
            "title": "Old Title",
            "summary": "Old Summary",
            "content": "Old Content",
            "tags": ["Python"],
        },
    )
    project_id = create_res.json()["id"]

    # Patch it (Partial update)
    patch_res = admin_client.patch(
        f"/api/v1/projects/{project_id}",
        json={"title": "New Title", "tags": ["Python", "Rust"]},
    )

    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["title"] == "New Title"
    assert data["summary"] == "Old Summary"  # Should remain unchanged
    assert data["content"] == "Old Content"  # Should remain unchanged
    assert data["tags"] == ["Python", "Rust"]


def test_delete_project(admin_client):
    # Create project
    create_res = admin_client.post(
        "/api/v1/projects/", json={"title": "Delete Me", "summary": "To be deleted"}
    )
    project_id = create_res.json()["id"]

    # Delete it
    delete_res = admin_client.delete(f"/api/v1/projects/{project_id}")
    assert delete_res.status_code == 204

    # Verify it's gone
    get_res = admin_client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 404


def test_create_project_unauthorized(client):
    response = client.post("/api/v1/projects/", json={"title": "Hacked", "summary": "Hack"})
    assert response.status_code == 401


def test_upload_project_image(admin_client):
    """Test successful image upload for an existing project."""
    # Create a project first so we have a valid ID
    create_res = admin_client.post(
        "/api/v1/projects/",
        json={
            "title": "Image Upload Test Project",
            "summary": "Testing file uploads",
        },
    )
    project_id = create_res.json()["id"]

    # Mock a file upload (simulate a PNG file in memory)
    file_content = b"fake project image bytes"
    files = {"file": ("project_pic.png", file_content, "image/png")}

    # Send the upload request
    response = admin_client.post(
        f"/api/v1/projects/{project_id}/upload-image", files=files
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["image_url"] is not None
    assert f"{settings.MEDIA_URL}/projects/" in data["image_url"]
    assert data["image_url"].endswith(".png")


def test_upload_project_image_not_found(admin_client):
    """Test uploading an image to a non-existent project returns 404."""
    files = {"file": ("test.jpg", b"fake bytes", "image/jpeg")}

    # Send request to an ID that we know doesn't exist (e.g., 9999)
    response = admin_client.post("/api/v1/projects/9999/upload-image", files=files)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_project_image(admin_client):
    """Test deleting an image associated with an existing project."""
    # 1. Create project
    create_res = admin_client.post(
        "/api/v1/projects/",
        json={
            "title": "Delete Image Project",
            "summary": "Testing image deletion",
        },
    )
    project_id = create_res.json()["id"]

    # 2. Upload image
    files = {"file": ("proj_pic.png", b"fake project bytes", "image/png")}
    upload_res = admin_client.post(
        f"/api/v1/projects/{project_id}/upload-image", files=files
    )
    assert upload_res.status_code == 200
    img_url = upload_res.json()["image_url"]
    assert img_url is not None

    rel_path = img_url[len(settings.MEDIA_URL) :].lstrip("/")
    file_on_disk = Path(settings.MEDIA_ROOT) / rel_path
    assert file_on_disk.exists()

    # 3. Delete image
    delete_res = admin_client.delete(f"/api/v1/projects/{project_id}/image")
    assert delete_res.status_code == 204

    # 4. Verify DB image_url is None and file was unlinked
    get_res = admin_client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 200
    assert get_res.json()["image_url"] is None
    assert not file_on_disk.exists()

    # 5. Idempotent deletion on project with no image returns 204
    second_delete = admin_client.delete(f"/api/v1/projects/{project_id}/image")
    assert second_delete.status_code == 204


def test_delete_project_image_unauthorized(client):
    """Test unauthenticated request to delete project image returns 401."""
    response = client.delete("/api/v1/projects/1/image")
    assert response.status_code == 401


def test_delete_project_image_not_found(admin_client):
    """Test deleting image for non-existent project returns 404."""
    response = admin_client.delete("/api/v1/projects/9999/image")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
