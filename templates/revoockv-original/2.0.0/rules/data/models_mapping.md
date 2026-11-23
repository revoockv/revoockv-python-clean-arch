# Models mapping (required)

Data models (DTOs) represent technology-specific shapes: JSON payloads, DB rows, ORM objects,
SDK responses. Entities represent business concepts. They are separate classes even when the
fields are identical today.

Location: `src/<package>/features/<feature>/data/models/<name>_model.py`, class `<Name>Model`.

## Rules (`model_mapping`, `import_violation`)

- `to_entity(self) -> Entity` and `@classmethod from_entity(cls, entity) -> Self` are required.
- Wire (de)serialization lives in the model too: `from_dict` / `to_dict`, `from_row`, `from_orm`, ...
- Mapping logic lives in the model class, never in repositories' callers or presentation.
- Domain never imports data models. Presentation never imports data models.
- Models are frozen dataclasses by default. Pydantic `BaseModel` is allowed in `data/models/`
  when you want validation of external payloads — the mapping methods stay the same.
- Presentation has its own schemas (`presentation/api/schemas/`) that map from entities with
  `from_entity`; never reuse data models as API schemas.

## Example

```python
@dataclass(frozen=True, slots=True)
class SongModel:
    """Song as stored in the songs API."""

    id: str
    title: str
    author_name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build the model from the API JSON."""
        return cls(id=str(data["id"]), title=str(data["title"]), author_name=str(data["author"]["name"]))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the API JSON."""
        return {"id": self.id, "title": self.title, "author": {"name": self.author_name}}

    @classmethod
    def from_entity(cls, entity: Song) -> Self:
        """Build the model from a domain entity."""
        return cls(id=entity.id, title=entity.title, author_name=entity.author)

    def to_entity(self) -> Song:
        """Map to a domain entity."""
        return Song(id=self.id, title=self.title, author=self.author_name)
```

## Three shapes of the same data

| Layer | Class | Purpose |
|---|---|---|
| domain/entities | `Song` | business concept, stdlib only |
| data/models | `SongModel` | storage / wire format, `to_entity` / `from_entity` |
| presentation/api/schemas | `SongResponse`, `AddSongRequest` | public API contract (Pydantic), `from_entity` |
