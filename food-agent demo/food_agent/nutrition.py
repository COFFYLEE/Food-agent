from __future__ import annotations

import csv
from pathlib import Path

from food_agent.schemas import FoodItem, NutritionTotals

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "nutrition.csv"


def load_foods(path: Path = DATA_FILE) -> dict[str, dict[str, float | str]]:
    foods: dict[str, dict[str, float | str]] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            entry: dict[str, float | str] = {"name": row["name"], "aliases": row["aliases"]}
            for key in ("calories", "protein", "carbs", "fat", "fiber"):
                entry[key] = float(row[key])
            for alias in [row["name"], *row["aliases"].split("|")]:
                foods[alias.strip().lower()] = entry
    return foods


def find_food(name: str, foods: dict | None = None) -> dict | None:
    foods = foods or load_foods()
    normalized = name.strip().lower()
    if normalized in foods:
        return foods[normalized]
    for alias, entry in foods.items():
        if alias in normalized or normalized in alias:
            return entry
    return None


def calculate_item(item: FoodItem, foods: dict | None = None) -> NutritionTotals:
    entry = find_food(item.name, foods)
    if not entry or not item.estimated_grams:
        return NutritionTotals()
    ratio = item.estimated_grams / 100
    return NutritionTotals(
        calories=round(float(entry["calories"]) * ratio, 1),
        protein=round(float(entry["protein"]) * ratio, 1),
        carbs=round(float(entry["carbs"]) * ratio, 1),
        fat=round(float(entry["fat"]) * ratio, 1),
        fiber=round(float(entry["fiber"]) * ratio, 1),
    )


def calculate_meal(items: list[FoodItem]) -> NutritionTotals:
    foods = load_foods()
    total = NutritionTotals()
    for item in items:
        total = total.add(calculate_item(item, foods))
    return NutritionTotals(**{key: round(value, 1) for key, value in total.model_dump().items()})

