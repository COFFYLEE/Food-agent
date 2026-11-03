from __future__ import annotations

import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from food_agent.parser import parse_meal_locally
from food_agent.schemas import NutritionTotals, ParsedMeal

load_dotenv()


def api_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def ollama_available(timeout: float = 0.25) -> bool:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    try:
        with urlopen(f"{base_url}/api/tags", timeout=timeout) as response:
            return response.status == 200
    except (OSError, URLError):
        return False


def provider_status() -> tuple[str, str]:
    requested = os.getenv("AI_PROVIDER", "auto").lower()
    if requested == "local":
        return "local", "本地规则模式"
    if requested in {"auto", "ollama"} and ollama_available():
        model = os.getenv("OLLAMA_MODEL", "qwen3:4b")
        return "ollama", f"Ollama 本地 AI · {model}"
    if requested in {"auto", "openai"} and api_available():
        model = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")
        return "openai", f"OpenAI 在线 AI · {model}"
    return "local", "本地规则模式"


def _parse_with_ollama(text: str, meal_type: str) -> ParsedMeal:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    schema = ParsedMeal.model_json_schema()
    body = {
        "model": os.getenv("OLLAMA_MODEL", "qwen3:4b"),
        "stream": False,
        "think": False,
        "format": schema,
        "options": {"temperature": 0, "num_predict": 300},
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是饮食记录解析器。只按照 JSON Schema 返回数据。每种已识别食物都必须"
                    "根据常见份量填写 estimated_grams，例如半个牛油果约75克、一小盒酸奶约150克；"
                    "不确定时仍给保守估计并降低 confidence，完全无法识别时才要求澄清。"
                ),
            },
            {"role": "user", "content": f"餐次：{meal_type}\n记录：{text}"},
        ],
    }
    request = Request(
        f"{base_url}/api/chat",
        data=json.dumps(body, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        payload = json.loads(response.read())
    return ParsedMeal.model_validate_json(payload["message"]["content"])


def _parse_with_openai(text: str, meal_type: str) -> ParsedMeal | None:

    from openai import OpenAI

    client = OpenAI()
    response = client.responses.parse(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-terra"),
        reasoning={"effort": "low"},
        input=[
            {
                "role": "developer",
                "content": (
                    "将中文饮食描述提取为结构化数据。分量不明确时给合理区间中的保守估计，"
                    "置信度要反映不确定性；完全无法判断时设置 needs_clarification。"
                ),
            },
            {"role": "user", "content": f"餐次：{meal_type}\n记录：{text}"},
        ],
        text_format=ParsedMeal,
    )
    return response.output_parsed


def parse_meal(text: str, meal_type: str) -> tuple[ParsedMeal, str]:
    provider, label = provider_status()
    try:
        if provider == "ollama":
            return _parse_with_ollama(text, meal_type), label
        if provider == "openai":
            parsed = _parse_with_openai(text, meal_type)
            if parsed is not None:
                return parsed, label
    except Exception:  # noqa: BLE001 - provider failures must not block meal logging
        # A local fallback keeps meal logging usable when a model is unavailable.
        return parse_meal_locally(text, meal_type), f"{label} 暂不可用，已使用本地规则"
    return parse_meal_locally(text, meal_type), "本地规则模式"


def generate_feedback(totals: NutritionTotals) -> str:
    observations: list[str] = []
    if totals.protein < 50:
        observations.append("今天记录到的蛋白质偏少，下一餐可选择鱼、鸡肉、鸡蛋、豆腐或酸奶。")
    else:
        observations.append("今天记录到的蛋白质基础不错。")
    if totals.fiber < 20:
        observations.append("膳食纤维偏少，下一餐建议增加两份蔬菜或一份水果。")
    if totals.calories > 2000:
        observations.append("当前记录的总热量已经较高，下一餐可减少油炸食物和含糖饮料。")
    else:
        observations.append("热量只是估算值；不明确的分量会让结果产生较大误差。")
    return " ".join(observations)
