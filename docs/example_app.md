# The example app

Every template's `example/` builds this same program, so templates can be compared file by file. Only the
architecture differs; the behavior, texts and tests are the same.

## What it does

Notes and their statistics, with two adapters over the same use cases:

- **CLI** (`main.py`, Typer): `notes add TEXT`, `notes list`, `notes edit ID TEXT`, `notes delete ID`,
  `statistics show`. Blank text is refused with "Note text must not be empty"; failures go to stderr with exit code 1;
  an empty list prints "No notes yet".
- **HTTP** (`api.py`, FastAPI): `GET /notes`, `POST /notes` (201), `PUT /notes/{id}`, `DELETE /notes/{id}` (204);
  refused text → 422, unknown id on delete → 404.
- **Statistics**: notes, words, added today, edited (a note whose `updated_at` is not its `created_at`).

## Where the data lives

`core/data/data_sources/` has a `DatabaseDataSource` interface (tables of rows keyed by `id`: `rows`, `insert`,
`update`, `delete`; an unknown or duplicate id raises) with two implementations: `JsonFileDatabaseDataSource`
(the app; the path comes from `EXAMPLE_APP_DATABASE`, default `notes.json`) and `InMemoryDatabaseDataSource` (tests;
optional `latency`). `core/data/services/clock_service.py` is the only source of "now".

Both features read the same `notes` table through their own data sources, models and repositories — features never
import each other:

| Feature | Data source | Model | Entity | Use cases |
|---|---|---|---|---|
| `notes` | `DatabaseNotesDataSource` (UUID v4 ids, timestamps from the clock) | `NoteModel` (row ↔ model ↔ `Note`) | `Note` | `ListNotes`, `AddNote`, `UpdateNote` (both trim and refuse blank text), `DeleteNote` |
| `statistics` | `DatabaseStatisticsDataSource` (reads `notes`) | `NoteFactsModel` | `NoteFacts`, `NotesStatistics.of(facts, now=)` | `GetNotesStatistics` |

`StatisticsRepositoryImpl` orchestrates a data source and a service (the clock) — the data design of the template.

## Tests (every template)

- core: `Result` matching; both database data sources (insert/update/delete, unknown and duplicate ids, the JSON file
  kept between instances);
- domain: `AddNote` / `UpdateNote` validation with a fake repository; `NotesStatistics.of` counts;
- data: `NoteModel` round trips; notes repository (order, update, failures); statistics repository (counts, failure);
- presentation: the notes CLI flow, the notes HTTP flow, `statistics show`.
