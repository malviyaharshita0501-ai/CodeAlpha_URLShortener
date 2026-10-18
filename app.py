from flask import Flask, request, redirect, render_template, jsonify
import sqlite3
import string
import secrets
from urllib.parse import urlparse

app = Flask(__name__)
DATABASE = "urls.db"


def initialize_database():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT UNIQUE NOT NULL,
                original_url TEXT NOT NULL
            )
        """)


def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.hostname)
            and "." in parsed.hostname
        )
    except ValueError:
        return False


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/shorten", methods=["POST"])
def shorten_url():
    data = request.get_json(silent=True) or {}
    original_url = data.get("url", "").strip()

    if not is_valid_url(original_url):
        return jsonify({"error": "Please enter a valid URL."}), 400

    with sqlite3.connect(DATABASE) as conn:
        existing = conn.execute(
            "SELECT short_code FROM urls WHERE original_url = ?",
            (original_url,)
        ).fetchone()

        if existing:
            short_code = existing[0]
        else:
            while True:
                short_code = "".join(
                    secrets.choice(string.ascii_letters + string.digits)
                    for _ in range(6)
                )

                try:
                    conn.execute(
                        "INSERT INTO urls (short_code, original_url) VALUES (?, ?)",
                        (short_code, original_url)
                    )
                    break
                except sqlite3.IntegrityError:
                    continue

    return jsonify({
        "original_url": original_url,
        "short_url": request.host_url + short_code,
        "short_code": short_code
    })


@app.route("/<short_code>")
def redirect_url(short_code):
    with sqlite3.connect(DATABASE) as conn:
        result = conn.execute(
            "SELECT original_url FROM urls WHERE short_code = ?",
            (short_code,)
        ).fetchone()

    if result is None:
        return jsonify({"error": "Short URL not found."}), 404

    return redirect(result[0])


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)