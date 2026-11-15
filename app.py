"""
Quick Note - a small single-page notes app.

The browser (index.html) talks to this Flask backend over JSON.
Every note is written to a SQLite database file (notes.db) and read
back from it, so notes survive a page refresh and a server restart.

Run it with:
    python app.py
then open http://127.0.0.1:5000
"""

import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, g, jsonify, render_template, request

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "notes.db")
MAX_LENGTH = 2000

app = Flask(__name__)


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
def get_db():
    """Open one SQLite connection per request (stored on Flask's `g`)."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the table if it does not exist yet."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                content    TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def row_to_note(row):
    return {
        "id": row["id"],
        "content": row["content"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html", max_length=MAX_LENGTH)


# --------------------------------------------------------------------------
# API  (request in -> database -> JSON response out)
# --------------------------------------------------------------------------
@app.get("/api/notes")
def list_notes():
    rows = get_db().execute(
        "SELECT id, content, created_at, updated_at FROM notes ORDER BY id DESC"
    ).fetchall()
    return jsonify({"notes": [row_to_note(r) for r in rows], "count": len(rows)})


@app.post("/api/notes")
def create_note():
    payload = request.get_json(silent=True) or {}
    content = str(payload.get("content", "")).strip()

    if not content:
        return jsonify({"error": "Note cannot be empty."}), 400
    if len(content) > MAX_LENGTH:
        return jsonify({"error": f"Note is longer than {MAX_LENGTH} characters."}), 400

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db = get_db()
    cursor = db.execute(
        "INSERT INTO notes (content, created_at, updated_at) VALUES (?, ?, ?)",
        (content, now, now),
    )
    db.commit()
    row = db.execute(
        "SELECT id, content, created_at, updated_at FROM notes WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return jsonify({"note": row_to_note(row)}), 201


@app.put("/api/notes/<int:note_id>")
def update_note(note_id):
    payload = request.get_json(silent=True) or {}
    content = str(payload.get("content", "")).strip()

    if not content:
        return jsonify({"error": "Note cannot be empty."}), 400
    if len(content) > MAX_LENGTH:
        return jsonify({"error": f"Note is longer than {MAX_LENGTH} characters."}), 400

    db = get_db()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = db.execute(
        "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?",
        (content, now, note_id),
    )
    db.commit()
    if result.rowcount == 0:
        return jsonify({"error": "Note not found."}), 404

    row = db.execute(
        "SELECT id, content, created_at, updated_at FROM notes WHERE id = ?",
        (note_id,),
    ).fetchone()
    return jsonify({"note": row_to_note(row)})


@app.delete("/api/notes/<int:note_id>")
def delete_note(note_id):
    db = get_db()
    result = db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    if result.rowcount == 0:
        return jsonify({"error": "Note not found."}), 404
    return jsonify({"deleted": note_id})


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found."}), 404
    return render_template("index.html", max_length=MAX_LENGTH), 404


if __name__ == "__main__":
    init_db()
    print(f"Database file: {DB_PATH}")
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True, port=5000)
