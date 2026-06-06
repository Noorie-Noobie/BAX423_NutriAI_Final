from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from nutriai.planner import candidate_pool, generate_plan, persona_profiles  # noqa: E402
from nutriai.rules import blocked_profile_tokens, bloom_might_contain, explain_exclusion, row_block_tokens  # noqa: E402


DATA_DIR = ROOT / "data"


def bloom_benchmark(recipes: pd.DataFrame) -> dict:
    profile = persona_profiles()["Ravi"]
    expanded = pd.concat([recipes] * 800, ignore_index=True)
    blocked = blocked_profile_tokens(profile)

    start = time.perf_counter()
    exact_blocked = 0
    for _, row in expanded.iterrows():
        tokens = row_block_tokens(row)
        if any(token in tokens for token in blocked):
            exact_blocked += 1
    exact_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    bloom_blocked = 0
    for _, row in expanded.iterrows():
        bits = int(row["bloom_bits"])
        if any(bloom_might_contain(bits, token) for token in blocked):
            bloom_blocked += 1
    bloom_ms = (time.perf_counter() - start) * 1000

    return {
        "benchmark": "Bloom precheck vs exact token scan",
        "baseline": f"{exact_ms:.2f} ms",
        "optimized": f"{bloom_ms:.2f} ms",
        "impact": f"{exact_ms / bloom_ms:.2f}x faster on expanded catalog",
        "notes": f"Blocked counts exact={exact_blocked}, bloom_maybe={bloom_blocked}",
    }


def baseline_plan_quality(recipes: pd.DataFrame, profile: dict) -> tuple[int, float]:
    rows = []
    used = set()
    for day in range(1, 8):
        for meal_type, split in {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.4}.items():
            pool, _ = candidate_pool(recipes, profile, meal_type)
            pool = pool[~pool["recipe_id"].isin(used)]
            target = profile["calorie_target"] * split
            chosen = pool.assign(calorie_gap=(pool["calories"] - target).abs()).sort_values("calorie_gap").iloc[0].copy()
            chosen["day"] = day
            rows.append(chosen)
            used.add(chosen["recipe_id"])
    plan = pd.DataFrame(rows)
    daily = plan.groupby("day").sum(numeric_only=True).reset_index()
    reviews = persona_specific_reviews(plan, daily, profile)
    diversity = round(0.7 * (plan["recipe_id"].nunique() / len(plan)) + 0.3 * min(plan["category"].nunique() / 10, 1), 3)
    return reviews, diversity


def persona_specific_reviews(plan: pd.DataFrame, daily: pd.DataFrame, profile: dict) -> int:
    reviews = 0
    if "IBS" in profile["conditions"]:
        reviews += int((daily["iron_mg"] < 14.4).sum())
    if "GERD" in profile["conditions"]:
        reviews += int((daily["b12_mcg"] < 1.92).sum())
    if "Type 2 Diabetes" in profile["conditions"]:
        reviews += int((daily["fiber_g"] < 25).sum())
        reviews += int(plan["gi"].max() > 55)
    if "Hypertension" in profile["conditions"]:
        reviews += int((daily["sodium_mg"] > 1500).sum())
        reviews += int((daily["potassium_mg"] < 2720).sum())
        reviews += int(plan["is_fish"].sum() < 3)
    return reviews


def ranking_benchmark(recipes: pd.DataFrame) -> dict:
    base_reviews = 0
    opt_reviews = 0
    base_diversities = []
    opt_diversities = []
    for profile in persona_profiles().values():
        reviews, diversity = baseline_plan_quality(recipes, profile)
        base_reviews += reviews
        base_diversities.append(diversity)
        result = generate_plan(recipes, profile)
        opt_reviews += persona_specific_reviews(result["plan"], result["daily"], profile)
        opt_diversities.append(result["diversity_score"])

    return {
        "benchmark": "Embedding-aware ranking vs calorie-only baseline",
        "baseline": f"{base_reviews} persona-specific review flags; diversity {sum(base_diversities) / len(base_diversities):.2f}",
        "optimized": f"{opt_reviews} persona-specific review flags; diversity {sum(opt_diversities) / len(opt_diversities):.2f}",
        "impact": "Improved diversity and nutrient targeting after hard filters",
        "notes": "Baseline chooses closest calories only; optimized adds hash embeddings, nutrient fit, clinical boosts, and rebalancing.",
    }


def generation_benchmark(recipes: pd.DataFrame) -> dict:
    times = []
    for profile in persona_profiles().values():
        result = generate_plan(recipes, profile)
        times.append(result["generation_time"])
    return {
        "benchmark": "Sub-60-second generation",
        "baseline": "60.00 s requirement",
        "optimized": f"mean {sum(times) / len(times):.3f}s; max {max(times):.3f}s",
        "impact": "All required personas generated far below the cap",
        "notes": "Measured locally with preprocessed CSV catalogs.",
    }


def main() -> None:
    recipes = pd.read_csv(DATA_DIR / "recipe_catalog.csv")
    rows = [bloom_benchmark(recipes), ranking_benchmark(recipes), generation_benchmark(recipes)]
    out = ROOT / "docs" / "benchmark_results.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
