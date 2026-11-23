"""User-facing text of the notes failures."""

from example_app.features.notes.domain.entities.note_failure import NoteFailure


class NoteFailureText:
    """The text of every ``NoteFailure``; a new member without a text fails mypy."""

    _EMPTY_TEXT = "Note text must not be empty"
    _NOT_FOUND = "There is no such note"
    _STORAGE = "The notes could not be read or saved"

    @classmethod
    def of(cls, failure: NoteFailure) -> str:
        """Return the text that tells the user about ``failure``."""
        match failure:
            case NoteFailure.EMPTY_TEXT:
                return cls._EMPTY_TEXT
            case NoteFailure.NOT_FOUND:
                return cls._NOT_FOUND
            case NoteFailure.STORAGE:
                return cls._STORAGE
