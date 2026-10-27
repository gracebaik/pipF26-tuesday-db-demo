"""Flask app that lists student names from Postgres."""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from flask import Flask, render_template

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

app = Flask(__name__)


def get_student_names() -> list[str]:
    database_url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get(
        "DATABASE_URL"
    )
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing from .env")

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM students ORDER BY name")
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


@app.get("/")
def index():
    names = get_student_names()
    return render_template("index.html", names=names)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
