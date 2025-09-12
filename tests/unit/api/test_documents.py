import io
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from uuid import uuid4
from types import SimpleNamespace

from fastapi import FastAPI

import app.api.documents as documents_api
from app.api.documents import documents, get_documents_service

# ---- PATCH DEPENDENCIES ----


def fake_token_to_user():
    return uuid4()


@pytest.fixture
def client():
    app = FastAPI()
    service = MagicMock()

    app.dependency_overrides[get_documents_service] = lambda: service
    app.dependency_overrides[documents_api.token_to_user] = fake_token_to_user

    app.include_router(documents)
    return TestClient(app)


@pytest.fixture
def mock_service(client):
    return client.app.dependency_overrides[get_documents_service]()


# ---- HELPERS ----


class FakeDocument:
    def __init__(self, id, filename):
        self.id = id
        self.filename = filename
        self.content_type = "application/pdf"
        self.size_bytes = 123
        self.storage_path = "/tmp/file.pdf"
        self.metadata = {"author": "tester"}


# ---- TESTS ----


def test_upload_document(client, mock_service):
    project_id = uuid4()
    doc = FakeDocument(uuid4(), "plik.txt")
    mock_service.upload_document = AsyncMock(return_value=doc)

    files = {"file": ("plik.txt", io.BytesIO(b"abc"), "text/plain")}
    data = {"project_id": str(project_id)}

    response = client.post("/documents/", files=files, data=data)

    assert response.status_code == 201
    assert response.json()["filename"] == "plik.txt"
    mock_service.upload_document.assert_awaited_once()


def test_download_document(client, mock_service):
    doc = FakeDocument(uuid4(), "plik.pdf")
    fake_file = io.BytesIO(b"content")
    mock_service.download_document = AsyncMock(return_value=(fake_file, doc))

    response = client.get(f"/documents/{doc.id}")

    assert response.status_code == 200
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="{doc.filename}"'
    )
    body = b"".join(response.iter_bytes())
    assert body == b"content"
    mock_service.download_document.assert_awaited_once()


def test_update_document(client, mock_service):
    doc = FakeDocument(uuid4(), "updated.pdf")
    mock_service.update_document.return_value = doc

    response = client.put(f"/documents/{doc.id}", json={"filename": "updated.pdf"})

    assert response.status_code == 200
    assert response.json()["filename"] == "updated.pdf"
    mock_service.update_document.assert_called_once()


def test_delete_document(client, mock_service):
    doc_id = uuid4()
    mock_service.delete_document = AsyncMock(return_value=None)

    response = client.delete(f"/documents/{doc_id}")

    assert response.status_code == 204
    mock_service.delete_document.assert_awaited_once()
