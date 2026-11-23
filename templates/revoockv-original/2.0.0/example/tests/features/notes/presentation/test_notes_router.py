from http import HTTPStatus
from pathlib import Path

from fastapi.testclient import TestClient

from example_app.api import create_app


def test_notes_api(database_file: Path) -> None:
    with TestClient(create_app()) as client:
        assert client.get("/notes").json() == []

        created = client.post("/notes", json={"text": " Buy milk "})
        assert created.status_code == HTTPStatus.CREATED
        note = created.json()
        assert note["text"] == "Buy milk"

        updated = client.put(f"/notes/{note['id']}", json={"text": "Buy bread"})
        assert updated.json()["text"] == "Buy bread"

        assert client.delete(f"/notes/{note['id']}").status_code == HTTPStatus.NO_CONTENT
        missing = client.delete(f"/notes/{note['id']}")
        assert missing.status_code == HTTPStatus.NOT_FOUND
        assert missing.json()["detail"] == "There is no such note"


def test_blank_text_is_422(database_file: Path) -> None:
    with TestClient(create_app()) as client:
        response = client.post("/notes", json={"text": ""})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["detail"] == "Note text must not be empty"
