# Quick Note

A single-page notes app: write a note in the browser, it is sent to a Python
backend, saved in a SQLite database, and shown back on the same page. Refresh
or restart the server and the notes are still there.

## What it demonstrates

The full request → response → storage loop:

1. The browser builds a JSON request (`POST /api/notes`).
2. Flask receives it, validates it, and writes a row into SQLite.
3. Flask sends back the saved note as JSON.
4. The page renders that note in the list without a reload.

## Requirements

- Python 3.9 or newer
- Flask (`pip install -r requirements.txt`)

## Run it

```bash
cd noteapp
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>.

The first run creates `notes.db` in the same folder. Delete that file to start
from an empty list.

## Files

| File | What it does |
| --- | --- |
| `app.py` | Flask server: page route, JSON API, SQLite access |
| `templates/index.html` | The whole front end — markup, CSS and JavaScript in one page |
| `test_app.py` | 18 automated checks of the backend (no browser needed) |
| `requirements.txt` | The one dependency |

## API

| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| `GET` | `/` | – | the page |
| `GET` | `/api/notes` | – | `{"notes": [...], "count": n}`, newest first |
| `POST` | `/api/notes` | `{"content": "..."}` | `201` with `{"note": {...}}` |
| `PUT` | `/api/notes/<id>` | `{"content": "..."}` | `200` with the updated note |
| `DELETE` | `/api/notes/<id>` | – | `200` with `{"deleted": <id>}` |

Errors come back as `{"error": "..."}` with status `400` (blank or too long) or
`404` (no such note).

## Database

```sql
CREATE TABLE notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL,   -- ISO-8601 UTC
    updated_at TEXT NOT NULL
);
```

A connection is opened per request and closed when the request ends, so no
connection is shared between threads.

## Tests

```bash
python test_app.py
```

Runs the app in-process against a temporary database and checks create, list,
validation, edit, delete and on-disk persistence.

## Things worth trying next

- Add a search box that filters the list.
- Add user accounts so each person sees only their own notes.
- Swap SQLite for PostgreSQL when you need more than one server.
