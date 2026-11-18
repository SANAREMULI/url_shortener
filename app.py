from contextlib import contextmanager
from pathlib import Path
import random
import string
import sqlite3
from collections.abc import Generator
from flask import Flask, request, redirect

app = Flask(__name__)
DATABASE_PATH = Path(__file__).resolve().with_name("urls.db")


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        with connection:
            yield connection
    finally:
        connection.close()

# Create the table the first time the program runs
with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE,
            original_url TEXT
        )
    """)

# Make a random 6-character code like "aB3x9Q"
def make_code():
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(6))

# HOME PAGE: shows a simple form
@app.route("/")
def home():
    return """
        <h2>URL Shortener</h2>
        <form action="/shorten" method="post">
            <input type="text" name="url" placeholder="Paste long link here" size="50">
            <button type="submit">Shorten</button>
        </form>
    """

# JOB 1: take the long link, save it, show the short link
@app.route("/shorten", methods=["POST"])
def shorten():
    long_url = request.form["url"]

    # Basic check: the link must start with http:// or https://
    if not long_url.startswith(("http://", "https://")):
        return "Please enter a valid link starting with http:// or https://"

    code = make_code()
    with get_db() as db:
        db.execute("INSERT INTO urls (short_code, original_url) VALUES (?, ?)",
                   (code, long_url))

    short_link = request.host_url + code
    return f'Your short link: <a href="{short_link}">{short_link}</a>'

# JOB 2: take a code, find the long link, send the visitor there
@app.route("/<code>")
def go_to_link(code):
    with get_db() as db:
        row = db.execute("SELECT original_url FROM urls WHERE short_code = ?",
                         (code,)).fetchone()
    if row:
        return redirect(row[0])
    return "Sorry, that link was not found.", 404

if __name__ == "__main__":
    app.run(debug=True)