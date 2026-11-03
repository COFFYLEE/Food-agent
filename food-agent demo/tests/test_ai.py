import json

from food_agent.ai import provider_status


def test_explicit_local_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "local")
    provider, label = provider_status()
    assert provider == "local"
    assert "本地规则" in label


def test_schema_example_is_valid_json():
    example = {
        "meal_type": "lunch",
        "foods": [
            {
                "name": "米饭",
                "amount": 1,
                "unit": "碗",
                "estimated_grams": 200,
                "confidence": 0.8,
            }
        ],
        "needs_clarification": False,
        "clarification_question": None,
    }
    assert json.loads(json.dumps(example))["foods"][0]["name"] == "米饭"
