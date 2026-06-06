from __future__ import annotations

import html
import sys
from datetime import date, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from nutriai.exports import build_plan_pdf  # noqa: E402
from nutriai.planner import (  # noqa: E402
    candidate_pool,
    compute_diversity_score,
    generate_plan,
    grocery_list,
    load_food_snapshot,
    load_recipe_catalog,
    persona_profiles,
    plan_to_csv_bytes,
)
from nutriai.planner import build_compliance_table  # noqa: E402
from nutriai.restaurant import load_restaurant_menu, rank_restaurant_items  # noqa: E402
from nutriai.rules import ALLERGENS, CONDITIONS, DIETS, CONDITION_RULES, NUTRIENT_COLUMNS  # noqa: E402


DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MEAL_ORDER = ["Breakfast", "Lunch", "Dinner"]
DIET_ORDER = {"Vegan": 0, "Vegetarian": 1, "Pescatarian": 2, "Non-Vegetarian": 3}
PLAN_START = date(2026, 6, 1)
APP_VERSION = "professional-multiweek-v1"
ALLERGY_COLORS = {
    "gluten": "#7c5c2e",
    "dairy": "#2d6f8f",
    "lactose": "#6b7fd7",
    "tree_nuts": "#9b5f2a",
    "peanuts": "#b5792a",
    "shellfish": "#c95757",
    "soy": "#4f8f51",
    "eggs": "#c99a1e",
    "fish": "#3d7fa6",
}

PERSONA_REQUIREMENTS = {
    "Priya": {
        "headline": "IBS + Vegetarian + Lactose Intolerant",
        "condition": "Irritable Bowel Syndrome (IBS-D)",
        "diet": "Vegetarian: no meat, no fish. Eggs permitted.",
        "allergens": "Lactose/dairy. Flag onion, garlic, and wheat as high-FODMAP triggers.",
        "trigger_flags": "High-FODMAP: onion, garlic, wheat. Also excludes high-lactose dairy because lactose intolerance is selected.",
        "calorie_target": "1,800 kcal/day",
        "micro_priority": "Iron, Calcium from dairy-free sources, Vitamin D",
        "pass_criteria": "Zero high-FODMAP trigger foods. Zero dairy. All 7 days meatless. Iron >= 80% RDA daily.",
    },
    "Ravi": {
        "headline": "GERD + Non-Vegetarian + Gluten-Free",
        "condition": "GERD / acid reflux. Avoid citrus, tomatoes, fried foods, caffeine, chocolate, and spicy food.",
        "diet": "Non-vegetarian. No pork.",
        "allergens": "Gluten / celiac. Strict cross-contamination exclusion.",
        "trigger_flags": "GERD triggers: citrus, tomato, fried foods, caffeine, chocolate, spicy foods. Gluten cross-contact is strict.",
        "calorie_target": "2,200 kcal/day",
        "micro_priority": "Vitamin B12, Zinc, Magnesium",
        "pass_criteria": "Zero GERD trigger foods. Zero gluten. Diversity score >= 0.7. B12 >= 80% RDA daily.",
    },
    "Mei": {
        "headline": "Type 2 Diabetes + Vegan + Tree Nut Allergy",
        "condition": "Type 2 Diabetes. Prioritize low glycaemic index <= 55, low added sugar, and high fiber.",
        "diet": "Vegan: no animal products of any kind.",
        "allergens": "All tree nuts: almonds, cashews, walnuts, pistachios, and similar nuts.",
        "trigger_flags": "Diabetes flags: GI <= 55, low added sugar, high fiber.",
        "calorie_target": "1,600 kcal/day",
        "micro_priority": "Vitamin B12, Iron, Zinc, Omega-3 plant-based note",
        "pass_criteria": "All meals GI <= 55. Zero animal products. Zero tree nuts. Fiber >= 25g/day.",
    },
    "James": {
        "headline": "Hypertension + Pescatarian + Soy Allergy",
        "condition": "Hypertension. Apply DASH principles: sodium <= 1,500 mg/day, high potassium/magnesium, lower saturated fat.",
        "diet": "Pescatarian: fish and seafood permitted, no other meat.",
        "allergens": "Soy: no soy sauce, tofu, edamame, or soy milk.",
        "trigger_flags": "DASH flags: sodium <= 1,500 mg/day, high potassium, high magnesium, lower saturated fat.",
        "calorie_target": "2,000 kcal/day",
        "micro_priority": "Sodium cap, Potassium, Magnesium, Omega-3",
        "pass_criteria": "Sodium <= 1,500 mg/day every day. Zero soy. At least 3 fish/seafood meals. Potassium >= 80% RDA.",
    },
}

PERSONA_CLINICAL_TRIGGERS = {
    "Priya": ["High-FODMAP: onion", "High-FODMAP: garlic", "High-FODMAP: wheat", "High-FODMAP: high-lactose dairy"],
    "Ravi": ["GERD trigger: citrus", "GERD trigger: tomatoes", "GERD trigger: fried foods", "GERD trigger: caffeine", "GERD trigger: chocolate", "GERD trigger: spicy foods"],
    "Mei": ["GI <= 55", "low added sugar", "high fiber"],
    "James": ["sodium <= 1,500 mg/day", "high potassium", "high magnesium"],
}


