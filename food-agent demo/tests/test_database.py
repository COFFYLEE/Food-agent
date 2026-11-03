from datetime import date

from food_agent.database import clear_meals, daily_totals, delete_meal, get_meals, save_meal
from food_agent.schemas import FoodItem, MealRecord, NutritionTotals


def test_save_and_read_meal(tmp_path):
    path = tmp_path / "test.db"
    record = MealRecord(
        record_date=date(2026, 9, 2),
        meal_type="breakfast",
        original_text="两个鸡蛋",
        foods=[FoodItem(name="鸡蛋", estimated_grams=100)],
        totals=NutritionTotals(calories=143, protein=12.6),
    )
    saved_id = save_meal(record, path)
    records = get_meals(date(2026, 9, 2), path=path)
    assert saved_id == 1
    assert records[0].original_text == "两个鸡蛋"
    assert daily_totals(records).calories == 143


def test_delete_one_meal(tmp_path):
    path = tmp_path / "delete.db"
    record = MealRecord(
        record_date=date(2026, 9, 2),
        meal_type="breakfast",
        original_text="一个鸡蛋",
        foods=[FoodItem(name="鸡蛋", estimated_grams=50)],
        totals=NutritionTotals(calories=71.5),
    )
    meal_id = save_meal(record, path)
    assert delete_meal(meal_id, path=path) is True
    assert delete_meal(meal_id, path=path) is False
    assert get_meals(date(2026, 9, 2), path=path) == []


def test_clear_only_selected_date(tmp_path):
    path = tmp_path / "clear.db"
    for record_date in (date(2026, 9, 2), date(2026, 9, 3)):
        save_meal(
            MealRecord(
                record_date=record_date,
                meal_type="lunch",
                original_text="米饭",
                foods=[FoodItem(name="米饭", estimated_grams=200)],
                totals=NutritionTotals(calories=260),
            ),
            path,
        )
    assert clear_meals(date(2026, 9, 2), path=path) == 1
    assert len(get_meals(date(2026, 9, 3), path=path)) == 1
