"""Smoke test for the Quick Note backend.

Runs the Flask app in-process against a throwaway database, so no server or
browser is needed:

    python test_app.py
"""

import json
import os
import tempfile

import app as noteapp

tmpdir = tempfile.mkdtemp()
noteapp.DB_PATH = os.path.join(tmpdir, "test_notes.db")
noteapp.init_db()

client = noteapp.app.test_client()
passed = 0


def check(label, condition, detail=""):
    global passed
    if not condition:
        raise AssertionError(f"FAIL: {label} {detail}")
    passed += 1
    print(f"  ok  {label}")


print("Quick Note backend test")

# 1. the page loads
res = client.get("/")
check("GET / returns the page", res.status_code == 200 and b"Quick Note" in res.data)

# 2. empty database
res = client.get("/api/notes")
check("GET /api/notes on empty db", res.status_code == 200 and res.get_json()["count"] == 0)

# 3. create a note
res = client.post("/api/notes", json={"content": "Buy filter coffee"})
created = res.get_json()["note"]
check("POST /api/notes returns 201", res.status_code == 201, res.status_code)
check("created note has an id and content",
      created["id"] == 1 and created["content"] == "Buy filter coffee")
check("created note has a timestamp", bool(created["created_at"]))

# 4. it is persisted and listed
res = client.get("/api/notes")
body = res.get_json()
check("note is listed after saving", body["count"] == 1 and body["notes"][0]["content"] == "Buy filter coffee")

# 5. empty content is rejected
res = client.post("/api/notes", json={"content": "   "})
check("blank note is rejected with 400", res.status_code == 400)
check("rejection carries an error message", "error" in res.get_json())

# 6. too long is rejected
res = client.post("/api/notes", json={"content": "x" * (noteapp.MAX_LENGTH + 1)})
check("over-long note is rejected with 400", res.status_code == 400)

# 7. newest note comes first
client.post("/api/notes", json={"content": "Second note"})
notes = client.get("/api/notes").get_json()["notes"]
check("notes are newest first", [n["content"] for n in notes] == ["Second note", "Buy filter coffee"])

# 8. edit
res = client.put("/api/notes/1", json={"content": "Buy filter coffee and milk"})
check("PUT /api/notes/1 updates", res.status_code == 200 and
      res.get_json()["note"]["content"] == "Buy filter coffee and milk")
check("updated note keeps its id", res.get_json()["note"]["id"] == 1)

# 9. edit of a missing note
res = client.put("/api/notes/999", json={"content": "ghost"})
check("PUT on a missing note returns 404", res.status_code == 404)

# 10. delete
res = client.delete("/api/notes/1")
check("DELETE /api/notes/1 returns 200", res.status_code == 200)
notes = client.get("/api/notes").get_json()["notes"]
check("deleted note is gone", [n["content"] for n in notes] == ["Second note"])

# 11. delete again
res = client.delete("/api/notes/1")
check("DELETE on a missing note returns 404", res.status_code == 404)

# 12. unknown API path stays JSON
res = client.get("/api/nope")
check("unknown API path returns JSON 404", res.status_code == 404 and "error" in res.get_json())

# 13. data really is on disk (survives a new connection)
import sqlite3
with sqlite3.connect(noteapp.DB_PATH) as conn:
    rows = conn.execute("SELECT content FROM notes").fetchall()
check("note is stored in the sqlite file", [r[0] for r in rows] == ["Second note"])

print(f"\nAll {passed} checks passed.")
