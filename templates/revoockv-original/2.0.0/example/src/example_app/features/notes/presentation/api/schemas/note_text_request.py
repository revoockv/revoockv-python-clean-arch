"""Note text request body."""

from pydantic import BaseModel


class NoteTextRequest(BaseModel):
    """Text posted to ``POST /notes`` and ``PUT /notes/{note_id}``."""

    text: str