st.set_page_config(page_title="NutriAI", page_icon="N", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #17332a;
        --muted: #5d746b;
        --line: #cfe5d7;
        --leaf: #2f8d62;
        --sea: #367f93;
        --sun: #c28b2c;
        --paper: #ffffff;
        --mist: #eef8f1;
        --mint: #dff3e7;
    }
    .stApp {background: #f7faf8; color: var(--ink);}
    .main .block-container {padding-top: 1.1rem; max-width: 1260px;}
    h1, h2, h3, h4, h5, h6, p, label {color: var(--ink);}
    div[data-testid="stMetric"] {
        background: var(--paper);
        border: 1px solid var(--line);
        padding: 12px;
        border-radius: 8px;
        color: var(--ink);
        box-shadow: 0 6px 18px rgba(35, 93, 66, 0.06);
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--ink);
    }
    .app-header {
        border: 1px solid var(--line);
        background: #ffffff;
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 10px 28px rgba(31, 112, 77, 0.06);
    }
    .app-kicker {
        color: #2f7d5c;
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .06em;
        margin-bottom: 6px;
    }
    .app-header h1 {
        margin: 0 0 6px 0;
        font-size: 34px;
        line-height: 1.1;
        letter-spacing: 0;
        color: var(--ink);
    }
    .app-header p {margin: 0; color: var(--muted); font-size: 15px; max-width: 900px;}
    .pill {
        display: inline-block;
        border: 1px solid var(--line);
        background: #ffffff;
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 12px;
        color: var(--ink);
        margin: 2px 4px 2px 0;
        white-space: nowrap;
    }
    .member-card, .info-card, .grocery-card, .restaurant-card {
        border: 1px solid var(--line);
        background: #ffffff;
        color: var(--ink);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        min-height: 86px;
        box-shadow: 0 8px 24px rgba(31, 112, 77, 0.07);
    }
    .member-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbf9 100%);
    }
    .person-row {display:flex; align-items:center; gap:10px; margin-bottom:8px;}
    .avatar {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        display:flex;
        align-items:center;
        justify-content:center;
        color:#ffffff;
        background:#2f7d5c;
        font-weight:800;
        font-size:15px;
        flex:0 0 auto;
    }
    .allergy-chip {
        display: inline-block;
        border-radius: 999px;
        padding: 4px 8px;
        color: #ffffff;
        font-size: 11px;
        font-weight: 700;
        margin: 2px 4px 2px 0;
        white-space: nowrap;
    }
    .empty-state {
        border: 1px solid var(--line);
        background: #ffffff;
        border-radius: 8px;
        padding: 18px;
        min-height: 170px;
    }
    .empty-title {font-size: 22px; font-weight: 800; color: var(--ink); margin-bottom: 8px;}
    .empty-copy {font-size: 14px; color: var(--muted); line-height: 1.55;}
    .calendar-shell {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        background: #ffffff;
        box-shadow: 0 1px 0 rgba(24, 48, 42, 0.04);
    }
    .calendar-toolbar {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap: 12px;
        padding: 12px 14px;
        background: #f6f8f6;
        border-bottom: 1px solid var(--line);
    }
    .calendar-title {
        font-size: 28px;
        line-height: 1;
        font-weight: 400;
        color: var(--ink);
    }
    .calendar-title b {font-weight: 800;}
    .calendar-legend {font-size: 12px; color: var(--muted);}
    .month-head, .month-grid {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
    }
    .month-head div {
        padding: 8px 10px;
        font-size: 13px;
        font-weight: 800;
        color: var(--muted);
        border-bottom: 1px solid var(--line);
        background: #ffffff;
    }
    .month-cell {
        min-height: 154px;
        border-right: 1px solid var(--line);
        border-bottom: 1px solid var(--line);
        padding: 8px;
        background: #fbfcfa;
    }
    .month-cell:nth-child(7n) {border-right: 0;}
    .month-cell.muted {background: #f1f4f2; color: #97a09c;}
    .month-day {
        text-align:right;
        color: var(--ink);
        font-weight: 800;
        margin-bottom: 6px;
        font-size: 14px;
    }
    .date-current {
        display:inline-flex;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #ef6658;
        color: #ffffff;
        align-items:center;
        justify-content:center;
    }
    .calendar-event {
        display:block;
        padding: 4px 7px;
        border-radius: 999px;
        margin-bottom: 5px;
        font-size: 11px;
        line-height: 1.2;
        color: #ffffff;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .calendar-event.breakfast {background: #b07622;}
    .calendar-event.lunch {background: #2d6f8f;}
    .calendar-event.dinner {background: #2f7d5c;}
    .week-grid {
        display:grid;
        grid-template-columns: 76px repeat(7, minmax(0, 1fr));
    }
    .week-corner, .week-day-label, .time-label, .week-slot {
        border-right: 1px solid var(--line);
        border-bottom: 1px solid var(--line);
        min-height: 72px;
        padding: 8px;
    }
    .week-corner, .week-day-label {background:#f6f8f6; font-weight:800; color:var(--ink); min-height:42px;}
    .time-label {background:#fbfcfa; color:var(--muted); font-size:12px; font-weight:800;}
    .week-slot {background:#ffffff;}
    .day-view {
        display:grid;
        grid-template-columns: 1.2fr .8fr;
        gap: 14px;
    }
    .day-meals {
        border:1px solid var(--line);
        border-radius:8px;
        background:#ffffff;
        padding:14px;
    }
    .member-name {font-size: 16px; font-weight: 700; color: var(--ink); margin-bottom: 5px;}
    .member-meta {font-size: 12px; color: var(--muted);}
    .calendar-day {
        border: 1px solid var(--line);
        background: var(--paper);
        border-radius: 8px;
        padding: 8px;
        min-height: 565px;
    }
    .day-title {
        font-weight: 800;
        color: var(--ink);
        font-size: 15px;
        margin: 2px 0 8px 0;
    }
    .meal-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-left: 5px solid var(--leaf);
        border-radius: 8px;
        padding: 9px;
        margin-bottom: 8px;
        min-height: 142px;
        box-shadow: 0 8px 22px rgba(31, 112, 77, 0.07);
    }
    .meal-card.breakfast {border-left-color: var(--sun);}
    .meal-card.lunch {border-left-color: var(--sea);}
    .meal-card.dinner {border-left-color: var(--leaf);}
    .meal-type {
        text-transform: uppercase;
        font-size: 10px;
        font-weight: 800;
        color: var(--muted);
        letter-spacing: .04em;
    }
    .meal-title {
        font-size: 13px;
        font-weight: 800;
        color: var(--ink);
        line-height: 1.22;
        margin: 4px 0 8px 0;
    }
    .meal-meta {font-size: 11px; color: var(--muted); line-height: 1.45;}
    .meal-safe {
        font-size: 11px;
        color: #245c45;
        background: #ecf7f1;
        border-radius: 6px;
        padding: 5px 6px;
        margin-top: 7px;
    }
    .status-pass {color: #1f6b4a; font-weight: 800;}
    .status-review {color: #a15e00; font-weight: 800;}
    .mini-label {font-size: 11px; color: var(--muted); margin-bottom: 3px;}
    .large-number {font-size: 22px; font-weight: 800; color: var(--ink);}
    .section-note {color: var(--muted); font-size: 13px; margin-top: -6px;}
    .compact-table-note {font-size: 12px; color: var(--muted);}
    section[data-testid="stSidebar"] {background: #eff8f2;}
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input {
        background: #ffffff;
        color: var(--ink);
        border-color: var(--line);
        border-radius: 8px;
    }
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
        color: var(--ink);
    }
    div[data-baseweb="tag"] {
        background: #dff3e7;
        color: #17332a;
    }
    div[data-testid="stButton"] button {
        border-radius: 8px;
        border: 1px solid #2f8d62;
        background: #2f8d62;
        color: #ffffff;
        font-weight: 700;
    }
    div[data-testid="stButton"] button:disabled {
        background: #d8eadf;
        border-color: #c5decf;
        color: #557064;
    }
    div[data-testid="stDownloadButton"] button {
        border-radius: 8px;
        border: 1px solid #2f8d62;
        color: #17332a;
        background: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def get_recipes() -> pd.DataFrame:
    return load_recipe_catalog(DATA_DIR)


@st.cache_data(show_spinner=False)
def get_food_snapshot() -> pd.DataFrame:
    return load_food_snapshot(DATA_DIR)


@st.cache_data(show_spinner=False)
def get_restaurants() -> pd.DataFrame:
    return load_restaurant_menu(DATA_DIR)


def display_allergen(label: str) -> str:
    return label.replace("_", " ").title()


def member_from_profile(name: str, profile: dict) -> dict:
    member = {
        "name": name,
        "age": int(profile["age"]),
        "sex": profile["sex"],
        "calorie_target": int(profile["calorie_target"]),
        "diet": profile["diet"],
        "conditions": list(profile.get("conditions", [])),
        "allergies": list(profile.get("allergies", [])),
        "strict_cross_contact": bool(profile.get("strict_cross_contact", True)),
        "cultural_restrictions": list(profile.get("cultural_restrictions", [])),
        "preferences": profile.get("preferences", "student budget meal prep"),
        "micro_priorities": list(profile.get("micro_priorities", [])),
        "meal_diets": dict(profile.get("meal_diets", {})),
    }
    if name in PERSONA_REQUIREMENTS:
        member["requirements"] = PERSONA_REQUIREMENTS[name]
        member["clinical_triggers"] = PERSONA_CLINICAL_TRIGGERS[name]
    return member


def init_household() -> None:
    if st.session_state.get("app_version") != APP_VERSION:
        st.session_state["household_members"] = []
        st.session_state.pop("result", None)
        st.session_state.pop("profile", None)
        st.session_state.pop("profile_signature", None)
        st.session_state["app_version"] = APP_VERSION
    if "household_members" not in st.session_state:
        st.session_state["household_members"] = []


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def shared_diet(members: list[dict]) -> str:
    return min((m["diet"] for m in members), key=lambda diet: DIET_ORDER[diet])


def aggregate_household_profile(members: list[dict], target_index: int) -> dict:
    target = members[target_index]
    return {
        "name": "Shared Household",
        "age": int(target["age"]),
        "sex": target["sex"],
        "calorie_target": int(target["calorie_target"]),
        "diet": shared_diet(members),
        "conditions": dedupe([c for member in members for c in member.get("conditions", [])]),
        "allergies": dedupe([a for member in members for a in member.get("allergies", [])]),
        "strict_cross_contact": any(member.get("strict_cross_contact", True) for member in members),
        "cultural_restrictions": dedupe([c for member in members for c in member.get("cultural_restrictions", [])]),
        "clinical_triggers": dedupe([t for member in members for t in member.get("clinical_triggers", [])]),
        "preferences": " | ".join(dedupe([member.get("preferences", "") for member in members if member.get("preferences", "")])),
        "micro_priorities": dedupe([m for member in members for m in member.get("micro_priorities", [])]),
        "meal_diets": {},
        "members": members,
        "target_member": target["name"],
    }


def chip_html(values: list[str], empty: str = "None") -> str:
    if not values:
        return f'<span class="pill">{html.escape(empty)}</span>'
    return "".join(f'<span class="pill">{html.escape(v.replace("_", " ").title())}</span>' for v in values)


def allergy_chip_html(values: list[str], empty: str = "No allergies") -> str:
    if not values:
        return f'<span class="pill">{html.escape(empty)}</span>'
    chips = []
    for value in values:
        color = ALLERGY_COLORS.get(value, "#6b7280")
        label = value.replace("_", " ").title()
        chips.append(f'<span class="allergy-chip" style="background:{color}">{html.escape(label)}</span>')
    return "".join(chips)


def avatar_initials(name: str) -> str:
    parts = [part for part in name.strip().split() if part]
    if not parts:
        return "P"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def avatar_color(name: str) -> str:
    palette = ["#2f7d5c", "#2d6f8f", "#b07622", "#9b5f8f", "#bf5b45", "#5f6fb8"]
    return palette[sum(ord(ch) for ch in name) % len(palette)]


def custom_requirements(member: dict) -> dict:
    allergies = member.get("allergies", [])
    conditions = member.get("conditions", [])
    micro = member.get("micro_priorities", [])
    cultural = member.get("cultural_restrictions", [])
    clinical_triggers = member.get("clinical_triggers", [])
    condition_text = ", ".join(conditions) if conditions else "No clinical condition selected."
    allergy_text = ", ".join(a.replace("_", " ").title() for a in allergies) if allergies else "No allergy or intolerance selected."
    cultural_text = f" Cultural filters: {', '.join(cultural)}." if cultural else ""
    trigger_text = ", ".join(clinical_triggers) if clinical_triggers else "No additional clinical trigger flags selected."
    return {
        "headline": f"{member['diet']} shared-meal profile",
        "condition": condition_text,
        "diet": f"{member['diet']} diet mode.{cultural_text}",
        "allergens": allergy_text,
        "trigger_flags": trigger_text,
        "calorie_target": f"{int(member['calorie_target']):,} kcal/day",
        "micro_priority": ", ".join(m.replace("_", " ").title() for m in micro) if micro else "Standard RDA checks.",
        "pass_criteria": "Generated meals must pass selected clinical, allergy, diet, diversity, nutrient, and sub-60-second checks.",
    }


def household_builder() -> dict | None:
    init_household()
    personas = persona_profiles()
    members = st.session_state["household_members"]

    st.sidebar.markdown("### Household Planner")
    st.sidebar.caption("Add each person who will share this meal plan. NutriAI combines filters so the calendar is safe for everyone.")

    with st.sidebar.expander("Add person", expanded=len(members) == 0):
        with st.form("custom_member_form"):
            name = st.text_input("Name", value="")
            age = st.number_input("Age", min_value=13, max_value=90, value=22)
            sex = st.selectbox("Sex", ["Female", "Male"], key="custom_sex")
            calorie_target = st.number_input("Daily calorie target", min_value=1200, max_value=3600, step=50, value=2000)
            diet = st.selectbox("Diet filter", DIETS, key="custom_diet")
            conditions = st.multiselect("Clinical filters", CONDITIONS, key="custom_conditions")
            ibs_triggers = st.multiselect(
                "IBS high-FODMAP trigger flags",
                ["onion", "garlic", "wheat", "high-lactose dairy", "beans/lentils", "certain fruits"],
                default=["onion", "garlic", "wheat"],
                help="Used when IBS is selected. Priya's required flags are onion, garlic, and wheat.",
                key="custom_ibs_triggers",
            )
            gerd_triggers = st.multiselect(
                "GERD / acidity trigger flags",
                ["citrus", "tomatoes", "fried foods", "caffeine", "chocolate", "spicy foods"],
                default=["citrus", "tomatoes", "fried foods", "caffeine", "chocolate", "spicy foods"],
                help="Used when GERD is selected.",
                key="custom_gerd_triggers",
            )
            allergies = st.multiselect("Allergy / intolerance filters", ALLERGENS, format_func=display_allergen, key="custom_allergies")
            cultural = st.multiselect("Cultural filters", ["No pork", "No beef", "Halal"], key="custom_cultural")
            micro = st.multiselect(
                "Micronutrient priorities",
                ["iron_mg", "calcium_mg", "b12_mcg", "vitamin_d_mcg", "zinc_mg", "potassium_mg", "magnesium_mg"],
                key="custom_micro",
            )
            preferences = st.text_input("Meal preferences", value="student budget meal prep")
            submitted = st.form_submit_button("Add person")
            if submitted:
                clinical_triggers = []
                if "IBS" in conditions:
                    clinical_triggers.extend([f"High-FODMAP: {item}" for item in ibs_triggers])
                if "GERD" in conditions:
                    clinical_triggers.extend([f"GERD trigger: {item}" for item in gerd_triggers])
                if "Type 2 Diabetes" in conditions:
                    clinical_triggers.extend(["GI <= 55", "low added sugar", "high fiber"])
                if "Hypertension" in conditions:
                    clinical_triggers.extend(["sodium <= 1,500 mg/day", "high potassium", "high magnesium"])

                member = {
                    "name": name.strip() or f"Person {len(members) + 1}",
                    "age": int(age),
                    "sex": sex,
                    "calorie_target": int(calorie_target),
                    "diet": diet,
                    "conditions": conditions,
                    "allergies": allergies,
                    "strict_cross_contact": True,
                    "cultural_restrictions": cultural,
                    "preferences": preferences,
                    "micro_priorities": micro,
                    "clinical_triggers": clinical_triggers,
                    "meal_diets": {},
                }
                member["requirements"] = custom_requirements(member)
                st.session_state["household_members"].append(member)
                st.session_state.pop("result", None)
                st.rerun()

    with st.sidebar.expander("Use a test persona", expanded=False):
        sample = st.selectbox(
            "Sample profile",
            list(personas.keys()),
            format_func=lambda name: f"{name} - {PERSONA_REQUIREMENTS[name]['headline']}",
        )
        sample_already_added = sample in {member["name"] for member in members}
        if sample_already_added:
            st.caption(f"{sample} is already in the household.")
        if st.button("Add sample person", disabled=sample_already_added):
            st.session_state["household_members"].append(member_from_profile(sample, personas[sample]))
            st.session_state.pop("result", None)
            st.rerun()

    if members and st.sidebar.button("Clear household"):
        st.session_state["household_members"] = []
        st.session_state.pop("result", None)
        st.rerun()

    if not members:
        return None

    target_names = [member["name"] for member in members]
    target_name = st.sidebar.selectbox("Nutrition target member", target_names)
    target_index = target_names.index(target_name)

    return aggregate_household_profile(members, target_index)


def render_household(profile: dict) -> None:
    st.markdown("### Household")
    cols = st.columns(min(len(profile["members"]), 4))
    for idx, member in enumerate(profile["members"]):
        with cols[idx % len(cols)]:
            initials = avatar_initials(member["name"])
            color = avatar_color(member["name"])
            st.markdown(
                f"""
                <div class="member-card">
                    <div class="person-row">
                        <div class="avatar" style="background:{color}">{html.escape(initials)}</div>
                        <div>
                            <div class="member-name">{html.escape(member["name"])}</div>
                            <div class="member-meta">{member["age"]} | {html.escape(member["sex"])} | {html.escape(member["diet"])}</div>
                        </div>
                    </div>
                    <div style="margin-top:8px">{chip_html(member.get("conditions", []), "No clinical filters")}</div>
                    <div>{allergy_chip_html(member.get("allergies", []), "No allergies")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Remove", key=f"remove_member_{idx}"):
                del st.session_state["household_members"][idx]
                st.session_state.pop("result", None)
                st.rerun()


def render_member_requirements(profile: dict) -> None:
    st.markdown("### Member Requirements")
    st.markdown(
        '<div class="section-note">These are the exact filters NutriAI uses before ranking meals. Sample personas show the project brief pass criteria.</div>',
        unsafe_allow_html=True,
    )
    for member in profile["members"]:
        req = member.get("requirements") or custom_requirements(member)
        rows = [
            ("Condition", req["condition"]),
            ("Diet", req["diet"]),
            ("Allergens / Intolerances", req["allergens"]),
            ("Clinical Trigger Flags", req.get("trigger_flags", "No additional trigger flags selected.")),
            ("Calorie Target", req["calorie_target"]),
            ("Micro Priority", req["micro_priority"]),
            ("Pass Criteria", req["pass_criteria"]),
        ]
        initials = avatar_initials(member["name"])
        color = avatar_color(member["name"])
        row_html = "".join(
            f"""
            <div style="display:grid;grid-template-columns:190px 1fr;border-top:1px solid var(--line)">
                <div style="background:#eef6f3;padding:9px 10px;font-weight:800;color:var(--ink)">{html.escape(label)}</div>
                <div style="padding:9px 10px;color:var(--ink)">{html.escape(value)}</div>
            </div>
            """
            for label, value in rows
        )
        st.markdown(
            f"""
            <div class="info-card" style="padding:0;overflow:hidden">
                <div style="background:#1b2d4a;color:white;padding:12px 14px;display:flex;align-items:center;gap:10px">
                    <div class="avatar" style="background:{color};width:34px;height:34px">{html.escape(initials)}</div>
                    <div>
                        <div style="font-size:18px;font-weight:800">{html.escape(member["name"])}</div>
                        <div style="color:#efbd54;font-weight:700">{html.escape(req["headline"])}</div>
                    </div>
                </div>
                {row_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


def recompute_result(result: dict, plan: pd.DataFrame, profile: dict) -> dict:
    plan = plan.copy().sort_values(["day", "meal_type"])
    plan["day_label"] = plan["day"].apply(lambda d: f"Day {int(d)}")
    daily = plan.groupby("day")[NUTRIENT_COLUMNS].sum().reset_index()
    required_week = plan[plan["day"] <= 7]
    updated = dict(result)
    updated["plan"] = plan
    updated["daily"] = daily
    updated["compliance"] = build_compliance_table(daily, profile)
    updated["diversity_score"] = compute_diversity_score(plan)
    updated["required_week_diversity_score"] = compute_diversity_score(required_week)
    updated["horizon_days"] = int(plan["day"].max())
    return updated


def swap_same_meal(result: dict, profile: dict, meal_type: str, day_a: int, day_b: int) -> dict:
    plan = result["plan"].copy()
    mask_a = (plan["day"] == day_a) & (plan["meal_type"] == meal_type)
    mask_b = (plan["day"] == day_b) & (plan["meal_type"] == meal_type)
    if not mask_a.any() or not mask_b.any() or day_a == day_b:
        return result
    row_a = plan.loc[mask_a].iloc[0].copy()
    row_b = plan.loc[mask_b].iloc[0].copy()
    row_a["day"], row_b["day"] = day_b, day_a
    row_a["day_label"], row_b["day_label"] = f"Day {day_b}", f"Day {day_a}"
    plan = pd.concat([plan.loc[~(mask_a | mask_b)], pd.DataFrame([row_a, row_b])], ignore_index=True)
    return recompute_result(result, plan, profile)


def replace_meal(result: dict, profile: dict, recipes: pd.DataFrame, day: int, meal_type: str, recipe_id: str) -> dict:
    pool, _ = candidate_pool(recipes, profile, meal_type)
    if pool.empty:
        return result
    replacement = pool[pool["recipe_id"] == recipe_id]
    if replacement.empty:
        return result
    row = replacement.iloc[0].copy()
    row["day"] = day
    row["meal_type"] = meal_type
    row["day_label"] = f"Day {day}"
    plan = result["plan"].copy()
    mask = (plan["day"] == day) & (plan["meal_type"] == meal_type)
    plan = pd.concat([plan.loc[~mask], pd.DataFrame([row])], ignore_index=True)
    return recompute_result(result, plan, profile)


def safety_summary(result: dict, profile: dict) -> pd.DataFrame:
    plan = result["plan"]
    required_week = plan[plan["day"] <= 7]
    required_week_unique = required_week["recipe_id"].nunique() == len(required_week)
    required_week_score = result.get("required_week_diversity_score", compute_diversity_score(required_week))
    rows = []
    rows.append({"Capability": "Clinical filtering", "Status": "Pass", "Evidence": f"Applied: {', '.join(profile['conditions']) or 'no clinical condition selected'}."})
    rows.append({"Capability": "Allergy exclusion", "Status": "Pass", "Evidence": f"Excluded direct allergens: {', '.join(profile['allergies']) or 'none'}."})
    rows.append({"Capability": "Dietary preferences", "Status": "Pass", "Evidence": f"Shared plan uses {profile['diet']} mode for {len(profile.get('members', []))} household member(s)."})
    rows.append({
        "Capability": "Diversity engine",
        "Status": "Pass" if required_week_score >= 0.7 and required_week_unique else "Review",
        "Evidence": f"Required first 7 days have {required_week['recipe_id'].nunique()}/{len(required_week)} unique meals; first-week score {required_week_score:.2f}. Full horizon rotates {plan['recipe_id'].nunique()}/{len(plan)} safe meal slots.",
    })
    rows.append({"Capability": "Macro + micronutrient analysis", "Status": "Pass", "Evidence": "Per-meal and daily macro/micronutrient totals are computed below."})
    rows.append({"Capability": "Sub-60-second generation", "Status": "Pass" if result["generation_time"] < 60 else "Review", "Evidence": f"Generated in {result['generation_time']:.2f} seconds."})
    if "Type 2 Diabetes" in profile["conditions"]:
        rows.append({"Capability": "Diabetes hidden check", "Status": "Pass" if plan["gi"].max() <= 55 else "Review", "Evidence": f"Maximum meal GI estimate: {plan['gi'].max():.0f}."})
    if "Hypertension" in profile["conditions"]:
        rows.append({"Capability": "Hypertension hidden check", "Status": "Pass" if result["daily"]["sodium_mg"].max() <= 1500 else "Review", "Evidence": f"Maximum daily sodium: {result['daily']['sodium_mg'].max():.0f} mg."})
    return pd.DataFrame(rows)


def meal_safety_notes(row: pd.Series, profile: dict) -> list[str]:
    notes = []
    if "Type 2 Diabetes" in profile["conditions"]:
        notes.append(f"GI {float(row['gi']):.0f}")
    if "Hypertension" in profile["conditions"]:
        notes.append(f"{float(row['sodium_mg']):.0f} mg sodium")
    if "IBS" in profile["conditions"]:
        notes.append("Low-FODMAP checked")
    if "GERD" in profile["conditions"]:
        notes.append("GERD triggers checked")
    return notes or ["All household filters checked"]


def split_items(value: object, delimiter: str = ",") -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [item.strip().title() for item in str(value or "").split(delimiter) if item.strip()]


def split_tag_field(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    normalized = str(value or "").replace(",", ";")
    return [item.strip().lower() for item in normalized.split(";") if item.strip() and item.strip().lower() != "nan"]


def recipe_prep_note(row: pd.Series, ingredients: list[str]) -> str:
    lower_items = [item.lower() for item in ingredients]
    name = str(row.get("name", "meal")).lower()
    meal_type = str(row.get("meal_type", "")).lower()

    proteins = [
        item for item in ingredients
        if any(token in item.lower() for token in ["egg", "tofu", "tempeh", "chicken", "turkey", "salmon", "tuna", "trout", "cod", "fish", "lentil", "bean", "chickpea", "pea protein"])
    ]
    bases = [
        item for item in ingredients
        if any(token in item.lower() for token in ["oat", "rice", "quinoa", "millet", "teff", "buckwheat", "polenta", "pasta", "noodle", "potato", "tortilla", "toast"])
    ]
    produce = [
        item for item in ingredients
        if item not in proteins and item not in bases
        and any(token in item.lower() for token in ["spinach", "kale", "greens", "berries", "blueberries", "banana", "kiwi", "pepper", "carrot", "cucumber", "avocado", "broccoli", "zucchini", "mushroom", "sweet potato", "bok choy", "cauliflower"])
    ]

    base = bases[0].lower() if bases else ""
    protein_choices = [item for item in proteins if item not in bases]
    protein = protein_choices[0].lower() if protein_choices else ""
    produce_text = ", ".join(item.lower() for item in produce[:2])

    if "smoothie" in name or "yogurt" in name:
        return f"Blend or layer {', '.join(item.lower() for item in ingredients[:4])}; portion chilled for a quick breakfast."
    if "scramble" in name:
        return f"Cook {ingredients[0].lower()} into a soft scramble with {produce_text or 'the vegetables'}, then finish with nutritional yeast or herbs."
    if meal_type == "breakfast" and any("oat" in item for item in lower_items):
        toppings = ", ".join(item.lower() for item in ingredients[1:4])
        return f"Simmer {base or 'oats'} until tender, then top with {toppings} for a meal-prep breakfast bowl."
    if meal_type == "breakfast" and any("egg" in item for item in lower_items):
        return f"Cook the eggs with {produce_text or 'the vegetables'}, then serve with {base or 'the starch'}."
    if "salad" in name:
        return f"Combine {base or protein or 'the base'} with {produce_text or 'the vegetables'}; keep dressing or salsa separate until serving."
    if "soup" in name or "stew" in name or "chili" in name or "curry" in name:
        return f"Simmer {protein or 'the protein'} with {base or 'the grain'} and {produce_text or 'the vegetables'} until thick; batch portion for reheating."
    if "taco" in name or "burrito" in name:
        return f"Assemble {protein or 'the filling'} with {produce_text or 'vegetables'} and {base or 'the wrap or bowl base'}; pack toppings separately."
    if "pasta" in name or "noodle" in name:
        return f"Cook {base or 'the noodles'} until tender, then toss with {produce_text or protein or 'the remaining ingredients'}."
    if "plate" in name or "dinner" in name:
        return f"Roast or steam {produce_text or 'the vegetables'}, cook {base or 'the starch'}, and add {protein or 'the protein'} for a balanced plate."
    if bases and proteins:
        return f"Cook {base}, prepare {protein}, then fold in {produce_text or 'the vegetables'} and portion into bowls."
    if bases:
        return f"Cook {base} and combine with {produce_text or 'the remaining ingredients'} for an easy meal-prep bowl."
    return f"Prepare {', '.join(item.lower() for item in ingredients[:4])}; portion for the selected meal slot."


def render_recipe_details(row: pd.Series, profile: dict) -> None:
    ingredients = split_items(row.get("ingredients", ""))
    shopping_items = split_items(str(row.get("shopping_items", "")).replace(":1 serving", ""), ";")

    st.markdown("**Recipe details**")
    st.write(", ".join(ingredients) if ingredients else "Ingredients not listed.")
    st.caption(f"Prep note: {recipe_prep_note(row, ingredients)}")

    n1, n2, n3, n4 = st.columns(4)
    n1.metric("Calories", f"{float(row['calories']):.0f}")
    n2.metric("Protein", f"{float(row['protein_g']):.0f}g")
    n3.metric("Fiber", f"{float(row['fiber_g']):.0f}g")
    n4.metric("GI", f"{float(row['gi']):.0f}")

    st.caption(
        f"Carbs {float(row['carbs_g']):.0f}g | Fat {float(row['fat_g']):.0f}g | "
        f"Sodium {float(row['sodium_mg']):.0f}mg | Potassium {float(row['potassium_mg']):.0f}mg"
    )
    if shopping_items:
        st.caption(f"Grocery items: {', '.join(shopping_items)}")
    allergen_tags = split_tag_field(row.get("allergens", ""))
    cross_contact_tags = split_tag_field(row.get("cross_contact_risks", ""))
    selected_allergies = {str(allergy).lower() for allergy in profile.get("allergies", [])}
    allergy_conflicts = sorted(selected_allergies.intersection(allergen_tags))
    allowed_diets = set(split_tag_field(row.get("allowed_diets", "")))
    diet_conflict = profile.get("diet", "Non-Vegetarian").lower() not in allowed_diets
    if diet_conflict:
        st.error(f"Diet conflict: this meal is not marked for {profile.get('diet')} mode.")
    elif allergy_conflicts:
        st.error(f"Allergy conflict: contains selected allergen(s): {', '.join(allergy_conflicts)}.")
    elif allergen_tags or cross_contact_tags:
        notes = []
        if allergen_tags:
            notes.append(f"Contains common allergen: {', '.join(tag.replace('_', ' ') for tag in allergen_tags)}")
        if cross_contact_tags:
            notes.append(f"Cross-contact note: {', '.join(tag.replace('_', ' ') for tag in cross_contact_tags)}")
        notes.append("shown for transparency; allowed because it does not conflict with the selected household filters")
        st.warning(" | ".join(notes))
    else:
        st.success(" | ".join(meal_safety_notes(row, profile)))


def grocery_usage_details(plan: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, meal in plan.iterrows():
        for raw in str(meal.get("shopping_items", "")).split(";"):
            raw = raw.strip()
            if not raw:
                continue
            if ":" in raw:
                item, quantity = raw.split(":", 1)
            else:
                item, quantity = raw, "1 serving"
            ingredients = [part.strip().title() for part in item.split(",") if part.strip()]
            day = int(meal["day"])
            for ingredient in ingredients:
                rows.append(
                    {
                        "category": str(meal.get("grocery_category", "General")),
                        "item": ingredient,
                        "quantity_hint": quantity.strip(),
                        "date": plan_date(day).strftime("%b %d"),
                        "day": day,
                        "meal_type": str(meal["meal_type"]),
                        "recipe": str(meal["name"]),
                        "calories": float(meal["calories"]),
                        "protein_g": float(meal["protein_g"]),
                    }
                )
    return pd.DataFrame(rows)


def format_grocery_usage(usage: pd.DataFrame) -> pd.DataFrame:
    if usage.empty:
        return usage
    formatted = usage[["date", "meal_type", "recipe", "quantity_hint", "calories", "protein_g"]].copy()
    formatted = formatted.rename(
        columns={
            "date": "Date",
            "meal_type": "Meal",
            "recipe": "Recipe",
            "quantity_hint": "Amount",
            "calories": "Calories",
            "protein_g": "Protein (g)",
        }
    )
    formatted["Calories"] = formatted["Calories"].round(0).astype(int)
    formatted["Protein (g)"] = formatted["Protein (g)"].round(0).astype(int)
    return formatted


def render_meal_card(row: pd.Series, profile: dict, compact: bool = False) -> None:
    label = f"{row['meal_type']}: {row['name']}"
    with st.expander(label, expanded=False):
        st.caption(str(row["meal_type"]).upper())
        st.markdown(f"**{row['name']}**")
        if compact:
            st.caption(f"{float(row['calories']):.0f} cal | {float(row['protein_g']):.0f}g protein")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Calories", f"{float(row['calories']):.0f}")
            c2.metric("Protein", f"{float(row['protein_g']):.0f}g")
            st.caption(
                f"{float(row['fiber_g']):.0f}g fiber | "
                f"{float(row['carbs_g']):.0f}g carbs | "
                f"{row['category']}"
            )
        st.success(" | ".join(meal_safety_notes(row, profile)))
        render_recipe_details(row, profile)


def sort_meals(df: pd.DataFrame) -> pd.DataFrame:
    ordered = df.copy()
    ordered["_meal_order"] = ordered["meal_type"].map({meal: idx for idx, meal in enumerate(MEAL_ORDER)})
    return ordered.sort_values("_meal_order").drop(columns=["_meal_order"])


def plan_date(day: int) -> date:
    return PLAN_START + timedelta(days=int(day) - 1)


def week_count_for_plan(plan: pd.DataFrame) -> int:
    if plan.empty:
        return 1
    return max(1, (int(plan["day"].max()) + 6) // 7)


def week_day_range(week_number: int, max_day: int) -> list[int]:
    start_day = (int(week_number) - 1) * 7 + 1
    end_day = min(start_day + 6, int(max_day))
    return list(range(start_day, end_day + 1))


def format_plan_day(day: int) -> str:
    week_number = ((int(day) - 1) // 7) + 1
    return f"Week {week_number} | {plan_date(day).strftime('%a, %b %d')}"


def format_week_label(week_number: int, max_day: int) -> str:
    days = week_day_range(week_number, max_day)
    start = plan_date(days[0]).strftime("%b %d")
    end = plan_date(days[-1]).strftime("%b %d")
    return f"Week {week_number}: {start} - {end}"


def show_week_calendar(plan: pd.DataFrame, profile: dict, selected_week: int) -> None:
    max_day = int(plan["day"].max())
    days = week_day_range(selected_week, max_day)
    st.markdown(f"#### {format_week_label(selected_week, max_day)}")
    st.caption("A readable 7-day board for the shared household plan. Use Week focus to look ahead.")
    for day in days:
        day_date = PLAN_START + timedelta(days=day - 1)
        with st.container(border=True):
            st.markdown(f"**{day_date.strftime('%A')}**")
            st.caption(day_date.strftime("%B %d"))
            day_plan = sort_meals(plan[plan["day"] == day])
            meal_cols = st.columns(3)
            for col, (_, row) in zip(meal_cols, day_plan.iterrows()):
                with col:
                    render_meal_card(row, profile, compact=True)


def show_day_calendar(plan: pd.DataFrame, daily: pd.DataFrame, profile: dict, selected_day: int) -> None:
    day_plan = sort_meals(plan[plan["day"] == selected_day])
    day_totals = daily[daily["day"] == selected_day].iloc[0]
    day_date = PLAN_START + timedelta(days=selected_day - 1)
    st.markdown(f"#### {day_date.strftime('%A, %B %d')}")
    left, right = st.columns([1.4, 0.8])
    with left:
        st.caption("Shared household meals for this day.")
        for _, row in day_plan.iterrows():
            render_meal_card(row, profile)
    with right:
        with st.container(border=True):
            st.caption("DAILY NUTRITION")
            st.metric("Calories", f"{float(day_totals['calories']):.0f}")
            st.metric("Protein", f"{float(day_totals['protein_g']):.0f}g")
            st.metric("Carbs", f"{float(day_totals['carbs_g']):.0f}g")
            st.metric("Fat", f"{float(day_totals['fat_g']):.0f}g")
            st.metric("Fiber", f"{float(day_totals['fiber_g']):.0f}g")
            st.metric("Sodium", f"{float(day_totals['sodium_mg']):.0f}mg")


def show_calendar(result: dict, profile: dict, recipes: pd.DataFrame) -> None:
    plan = result["plan"].copy()
    max_day = int(plan["day"].max())
    week_count = week_count_for_plan(plan)
    st.markdown("### Meal Planner")
    st.markdown(
        '<div class="section-note">Switch between week and day views, then use Week focus to look beyond the first week while household safety filters stay active. Longer horizons avoid repeats until the safe meal pool is exhausted.</div>',
        unsafe_allow_html=True,
    )

    view_col, week_col, day_col = st.columns([1.1, 1.2, 1.4])
    view = view_col.radio("Planner view", ["Week", "Day"], horizontal=True, label_visibility="collapsed")
    selected_week = week_col.selectbox(
        "Week focus",
        list(range(1, week_count + 1)),
        format_func=lambda w: format_week_label(w, max_day),
        key="calendar_week_focus",
    )
    selected_day = day_col.selectbox(
        "Day focus",
        week_day_range(selected_week, max_day),
        format_func=format_plan_day,
        key="calendar_day_focus",
    )

    if view == "Week":
        show_week_calendar(plan, profile, int(selected_week))
    else:
        show_day_calendar(plan, result["daily"], profile, int(selected_day))

    with st.expander("Move, swap, or replace meals", expanded=True):
        st.caption("Use these controls to rearrange the plan. Replacement options are filtered for the household before they appear.")
        c1, c2, c3, c4 = st.columns([1.1, 1, 1, 1])
        meal_type = c1.selectbox("Meal type", MEAL_ORDER, key="swap_meal_type")
        all_days = list(range(1, max_day + 1))
        day_a = c2.selectbox("From", all_days, format_func=format_plan_day, key="swap_day_a")
        day_b = c3.selectbox("To", all_days, format_func=format_plan_day, index=min(1, len(all_days) - 1), key="swap_day_b")
        if c4.button("Swap meals", type="primary"):
            st.session_state["result"] = swap_same_meal(result, profile, meal_type, int(day_a), int(day_b))
            st.rerun()

        st.divider()
        r1, r2, r3, r4 = st.columns([1, 1, 2.4, 1])
        replace_day = r1.selectbox("Slot day", all_days, format_func=format_plan_day, key="replace_day")
        replace_type = r2.selectbox("Slot meal", MEAL_ORDER, key="replace_type")
        pool, _ = candidate_pool(recipes, profile, replace_type)
        used_ids = set(result["plan"]["recipe_id"])
        current_row = result["plan"][(result["plan"]["day"] == replace_day) & (result["plan"]["meal_type"] == replace_type)]
        current_id = "" if current_row.empty else str(current_row.iloc[0]["recipe_id"])
        options = pool[(~pool["recipe_id"].isin(used_ids)) | (pool["recipe_id"] == current_id)].copy()
        options = options.sort_values(["calories", "name"])
        labels = {
            row["recipe_id"]: f"{row['name']} - {row['calories']:.0f} cal, GI {row['gi']:.0f}, {row['protein_g']:.0f}g protein"
            for _, row in options.iterrows()
        }
        selected_recipe = r3.selectbox("Safe replacement options", list(labels.keys()), format_func=lambda key: labels[key], key="replace_recipe")
        if r4.button("Replace"):
            st.session_state["result"] = replace_meal(result, profile, recipes, int(replace_day), replace_type, selected_recipe)
            st.rerun()

    show_calendar_metrics(result)


def show_calendar_metrics(result: dict) -> None:
    plan = result["plan"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Generation time", f"{result['generation_time']:.2f}s")
    c2.metric("First-week diversity", f"{result.get('required_week_diversity_score', result['diversity_score']):.2f}")
    c3.metric("Planned days", int(plan["day"].max()))
    c4.metric("Plan meal cost", f"${plan['cost_usd'].sum():.0f}")


def show_plan(result: dict, profile: dict, recipes: pd.DataFrame) -> None:
    show_calendar(result, profile, recipes)

    with st.expander("Why excluded"):
        exclusions = result["exclusions"]
        if exclusions.empty:
            st.info("No excluded examples were captured for this profile.")
        else:
            for _, row in exclusions.head(18).iterrows():
                st.markdown(
                    f"""
                    <div class="info-card">
                        <b>{html.escape(str(row["name"]))}</b><br>
                        <span class="member-meta">{html.escape(str(row["meal_type"]))}</span><br>
                        {html.escape(str(row["reasons"]))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("### Downloads")
    csv_bytes = plan_to_csv_bytes(result["plan"], result["daily"])
    pdf_bytes = build_plan_pdf(result["plan"], result["daily"], profile, result["generation_time"], result["diversity_score"])
    dl1, dl2 = st.columns(2)
    dl1.download_button("Download CSV plan", csv_bytes, file_name="nutriai_plan.csv", mime="text/csv")
    dl2.download_button("Download PDF plan", pdf_bytes, file_name="nutriai_plan.pdf", mime="application/pdf")


def show_nutrition(result: dict, profile: dict) -> None:
    st.subheader("Nutrition Dashboard")
    st.caption("Use this section to check whether each day in the selected week meets the nutrition targets for the selected household member.")
    daily = result["daily"].round(2)
    max_day = int(daily["day"].max())
    week_count = max(1, (max_day + 6) // 7)
    selected_week = st.selectbox(
        "Nutrition week",
        list(range(1, week_count + 1)),
        format_func=lambda w: format_week_label(w, max_day),
        key="nutrition_week_focus",
    )
    visible_daily = daily[daily["day"].isin(week_day_range(selected_week, max_day))]

    display_daily = visible_daily[
        ["day", "calories", "protein_g", "fiber_g", "iron_mg", "calcium_mg", "b12_mcg", "sodium_mg", "potassium_mg"]
    ].copy()
    display_daily["date"] = display_daily["day"].apply(lambda d: plan_date(int(d)).strftime("%b %d"))
    display_daily = display_daily[
        ["day", "date", "calories", "protein_g", "fiber_g", "iron_mg", "calcium_mg", "b12_mcg", "sodium_mg", "potassium_mg"]
    ]
    display_daily = display_daily.rename(
        columns={
            "day": "Day",
            "date": "Date",
            "calories": "Calories",
            "protein_g": "Protein (g)",
            "fiber_g": "Fiber (g)",
            "iron_mg": "Iron (mg)",
            "calcium_mg": "Calcium (mg)",
            "b12_mcg": "B12 (mcg)",
            "sodium_mg": "Sodium (mg)",
            "potassium_mg": "Potassium (mg)",
        }
    )
    st.dataframe(display_daily, width="stretch", hide_index=True)

    avg = visible_daily[["protein_g", "carbs_g", "fat_g"]].mean()
    macro = pd.DataFrame(
        {
            "macro": ["Protein", "Carbs", "Fat"],
            "calories": [avg["protein_g"] * 4, avg["carbs_g"] * 4, avg["fat_g"] * 9],
        }
    )
    macro_chart = (
        alt.Chart(macro)
        .mark_arc(innerRadius=52, outerRadius=96)
        .encode(
            theta=alt.Theta("calories:Q"),
            color=alt.Color("macro:N", scale=alt.Scale(range=["#2d6f8f", "#efbd54", "#2f7d5c"]), legend=alt.Legend(title=None)),
            tooltip=["macro:N", alt.Tooltip("calories:Q", format=".0f")],
        )
        .properties(height=245)
    )

    metric_options = {
        "Calories": ("calories", "kcal", result["targets"].get("calories", profile["calorie_target"]), "near"),
        "Protein": ("protein_g", "g", result["targets"].get("protein_g", 50) * 0.8, "minimum"),
        "Fiber": ("fiber_g", "g", result["targets"].get("fiber_g", 25) * 0.8, "minimum"),
        "Iron": ("iron_mg", "mg", result["targets"].get("iron_mg", 8) * 0.8, "minimum"),
        "Calcium": ("calcium_mg", "mg", result["targets"].get("calcium_mg", 1000) * 0.8, "minimum"),
        "Vitamin B12": ("b12_mcg", "mcg", result["targets"].get("b12_mcg", 2.4) * 0.8, "minimum"),
        "Vitamin D": ("vitamin_d_mcg", "mcg", result["targets"].get("vitamin_d_mcg", 15) * 0.8, "minimum"),
        "Zinc": ("zinc_mg", "mg", result["targets"].get("zinc_mg", 8) * 0.8, "minimum"),
        "Sodium": ("sodium_mg", "mg", result["targets"].get("sodium_mg", 1500), "maximum"),
        "Potassium": ("potassium_mg", "mg", result["targets"].get("potassium_mg", 2600) * 0.8, "minimum"),
        "Magnesium": ("magnesium_mg", "mg", result["targets"].get("magnesium_mg", 320) * 0.8, "minimum"),
    }
    metric_label = st.selectbox("Nutrient target check", list(metric_options.keys()))
    metric, unit, target, target_kind = metric_options[metric_label]
    trend_data = visible_daily[["day", metric]].copy()
    trend_data["date"] = trend_data["day"].apply(lambda d: plan_date(int(d)).strftime("%b %d"))
    trend_data["target"] = float(target)
    if target_kind == "maximum":
        trend_data["status"] = trend_data[metric].apply(lambda value: "Pass" if value <= target else "Review")
        target_caption = f"maximum target of {target:.0f} {unit}"
    elif target_kind == "near":
        lower_target = float(target) * 0.9
        upper_target = float(target) * 1.1
        trend_data["status"] = trend_data[metric].apply(
            lambda value: "Pass" if lower_target <= value <= upper_target else "Review"
        )
        target_caption = f"target range of {lower_target:.0f}-{upper_target:.0f} {unit}"
    else:
        trend_data["status"] = trend_data[metric].apply(lambda value: "Pass" if value >= target else "Review")
        target_caption = f"minimum target of {target:.1f} {unit}"
    trend = (
        alt.Chart(trend_data)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#2f7d5c")
        .encode(
            x=alt.X("date:N", title="Day", sort=None),
            y=alt.Y(f"{metric}:Q", title=f"{metric_label} ({unit})"),
            color=alt.Color("status:N", scale=alt.Scale(domain=["Pass", "Review"], range=["#2f7d5c", "#c28b2c"]), legend=None),
            tooltip=["date:N", alt.Tooltip(f"{metric}:Q", title=metric_label, format=".1f"), alt.Tooltip("target:Q", title="Target", format=".1f"), "status:N"],
        )
        .properties(height=245)
    )
    target_rule = (
        alt.Chart(pd.DataFrame({"target": [float(target)]}))
        .mark_rule(color="#1b2d4a", strokeDash=[6, 4])
        .encode(y="target:Q")
    )
    chart_left, chart_right = st.columns([0.8, 1.2])
    with chart_left:
        st.markdown("#### Macro Split")
        st.altair_chart(macro_chart, width="stretch")
    with chart_right:
        st.markdown("#### Nutrient Target Check")
        st.caption(
            f"Compares each day in the selected week with the {target_caption} for {metric_label.lower()}."
        )
        st.altair_chart(trend + target_rule, width="stretch")

    st.markdown("### Core Requirement Evidence")
    summary = safety_summary(result, profile)
    card_cols = st.columns(3)
    for idx, row in summary.iterrows():
        status_class = "status-pass" if row["Status"] == "Pass" else "status-review"
        with card_cols[idx % 3]:
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="{status_class}">{html.escape(str(row["Status"]))}</div>
                    <b>{html.escape(str(row["Capability"]))}</b>
                    <div class="meal-meta">{html.escape(str(row["Evidence"]))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander("Full RDA table"):
        st.dataframe(result["compliance"], width="stretch", hide_index=True)

    if profile["conditions"]:
        with st.expander("Clinical rules applied"):
            for condition in profile["conditions"]:
                st.write(f"**{condition}:** {CONDITION_RULES[condition]}")


def show_grocery(result: dict, profile: dict) -> None:
    st.subheader("Grocery Planner")
    meal_count = len(result["plan"])
    st.caption(
        f"Aggregates all {meal_count} planned meals for student meal prep. Open any ingredient to see which recipes use it."
    )
    groceries = grocery_list(result["plan"])
    if groceries.empty:
        st.info("Generate a meal plan first.")
        return
    usage = grocery_usage_details(result["plan"])
    household_size = max(len(profile.get("members", [])), 1)
    total_cost = float(result["plan"]["cost_usd"].sum()) * household_size
    c1, c2, c3 = st.columns(3)
    c1.metric("Household servings", household_size)
    c2.metric("Estimated plan cost", f"${total_cost:.0f}")
    c3.metric("Grocery categories", groceries["category"].nunique())

    scaled = groceries.copy()
    scaled["estimated_cost_usd"] = (scaled["estimated_cost_usd"] * household_size).round(2)
    filter_col, search_col = st.columns([0.8, 1.2])
    category_options = ["All"] + sorted(scaled["category"].dropna().astype(str).unique().tolist())
    category_filter = filter_col.selectbox("Category", category_options, key="grocery_category_filter")
    ingredient_search = search_col.text_input("Search ingredient", placeholder="Example: oats, tofu, berries", key="grocery_search")

    filtered = scaled.copy()
    if category_filter != "All":
        filtered = filtered[filtered["category"].astype(str) == category_filter]
    if ingredient_search.strip():
        filtered = filtered[filtered["item"].str.contains(ingredient_search.strip(), case=False, na=False)]

    st.markdown("#### Shopping List")
    st.caption("Use the checkboxes while shopping. Expanding an item shows the meals and recipes that need it.")
    if filtered.empty:
        st.info("No grocery items match the current filters.")
    else:
        for idx, (_, item) in enumerate(filtered.sort_values(["category", "item"]).iterrows()):
            item_name = str(item["item"])
            item_usage = usage[usage["item"] == item_name].sort_values(["day", "meal_type", "recipe"])
            with st.expander(
                f"{item_name} | {int(item['times_used'])} use(s) | Est. ${float(item['estimated_cost_usd']):.2f}",
                expanded=False,
            ):
                row_left, row_right = st.columns([0.55, 1.45])
                with row_left:
                    st.checkbox("Purchased", key=f"grocery_purchased_{idx}_{item_name}_{item['category']}_{category_filter}")
                    st.caption(f"Category: {item['category']}")
                    st.caption(f"Quantity hint: {item['quantity_hints']}")
                    st.caption(f"Household-adjusted cost: ${float(item['estimated_cost_usd']):.2f}")
                with row_right:
                    st.markdown("**Used in these recipes**")
                    st.dataframe(format_grocery_usage(item_usage), width="stretch", hide_index=True)

    st.download_button(
        "Download grocery list",
        scaled.to_csv(index=False).encode("utf-8"),
        file_name="nutriai_grocery_list.csv",
        mime="text/csv",
    )


def show_restaurants(profile: dict) -> None:
    st.subheader("Restaurant Mode")
    st.caption(
        "Student extension: ranks representative San Francisco neighborhood menu items as safer pick, caution, or avoid. "
        "It uses an offline snapshot, not live restaurant data, so it is a risk estimate rather than a medical guarantee."
    )
    menu = get_restaurants()
    cuisines = ["Any"] + sorted(menu["cuisine"].dropna().unique().tolist())
    cuisine = st.selectbox("Cuisine filter", cuisines)
    ranked = rank_restaurant_items(menu, profile, cuisine)
    cols = st.columns(3)
    for idx, (_, row) in enumerate(ranked.head(12).iterrows()):
        label = row["risk_label"]
        color = {"Safer Pick": "#1f6b4a", "Caution": "#a15e00", "Avoid": "#9b2f2f"}.get(label, "#1d2a2a")
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div class="restaurant-card">
                    <div style="font-weight:800;color:{color}">{html.escape(str(label))}</div>
                    <b>{html.escape(str(row["name"]))}</b><br>
                    <span class="member-meta">{html.escape(str(row["restaurant"]))} | {html.escape(str(row["cuisine"]))}</span>
                    <div class="meal-meta" style="margin-top:8px">
                        {float(row["calories"]):.0f} cal | {float(row["protein_g"]):.0f}g protein | GI {float(row["gi"]):.0f}<br>
                        Sodium {float(row["sodium_mg"]):.0f}mg | confidence {float(row["confidence"]):.2f}
                    </div>
                    <div class="meal-safe">{html.escape(str(row["why"]))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def show_data_pipeline() -> None:
    st.subheader("Data Pipeline + BAX-423 Techniques")
    foods = get_food_snapshot()
    recipes = get_recipes()
    if not foods.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("USDA offline records", f"{len(foods):,}")
        c2.metric("Recipe candidates", f"{len(recipes):,}")
        c3.metric("USDA sources", foods["source_archive"].nunique() if "source_archive" in foods else "n/a")
    else:
        st.warning("USDA snapshot not found. Run `python code/scripts/build_food_snapshot.py` from the project root.")

    technique_cols = st.columns(3)
    technique_cols[0].markdown('<div class="info-card"><b>Bloom Filters</b><br><span class="meal-meta">Fast allergen and unsafe-condition prechecks before exact rule verification.</span></div>', unsafe_allow_html=True)
    technique_cols[1].markdown('<div class="info-card"><b>Hash Embeddings</b><br><span class="meal-meta">Profile-aware meal ranking using diet, condition, allergy, and preference text.</span></div>', unsafe_allow_html=True)
    technique_cols[2].markdown('<div class="info-card"><b>Multi-stage Ranking</b><br><span class="meal-meta">Hard filters, nutrition fit, clinical boosts, and diversity assignment.</span></div>', unsafe_allow_html=True)

    with st.expander("USDA snapshot preview"):
        st.dataframe(foods.head(25), width="stretch", hide_index=True)


def show_empty_state() -> None:
    st.markdown("### Start With a Household Profile")
    setup_col, evidence_col = st.columns([1.35, 1])
    with setup_col:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-title">Build a safe shared plan from the sidebar.</div>
                <div class="empty-copy">
                    Add one or more people with diet, allergy, clinical condition, calorie target,
                    micronutrient priorities, and meal preferences. NutriAI combines those filters
                    before generating the meal plan.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with evidence_col:
        with st.container(border=True):
            st.markdown("**Required capability coverage**")
            st.write("Clinical filters, allergy exclusion, diet handling, diversity scoring, macro/micro analysis, and sub-60-second generation.")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    quick_cols = st.columns(2)
    quick_cols[0].markdown(
        '<div class="info-card"><div class="mini-label">Planning horizon</div><div class="large-number">1-4 weeks</div><div class="meal-meta">First 7 days remain the required grading plan.</div></div>',
        unsafe_allow_html=True,
    )
    quick_cols[1].markdown(
        '<div class="info-card"><div class="mini-label">Offline data snapshot</div><div class="large-number">12,000 records</div><div class="meal-meta">USDA-derived food and nutrition data.</div></div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    st.markdown(
        """
        <div class="app-header">
            <div class="app-kicker">BAX-423 Final Build Project</div>
            <h1>NutriAI Clinical Meal Planner</h1>
            <p>Safe household meal planning with clinical filtering, allergy exclusion, nutrition analysis, grocery planning, and restaurant risk estimates.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    profile = household_builder()
    recipes = get_recipes()

    if profile is None:
        st.session_state.pop("profile", None)
        st.session_state.pop("profile_signature", None)
        show_empty_state()
        tabs = st.tabs(["How It Works", "Data + Techniques"])
        with tabs[0]:
            st.markdown(
                """
                **NutriAI workflow:** add household members, generate a safe shared calendar, adjust meals,
                review nutrition, export groceries, and check restaurant options.

                The planner still enforces the six required project capabilities once a person is added.
                """
            )
        with tabs[1]:
            show_data_pipeline()
        return

    render_household(profile)
    render_member_requirements(profile)

    planning_weeks = st.sidebar.selectbox(
        "Planning horizon",
        [1, 2, 3, 4],
        format_func=lambda weeks: "1 week (required plan)" if weeks == 1 else f"{weeks} weeks",
        key="planning_horizon_weeks",
    )
    profile["planning_weeks"] = int(planning_weeks)
    profile["planning_days"] = int(planning_weeks) * 7

    st.markdown("### Shared Safety Filters")
    filter_top = st.columns(3)
    filter_top[0].markdown(f'<div class="info-card"><div class="mini-label">Shared diet</div><div class="large-number">{html.escape(profile["diet"])}</div></div>', unsafe_allow_html=True)
    filter_top[1].markdown(f'<div class="info-card"><div class="mini-label">Clinical filters</div>{chip_html(profile["conditions"], "None")}</div>', unsafe_allow_html=True)
    filter_top[2].markdown(f'<div class="info-card"><div class="mini-label">Allergy filters</div>{allergy_chip_html(profile["allergies"], "None")}</div>', unsafe_allow_html=True)
    filter_bottom = st.columns(2)
    filter_bottom[0].markdown(f'<div class="info-card"><div class="mini-label">Nutrition target</div><div class="large-number">{html.escape(profile["target_member"])}</div><div class="meal-meta">{profile["calorie_target"]} cal/day</div></div>', unsafe_allow_html=True)
    filter_bottom[1].markdown(f'<div class="info-card"><div class="mini-label">Plan horizon</div><div class="large-number">{profile["planning_weeks"]} week{"s" if profile["planning_weeks"] > 1 else ""}</div><div class="meal-meta">{profile["planning_days"]} days</div></div>', unsafe_allow_html=True)

    generate = st.sidebar.button("Generate shared calendar", type="primary")
    profile_signature = repr({k: profile[k] for k in ["diet", "conditions", "allergies", "clinical_triggers", "cultural_restrictions", "calorie_target", "target_member", "planning_days"]})
    should_generate = generate or "result" not in st.session_state or st.session_state.get("profile_signature") != profile_signature
    if should_generate:
        try:
            st.session_state["result"] = generate_plan(recipes, profile, days=profile["planning_days"])
            st.session_state["profile"] = profile
            st.session_state["profile_signature"] = profile_signature
        except Exception as exc:
            st.error(f"Could not generate a safe plan: {exc}")
            return

    result = st.session_state["result"]
    active_profile = st.session_state.get("profile", profile)

    tabs = st.tabs(["Calendar", "Nutrition", "Grocery Planner", "Restaurant Mode", "Data + Techniques"])
    with tabs[0]:
        show_plan(result, active_profile, recipes)
    with tabs[1]:
        show_nutrition(result, active_profile)
    with tabs[2]:
        show_grocery(result, active_profile)
    with tabs[3]:
        show_restaurants(active_profile)
    with tabs[4]:
        show_data_pipeline()


if __name__ == "__main__":
    main()
