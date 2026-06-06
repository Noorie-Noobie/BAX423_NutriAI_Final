from __future__ import annotations

import io
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .rules import (
    CONDITIONS,
    NUTRIENT_COLUMNS,
    blocked_profile_tokens,
    bloom_might_contain,
    cosine_similarity,
    explain_exclusion,
    hash_embedding,
    parse_tags,
    rda_targets,
    row_block_tokens,
)


MEAL_SPLITS = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.40}


def load_recipe_catalog(data_dir: Path) -> pd.DataFrame:
    recipes = pd.read_csv(data_dir / "recipe_catalog.csv")
    if "bloom_bits" not in recipes:
        recipes["bloom_bits"] = recipes.apply(lambda r: str(build_recipe_bloom(r)), axis=1)
    return recipes


def build_recipe_bloom(row: pd.Series) -> int:
    from .rules import build_bloom_bits

    return build_bloom_bits(row_block_tokens(row))


def load_food_snapshot(data_dir: Path) -> pd.DataFrame:
    path = data_dir / "food_snapshot.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def profile_query(profile: dict) -> str:
    pieces = [
        profile.get("diet", ""),
        " ".join(profile.get("conditions", [])),
        " ".join(profile.get("allergies", [])),
        " ".join(profile.get("micro_priorities", [])),
        profile.get("preferences", ""),
    ]
    return " ".join(pieces)


def candidate_pool(
    recipes: pd.DataFrame, profile: dict, meal_type: str, meal_diet: str | None = None
) -> tuple[pd.DataFrame, list]:
    blocked = blocked_profile_tokens(profile)
    rows = []
    exclusions = []
    for _, row in recipes[recipes["meal_type"] == meal_type].iterrows():
        bits = int(row.get("bloom_bits", 0))
        bloom_clear = True
        for token in blocked:
            if bloom_might_contain(bits, token):
                bloom_clear = False
                break
        reasons = [] if bloom_clear else explain_exclusion(row, profile, meal_diet)
        if bloom_clear:
            reasons = explain_exclusion(row, profile, meal_diet)
        if reasons:
            exclusions.append(
                {
                    "recipe_id": row["recipe_id"],
                    "name": row["name"],
                    "meal_type": row["meal_type"],
                    "reasons": "; ".join(reasons),
                }
            )
        else:
            rows.append(row)
    pool = pd.DataFrame(rows)
    return pool, exclusions


def score_candidates(pool: pd.DataFrame, profile: dict, meal_type: str, used_categories: Iterable[str]) -> pd.DataFrame:
    if pool.empty:
        return pool
    query = hash_embedding(profile_query(profile))
    target_calories = float(profile["calorie_target"]) * MEAL_SPLITS[meal_type]
    used_categories = set(used_categories)

    scored = pool.copy()
    sims = []
    for _, row in scored.iterrows():
        text = " ".join(
            [
                str(row.get("name", "")),
                str(row.get("category", "")),
                str(row.get("cuisine", "")),
                str(row.get("tags", "")),
                str(row.get("ingredients", "")),
            ]
        )
        sims.append(cosine_similarity(query, hash_embedding(text)))
    scored["embedding_similarity"] = sims

    calorie_fit = 1 - np.minimum(np.abs(scored["calories"] - target_calories) / max(target_calories, 1), 1)
    protein_fit = np.minimum(scored["protein_g"] / max(16, target_calories / 45), 1)
    fiber_fit = np.minimum(scored["fiber_g"] / 8, 1)
    sodium_fit = 1 - np.minimum(scored["sodium_mg"] / 900, 1)
    diversity_bonus = scored["category"].apply(lambda c: 0.15 if c not in used_categories else -0.2)

    score = 0.32 * calorie_fit + 0.18 * protein_fit + 0.12 * fiber_fit + 0.18 * scored["embedding_similarity"]
    score += 0.12 * sodium_fit + diversity_bonus

    if "Type 2 Diabetes" in profile.get("conditions", []):
        score += np.where(scored["gi"] <= 55, 0.18, -1.0)
    if "Hypertension" in profile.get("conditions", []):
        score += np.where(scored["sodium_mg"] <= 500, 0.2, -1.0)
        score += np.minimum(scored["potassium_mg"] / 1200, 1) * 0.12
    if "IBS" in profile.get("conditions", []):
        score += np.where(scored["ibs_safe"] == 1, 0.18, -1.0)
    if "GERD" in profile.get("conditions", []):
        score += np.where(scored["gerd_safe"] == 1, 0.18, -1.0)

    scored["score"] = score
    return scored.sort_values(["score", "calories"], ascending=[False, False])


