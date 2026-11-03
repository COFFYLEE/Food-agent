from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from food_agent.schemas import FoodItem, MealRecord, NutritionTotals

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "food_agent.db"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(path: Path = DB_PATH) -> None:
    with connect(path) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '演示用户',
                goal TEXT NOT NULL DEFAULT '改善饮食',
                allergies TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                record_date TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                original_text TEXT NOT NULL,
                foods_json TEXT NOT NULL,
                totals_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT OR IGNORE INTO users (id) VALUES (1);
            """
        )


def save_meal(record: MealRecord, path: Path = DB_PATH) -> int:
    init_db(path)
    with connect(path) as db:
        cursor = db.execute(
            """
            INSERT INTO meals
                (user_id, record_date, meal_type, original_text, foods_json, totals_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.user_id,
                record.record_date.isoformat(),
                record.meal_type,
                record.original_text,
                json.dumps([item.model_dump() for item in record.foods], ensure_ascii=False),
                record.totals.model_dump_json(),
            ),
        )
        return int(cursor.lastrowid)


def get_meals(record_date: date, user_id: int = 1, path: Path = DB_PATH) -> list[MealRecord]:
    init_db(path)
    with connect(path) as db:
        rows = db.execute(
            "SELECT * FROM meals WHERE user_id = ? AND record_date = ? ORDER BY id",
            (user_id, record_date.isoformat()),
        ).fetchall()
    return [
        MealRecord(
            id=row["id"],
            user_id=row["user_id"],
            record_date=date.fromisoformat(row["record_date"]),
            meal_type=row["meal_type"],
            original_text=row["original_text"],
            foods=[FoodItem.model_validate(item) for item in json.loads(row["foods_json"])],
            totals=NutritionTotals.model_validate_json(row["totals_json"]),
        )
        for row in rows
    ]


def daily_totals(records: list[MealRecord]) -> NutritionTotals:
    total = NutritionTotals()
    for record in records:
        total = total.add(record.totals)
    return NutritionTotals(**{key: round(value, 1) for key, value in total.model_dump().items()})


def delete_meal(meal_id: int, user_id: int = 1, path: Path = DB_PATH) -> bool:
    """Delete one meal owned by the user and report whether a row changed."""
    init_db(path)
    with connect(path) as db:
        cursor = db.execute(
            "DELETE FROM meals WHERE id = ? AND user_id = ?",
            (meal_id, user_id),
        )
        return cursor.rowcount == 1


def clear_meals(record_date: date, user_id: int = 1, path: Path = DB_PATH) -> int:
    """Delete all meals for one user on one date and return the number removed."""
    init_db(path)
    with connect(path) as db:
        cursor = db.execute(
            "DELETE FROM meals WHERE user_id = ? AND record_date = ?",
            (user_id, record_date.isoformat()),
        )
        return cursor.rowcount
