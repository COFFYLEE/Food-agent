from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class FoodItem(BaseModel):
    name: str
    amount: float | None = None
    unit: str | None = None
    estimated_grams: float | None = None
    confidence: float = Field(default=0.7, ge=0, le=1)


class ParsedMeal(BaseModel):
    meal_type: str
    foods: list[FoodItem]
    needs_clarification: bool = False
    clarification_question: str | None = None


class NutritionTotals(BaseModel):
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    fiber: float = 0

    def add(self, other: NutritionTotals) -> NutritionTotals:
        return NutritionTotals(
            calories=self.calories + other.calories,
            protein=self.protein + other.protein,
            carbs=self.carbs + other.carbs,
            fat=self.fat + other.fat,
            fiber=self.fiber + other.fiber,
        )


class MealRecord(BaseModel):
    id: int | None = None
    user_id: int = 1
    record_date: date
    meal_type: str
    original_text: str
    foods: list[FoodItem]
    totals: NutritionTotals