def daily_targets(profile: dict) -> dict[str, float]:
    targets = rda_targets(int(profile["age"]), profile["sex"])
    targets["calories"] = float(profile["calorie_target"])
    return targets


def summarize_day(day_rows: pd.DataFrame) -> dict[str, float]:
    return {col: float(day_rows[col].sum()) for col in NUTRIENT_COLUMNS if col in day_rows}


def generate_plan(recipes: pd.DataFrame, profile: dict, days: int = 7) -> dict:
    start = time.perf_counter()
    days = max(7, min(int(days), 28))
    used_ids: set[str] = set()
    used_counts: dict[str, int] = {}
    used_categories: list[str] = []
    exclusions = []
    plan_rows = []
    pools: dict[str, pd.DataFrame] = {}

    for meal_type in MEAL_SPLITS:
        meal_diet = profile.get("meal_diets", {}).get(meal_type, profile.get("diet", "Non-Vegetarian"))
        pool, meal_exclusions = candidate_pool(recipes, profile, meal_type, meal_diet)
        exclusions.extend(meal_exclusions)
        if pool.empty:
            raise ValueError(f"No safe {meal_type.lower()} candidates for this profile.")
        pools[meal_type] = pool

    targets = daily_targets(profile)
    for day in range(1, days + 1):
        day_selected = []
        for meal_type in MEAL_SPLITS:
            scored = score_candidates(
                pools[meal_type][~pools[meal_type]["recipe_id"].isin(used_ids)],
                profile,
                meal_type,
                used_categories,
            )
            if scored.empty:
                scored = score_candidates(pools[meal_type], profile, meal_type, used_categories)
                usage_penalty = scored["recipe_id"].map(lambda recipe_id: used_counts.get(str(recipe_id), 0)).astype(float)
                scored = scored.assign(score=scored["score"] - (0.65 * usage_penalty))
                scored = scored.sort_values(["score", "calories"], ascending=[False, False])
            chosen = scored.iloc[0].copy()
            chosen["day"] = day
            used_ids.add(str(chosen["recipe_id"]))
            used_counts[str(chosen["recipe_id"])] = used_counts.get(str(chosen["recipe_id"]), 0) + 1
            used_categories.append(str(chosen["category"]))
            day_selected.append(chosen)
        plan_rows.extend(day_selected)

        day_df = pd.DataFrame(day_selected)
        day_totals = summarize_day(day_df)
        if "Type 2 Diabetes" in profile.get("conditions", []) and day_totals.get("fiber_g", 0) < 25:
            plan_rows = rebalance_day_for_metric(plan_rows, pools, profile, day, "fiber_g", 25, used_ids, used_categories)
        if "Hypertension" in profile.get("conditions", []):
            plan_rows = rebalance_day_for_metric(
                plan_rows, pools, profile, day, "potassium_mg", targets["potassium_mg"] * 0.8, used_ids, used_categories
            )
            plan_rows = lower_sodium_day(plan_rows, pools, profile, day, used_ids, used_categories)
        if "IBS" in profile.get("conditions", []):
            plan_rows = rebalance_day_for_metric(
                plan_rows, pools, profile, day, "iron_mg", targets["iron_mg"] * 0.8, used_ids, used_categories
            )
        if "GERD" in profile.get("conditions", []):
            plan_rows = rebalance_day_for_metric(
                plan_rows, pools, profile, day, "b12_mcg", targets["b12_mcg"] * 0.8, used_ids, used_categories
            )

    plan = pd.DataFrame(plan_rows).sort_values(["day", "meal_type"])
    plan["day_label"] = plan["day"].apply(lambda d: f"Day {d}")
    daily = plan.groupby("day")[NUTRIENT_COLUMNS].sum().reset_index()
    compliance = build_compliance_table(daily, profile)
    generation_time = time.perf_counter() - start
    diversity_score = compute_diversity_score(plan)
    required_week = plan[plan["day"] <= 7]
    required_week_diversity_score = compute_diversity_score(required_week)

    return {
        "plan": plan,
        "daily": daily,
        "compliance": compliance,
        "exclusions": pd.DataFrame(exclusions).drop_duplicates().head(80),
        "generation_time": generation_time,
        "diversity_score": diversity_score,
        "required_week_diversity_score": required_week_diversity_score,
        "horizon_days": days,
        "targets": targets,
    }


