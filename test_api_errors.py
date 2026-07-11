from fastapi.testclient import TestClient

from main import MAX_UPLOAD_BYTES, app


client = TestClient(app)


def test_rejects_empty_file():
    response = client.post(
        "/analyze",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400


def test_rejects_unsupported_extension():
    response = client.post(
        "/analyze",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 415


def test_rejects_corrupted_image():
    response = client.post(
        "/analyze",
        files={"file": ("broken.jpg", b"not a jpeg", "image/jpeg")},
    )
    assert response.status_code == 422


def test_rejects_oversized_upload():
    response = client.post(
        "/analyze",
        files={
            "file": (
                "large.png",
                b"0" * (MAX_UPLOAD_BYTES + 1),
                "image/png",
            )
        },
    )
    assert response.status_code == 413
