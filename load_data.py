"""Create schema and load class_dataset.csv into Railway Postgres."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schema.sql"
CSV_CANDIDATES = [
    ROOT / "data" / "class_dataset.csv",
    ROOT / "class_dataset.csv",
]
TABLES = [
    "students",
    "tools",
    "availability_slots",
    "student_tools",
    "student_availability",
]


def split_values(raw: str | None) -> list[str]:
    if not raw:
        return []
    seen: set[str] = set()
    values: list[str] = []
    for part in raw.split(";"):
        value = part.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values


def find_csv() -> Path:
    for path in CSV_CANDIDATES:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "Could not find class_dataset.csv in data/ or the project root."
    )


def get_or_create_lookup(cur, table: str, name: str, cache: dict[str, int]) -> int:
    if name in cache:
        return cache[name]
    cur.execute(
        f"INSERT INTO {table} (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
        (name,),
    )
    lookup_id = cur.fetchone()[0]
    cache[name] = lookup_id
    return lookup_id


def main() -> None:
    load_dotenv(ROOT / ".env")
    database_url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get(
        "DATABASE_URL"
    )
    if not database_url:
        raise SystemExit(
            "DATABASE_URL is missing. Put the Railway public Postgres URL in .env and try again."
        )

    csv_path = find_csv()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = psycopg2.connect(database_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)

                tool_ids: dict[str, int] = {}
                slot_ids: dict[str, int] = {}

                with csv_path.open(newline="", encoding="utf-8") as handle:
                    for row in csv.DictReader(handle):
                        cur.execute(
                            """
                            INSERT INTO students (
                                netid, name, school_year, intro_programming,
                                skill_programming, skill_data_stats,
                                skill_frontend_design, skill_business_pitch,
                                working_style, interests, semester_goal, submitted_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING student_id
                            """,
                            (
                                row["netid"].strip(),
                                row["name"].strip(),
                                row["school_year"].strip() or None,
                                row["intro_programming"].strip() or None,
                                int(row["skill_programming"]),
                                int(row["skill_data_stats"]),
                                int(row["skill_frontend_design"]),
                                int(row["skill_business_pitch"]),
                                row["working_style"] or None,
                                row["interests"] or None,
                                row["semester_goal"] or None,
                                row["submitted_at"].strip() or None,
                            ),
                        )
                        student_id = cur.fetchone()[0]

                        for tool in split_values(row.get("tools")):
                            tool_id = get_or_create_lookup(cur, "tools", tool, tool_ids)
                            cur.execute(
                                """
                                INSERT INTO student_tools (student_id, tool_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                                """,
                                (student_id, tool_id),
                            )

                        for slot in split_values(row.get("availability")):
                            slot_id = get_or_create_lookup(
                                cur, "availability_slots", slot, slot_ids
                            )
                            cur.execute(
                                """
                                INSERT INTO student_availability (student_id, slot_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                                """,
                                (student_id, slot_id),
                            )

                print("Row counts:")
                for table in TABLES:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    print(f"  {table}: {cur.fetchone()[0]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