def rebalance_day_for_metric(
    plan_rows: list[pd.Series],
    pools: dict[str, pd.DataFrame],
    profile: dict,
    day: int,
    metric: str,
    threshold: float,
    used_ids: set[str],
    used_categories: list[str],
) -> list[pd.Series]:
    current = pd.DataFrame([r for r in plan_rows if int(r["day"]) == day])
    if current.empty or current[metric].sum() >= threshold:
        return plan_rows
    weakest_idx = current[metric].astype(float).idxmin()
    weakest_meal = current.loc[weakest_idx, "meal_type"]
    available = pools[weakest_meal][~pools[weakest_meal]["recipe_id"].isin(used_ids)]
    if available.empty:
        return plan_rows
    scored = score_candidates(available, profile, weakest_meal, used_categories)
    scored = scored.sort_values([metric, "score"], ascending=[False, False])
    replacement = scored.iloc[0].copy()
    replacement["day"] = day
    new_rows = []
    replaced = False
    for row in plan_rows:
        if int(row["day"]) == day and row["meal_type"] == weakest_meal and not replaced:
            new_rows.append(replacement)
            used_ids.add(str(replacement["recipe_id"]))
            used_categories.append(str(replacement["category"]))
            replaced = True
        else:
            new_rows.append(row)
    return new_rows


def lower_sodium_day(
    plan_rows: list[pd.Series],
    pools: dict[str, pd.DataFrame],
    profile: dict,
    day: int,
    used_ids: set[str],
    used_categories: list[str],
) -> list[pd.Series]:
    current = pd.DataFrame([r for r in plan_rows if int(r["day"]) == day])
    if current.empty or current["sodium_mg"].sum() <= 1500:
        return plan_rows
    highest_idx = current["sodium_mg"].astype(float).idxmax()
    highest_meal = current.loc[highest_idx, "meal_type"]
    available = pools[highest_meal][~pools[highest_meal]["recipe_id"].isin(used_ids)]
    if available.empty:
        return plan_rows
    replacement = available.sort_values(["sodium_mg", "potassium_mg"], ascending=[True, False]).iloc[0].copy()
    replacement["day"] = day
    new_rows = []
    replaced = False
    for row in plan_rows:
        if int(row["day"]) == day and row["meal_type"] == highest_meal and not replaced:
            new_rows.append(replacement)
            used_ids.add(str(replacement["recipe_id"]))
            used_categories.append(str(replacement["category"]))
            replaced = True
        else:
            new_rows.append(row)
    return new_rows


def compute_diversity_score(plan: pd.DataFrame) -> float:
    total = len(plan)
    unique_meals = plan["recipe_id"].nunique()
    unique_categories = plan["category"].nunique()
    category_score = min(unique_categories / 10, 1.0)
    repeat_score = unique_meals / max(total, 1)
    return round(0.7 * repeat_score + 0.3 * category_score, 3)


