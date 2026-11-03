from __future__ import annotations

from datetime import datetime

import streamlit as st

from food_agent.ai import generate_feedback, parse_meal, provider_status
from food_agent.database import (
    clear_meals,
    daily_totals,
    delete_meal,
    get_meals,
    init_db,
    save_meal,
)
from food_agent.nutrition import calculate_meal
from food_agent.schemas import MealRecord

MEAL_LABELS = {
    "早餐": "breakfast",
    "午餐": "lunch",
    "晚餐": "dinner",
    "零食/饮料": "snack",
}

st.set_page_config(page_title="Food Agent", page_icon="🥗", layout="centered")
init_db()

st.title("🥗 Food Agent")
st.caption("告诉我你吃了什么，我告诉你下一顿怎么吃。")

provider, provider_label = provider_status()
if provider == "ollama":
    st.success(f"{provider_label} 已启用，数据保留在本机", icon="🖥️")
elif provider == "openai":
    st.success(f"{provider_label} 已启用", icon="✨")
else:
    st.info(
        "当前为本地规则模式。启动 Ollama 后会自动启用免费的本地 AI。",
        icon="💡",
    )

with st.form("meal_form", clear_on_submit=True):
    meal_label = st.segmented_control("这是哪一餐？", list(MEAL_LABELS), default="午餐")
    description = st.text_area(
        "吃了什么？",
        placeholder="例如：午餐吃了一碗米饭、一个鸡腿和一些西兰花",
        height=110,
    )
    submitted = st.form_submit_button("记录并分析", type="primary", use_container_width=True)

if submitted:
    if not description.strip():
        st.warning("请先输入一段饮食记录。")
    else:
        with st.spinner("正在分析这顿饭…"):
            parsed, parser_name = parse_meal(description, MEAL_LABELS[meal_label or "午餐"])
            if parsed.needs_clarification:
                st.warning(parsed.clarification_question or "请补充分量信息。")
            else:
                totals = calculate_meal(parsed.foods)
                record = MealRecord(
                    record_date=datetime.now().astimezone().date(),
                    meal_type=parsed.meal_type,
                    original_text=description,
                    foods=parsed.foods,
                    totals=totals,
                )
                save_meal(record)
                st.success(f"记录成功 · {parser_name}")
                st.rerun()

records = get_meals(datetime.now().astimezone().date())
totals = daily_totals(records)

st.subheader("今天的营养概览")
columns = st.columns(4)
columns[0].metric("热量", f"{totals.calories:.0f} kcal")
columns[1].metric("蛋白质", f"{totals.protein:.1f} g")
columns[2].metric("碳水", f"{totals.carbs:.1f} g")
columns[3].metric("膳食纤维", f"{totals.fiber:.1f} g")

if records:
    st.subheader("下一餐建议")
    st.write(generate_feedback(totals))

    st.subheader("今日记录")
    for record in reversed(records):
        with st.expander(f"{record.meal_type} · {record.original_text}"):
            for food in record.foods:
                st.write(
                    f"- {food.name}：约 {food.estimated_grams or 0:.0f} g "
                    f"（置信度 {food.confidence:.0%}）"
                )
            st.caption(f"本餐估算 {record.totals.calories:.0f} kcal")
            if (
                record.id is not None
                and st.button(
                    "删除这条记录",
                    key=f"delete_meal_{record.id}",
                    icon="🗑️",
                    type="secondary",
                )
                and delete_meal(record.id)
            ):
                st.toast("记录已删除")
                st.rerun()

    with st.expander("管理今日记录"):
        confirm_clear = st.checkbox(
            "我确认要删除今天的全部饮食记录",
            key="confirm_clear_today",
        )
        if st.button(
            "清空今日记录",
            disabled=not confirm_clear,
            type="secondary",
            icon="⚠️",
        ):
            removed = clear_meals(datetime.now().astimezone().date())
            st.toast(f"已删除 {removed} 条记录")
            st.rerun()
else:
    st.caption("今天还没有记录。试试输入：两个鸡蛋、一杯牛奶。")

st.divider()
st.caption(
    "营养数值为估算结果，只用于一般性饮食参考，不能替代医生或注册营养师的诊断。"
)
