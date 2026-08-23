from app.core import settings


def test_get_empty_projects(client):
    response = client.get("/api/v1/projects/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_project(admin_client):
    payload = {
        "title": "Portfolio Web App",
        "description": "My personal portfolio built with React and FastAPI",
        "tech_stack": ["React", "FastAPI", "SQLite"],
        "github_url": "https://github.com/itzik/portfolio",
    }
    response = admin_client.post("/api/v1/projects/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Portfolio Web App"
    assert data["tech_stack"] == ["React", "FastAPI", "SQLite"]
    assert data["display_order"] == 1  # Should auto-increment to 1
    assert "id" in data


def test_get_project_by_id(client, admin_client):
    # Create project first
    create_res = admin_client.post(
        "/api/v1/projects/", json={"title": "Test Project", "description": "Desc"}
    )
    project_id = create_res.json()["id"]

    # Fetch it
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Project"


def test_update_project(admin_client):
    # Create project
    create_res = admin_client.post(
        "/api/v1/projects/",
        json={
            "title": "Old Title",
            "description": "Old Desc",
            "tech_stack": ["Python"],
        },
    )
    project_id = create_res.json()["id"]

    # Patch it (Partial update)
    patch_res = admin_client.patch(
        f"/api/v1/projects/{project_id}",
        json={"title": "New Title", "tech_stack": ["Python", "Rust"]},
    )

    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["title"] == "New Title"
    assert data["description"] == "Old Desc"  # Should remain unchanged
    assert data["tech_stack"] == ["Python", "Rust"]


def test_delete_project(admin_client):
    # Create project
    create_res = admin_client.post(
        "/api/v1/projects/", json={"title": "Delete Me", "description": "Desc"}
    )
    project_id = create_res.json()["id"]

    # Delete it
    delete_res = admin_client.delete(f"/api/v1/projects/{project_id}")
    assert delete_res.status_code == 204

    # Verify it's gone
    get_res = admin_client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 404


def test_create_project_unauthorized(client):
    response = client.post("/api/v1/projects/", json={"title": "Hacked"})
    assert response.status_code == 401


def test_upload_project_image(admin_client):
    """Test successful image upload for an existing project."""
    # Create a project first so we have a valid ID
    create_res = admin_client.post(
        "/api/v1/projects/",
        json={
            "title": "Image Upload Test Project",
            "description": "Testing file uploads",
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