def build_compliance_table(daily: pd.DataFrame, profile: dict) -> pd.DataFrame:
    targets = daily_targets(profile)
    rows = []
    for _, day in daily.iterrows():
        day_id = int(day["day"])
        for metric in [
            "calories",
            "protein_g",
            "fiber_g",
            "iron_mg",
            "calcium_mg",
            "b12_mcg",
            "vitamin_d_mcg",
            "zinc_mg",
            "potassium_mg",
            "magnesium_mg",
        ]:
            if metric not in day or metric not in targets:
                continue
            target = targets[metric] * (0.8 if metric != "calories" else 1.0)
            value = float(day[metric])
            rows.append(
                {
                    "day": day_id,
                    "metric": metric,
                    "value": round(value, 2),
                    "target": round(target, 2),
                    "status": "Pass" if value >= target else "Review",
                }
            )
        if "Hypertension" in profile.get("conditions", []):
            rows.append(
                {
                    "day": day_id,
                    "metric": "sodium_mg_cap",
                    "value": round(float(day["sodium_mg"]), 2),
                    "target": 1500,
                    "status": "Pass" if float(day["sodium_mg"]) <= 1500 else "Review",
                }
            )
    return pd.DataFrame(rows)


def grocery_list(plan: pd.DataFrame) -> pd.DataFrame:
    items = []
    for _, row in plan.iterrows():
        for raw in str(row.get("shopping_items", "")).split(";"):
            raw = raw.strip()
            if not raw:
                continue
            if ":" in raw:
                name, qty = raw.split(":", 1)
            else:
                name, qty = raw, "1 serving"
            ingredients = [part.strip().title() for part in name.split(",") if part.strip()]
            ingredient_cost = float(row.get("cost_usd", 0)) / max(len(ingredients), 1)
            for ingredient in ingredients:
                items.append(
                    {
                        "item": ingredient,
                        "quantity_hint": qty.strip(),
                        "used_in": row["name"],
                        "category": row.get("grocery_category", "General"),
                        "estimated_cost_usd": round(ingredient_cost, 2),
                    }
                )
    if not items:
        return pd.DataFrame()
    grocery = pd.DataFrame(items)
    summary = (
        grocery.groupby(["category", "item"])
        .agg(
            times_used=("used_in", "count"),
            quantity_hints=("quantity_hint", lambda x: ", ".join(sorted(set(x))[:3])),
            estimated_cost_usd=("estimated_cost_usd", "sum"),
        )
        .reset_index()
        .sort_values(["category", "item"])
    )
    return summary


def plan_to_csv_bytes(plan: pd.DataFrame, daily: pd.DataFrame) -> bytes:
    output = io.StringIO()
    output.write("Meal Plan\n")
    plan.to_csv(output, index=False)
    output.write("\nDaily Nutrient Totals\n")
    daily.to_csv(output, index=False)
    return output.getvalue().encode("utf-8")


def persona_profiles() -> dict[str, dict]:
    base = {
        "age": 25,
        "sex": "Female",
        "strict_cross_contact": True,
        "cultural_restrictions": [],
        "preferences": "student budget meal prep",
    }
    return {
        "Priya": {
            **base,
            "diet": "Vegetarian",
            "conditions": ["IBS"],
            "allergies": ["dairy", "lactose"],
            "calorie_target": 1800,
            "micro_priorities": ["iron_mg", "calcium_mg", "vitamin_d_mcg"],
            "meal_diets": {},
        },
        "Ravi": {
            **base,
            "age": 28,
            "sex": "Male",
            "diet": "Non-Vegetarian",
            "conditions": ["GERD"],
            "allergies": ["gluten"],
            "calorie_target": 2200,
            "micro_priorities": ["b12_mcg", "zinc_mg", "magnesium_mg"],
            "cultural_restrictions": ["No pork"],
            "meal_diets": {},
        },
        "Mei": {
            **base,
            "diet": "Vegan",
            "conditions": ["Type 2 Diabetes"],
            "allergies": ["tree_nuts"],
            "calorie_target": 1600,
            "micro_priorities": ["b12_mcg", "iron_mg", "zinc_mg"],
            "meal_diets": {},
        },
        "James": {
            **base,
            "age": 31,
            "sex": "Male",
            "diet": "Pescatarian",
            "conditions": ["Hypertension"],
            "allergies": ["soy"],
            "calorie_target": 2000,
            "micro_priorities": ["potassium_mg", "magnesium_mg"],
            "meal_diets": {},
        },
    }
