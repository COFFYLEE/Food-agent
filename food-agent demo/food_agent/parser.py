from __future__ import annotations

import re

from food_agent.nutrition import load_foods
from food_agent.schemas import FoodItem, ParsedMeal

MEAL_WORDS = {
    "早餐": "breakfast",
    "早饭": "breakfast",
    "午餐": "lunch",
    "午饭": "lunch",
    "晚餐": "dinner",
    "晚饭": "dinner",
    "零食": "snack",
}

PORTIONS = {
    "鸡蛋": (50, "个"),
    "牛奶": (250, "杯"),
    "米饭": (200, "碗"),
    "鸡胸肉": (150, "份"),
    "鸡腿": (150, "个"),
    "西兰花": (80, "份"),
    "番茄": (120, "个"),
    "苹果": (180, "个"),
    "香蕉": (120, "根"),
    "牛肉面": (500, "碗"),
    "可乐": (330, "罐"),
}

CHINESE_NUMBERS = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5}


def infer_meal_type(text: str, fallback: str = "meal") -> str:
    for word, meal_type in MEAL_WORDS.items():
        if word in text:
            return meal_type
    return fallback


def _quantity_before(text: str, position: int) -> float:
    prefix = text[max(0, position - 8) : position]
    match = re.search(r"(\d+(?:\.\d+)?)\s*$", prefix)
    if match:
        return float(match.group(1))
    for word, value in CHINESE_NUMBERS.items():
        if word in prefix[-3:]:
            return float(value)
    return 1.0


def parse_meal_locally(text: str, meal_type: str | None = None) -> ParsedMeal:
    foods = load_foods()
    found: list[FoodItem] = []
    used_names: set[str] = set()
    for alias in sorted(foods, key=len, reverse=True):
        if alias not in text.lower():
            continue
        canonical = str(foods[alias]["name"])
        if canonical in used_names:
            continue
        used_names.add(canonical)
        position = text.lower().find(alias)
        quantity = _quantity_before(text, position)
        grams_per_portion, unit = PORTIONS.get(canonical, (100, "份"))
        found.append(
            FoodItem(
                name=canonical,
                amount=quantity,
                unit=unit,
                estimated_grams=grams_per_portion * quantity,
                confidence=0.65,
            )
        )

    needs_clarification = not found
    return ParsedMeal(
        meal_type=meal_type or infer_meal_type(text),
        foods=found,
        needs_clarification=needs_clarification,
        clarification_question=(
            "我还没识别出具体食物。请补充食物名称和大致分量，例如“一碗米饭和一个鸡腿”。"
            if needs_clarification
            else None
        ),
    )

