from food_agent.nutrition import calculate_meal
from food_agent.parser import parse_meal_locally


def test_local_parser_finds_common_foods():
    meal = parse_meal_locally("午餐吃了一碗米饭、一个鸡腿和一些西兰花")
    assert meal.meal_type == "lunch"
    assert {food.name for food in meal.foods} == {"米饭", "鸡腿", "西兰花"}
    assert meal.needs_clarification is False


def test_nutrition_calculation_is_positive():
    meal = parse_meal_locally("两个鸡蛋和一杯牛奶", "breakfast")
    totals = calculate_meal(meal.foods)
    assert totals.calories > 200
    assert totals.protein > 10


def test_unknown_food_requests_clarification():
    meal = parse_meal_locally("吃了一点神秘料理")
    assert meal.needs_clarification is True

