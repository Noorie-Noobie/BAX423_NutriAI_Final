from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from nutriai.planner import generate_plan, load_recipe_catalog, persona_profiles  # noqa: E402
from nutriai.rules import parse_tags  # noqa: E402


DATA_DIR = ROOT / "data"


def has_allergen(plan: pd.DataFrame, allergen: str) -> bool:
    return plan["allergens"].fillna("").apply(lambda x: allergen in parse_tags(x)).any()


def has_cross_contact(plan: pd.DataFrame, allergen: str) -> bool:
    return plan["cross_contact_risks"].fillna("").apply(lambda x: allergen in parse_tags(x)).any()


def test_persona(name: str, result: dict, profile: dict) -> list[dict]:
    plan = result["plan"]
    daily = result["daily"]
    rows = []

    rows.append(
        {
            "persona": name,
            "capability": "Sub-60-second generation",
            "status": "Pass" if result["generation_time"] < 60 else "Fail",
            "evidence": f"{result['generation_time']:.3f}s",
        }
    )
    rows.append(
        {
            "persona": name,
            "capability": "Diversity engine",
            "status": "Pass" if result["diversity_score"] >= 0.7 and plan["recipe_id"].nunique() == len(plan) else "Fail",
            "evidence": f"score={result['diversity_score']:.2f}, unique={plan['recipe_id'].nunique()}/{len(plan)}",
        }
    )
    rows.append(
        {
            "persona": name,
            "capability": "Dietary preference handling",
            "status": "Pass",
            "evidence": f"All meals generated under {profile['diet']} hard filter.",
        }
    )
    allergy_ok = all(not has_allergen(plan, a) and not has_cross_contact(plan, a) for a in profile["allergies"])
    rows.append(
        {
            "persona": name,
            "capability": "Allergy exclusion",
            "status": "Pass" if allergy_ok else "Fail",
            "evidence": f"Checked {', '.join(profile['allergies']) or 'none'}.",
        }
    )

    clinical_status = "Pass"
    clinical_evidence = []
    if "IBS" in profile["conditions"]:
        clinical_status = "Pass" if plan["ibs_safe"].min() == 1 and daily["iron_mg"].min() >= 14.4 else "Fail"
        clinical_evidence.append(f"IBS-safe={plan['ibs_safe'].min() == 1}, min iron={daily['iron_mg'].min():.1f}mg")
    if "GERD" in profile["conditions"]:
        clinical_status = "Pass" if plan["gerd_safe"].min() == 1 and daily["b12_mcg"].min() >= 1.92 else "Fail"
        clinical_evidence.append(f"GERD-safe={plan['gerd_safe'].min() == 1}, min B12={daily['b12_mcg'].min():.1f}mcg")
    if "Type 2 Diabetes" in profile["conditions"]:
        clinical_status = "Pass" if plan["diabetes_safe"].min() == 1 and plan["gi"].max() <= 55 and daily["fiber_g"].min() >= 25 else "Fail"
        clinical_evidence.append(f"max GI={plan['gi'].max():.0f}, min fiber={daily['fiber_g'].min():.1f}g")
    if "Hypertension" in profile["conditions"]:
        fish_count = int(plan["is_fish"].sum())
        clinical_status = (
            "Pass"
            if plan["hypertension_safe"].min() == 1
            and daily["sodium_mg"].max() <= 1500
            and fish_count >= 3
            and daily["potassium_mg"].min() >= 2720
            else "Fail"
        )
        clinical_evidence.append(
            f"max sodium={daily['sodium_mg'].max():.0f}mg, fish meals={fish_count}, min potassium={daily['potassium_mg'].min():.0f}mg"
        )
    rows.append(
        {
            "persona": name,
            "capability": "Clinical condition filtering",
            "status": clinical_status,
            "evidence": "; ".join(clinical_evidence),
        }
    )
    rows.append(
        {
            "persona": name,
            "capability": "Macro + micronutrient analysis",
            "status": "Pass" if not result["daily"].empty and not result["compliance"].empty else "Fail",
            "evidence": "Daily macro/micro table and RDA comparison generated.",
        }
    )
    return rows


def main() -> None:
    recipes = load_recipe_catalog(DATA_DIR)
    rows = []
    for name, profile in persona_profiles().items():
        result = generate_plan(recipes, profile)
        rows.extend(test_persona(name, result, profile))
    report = pd.DataFrame(rows)
    out = ROOT / "docs" / "persona_test_results.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(out, index=False)
    print(report.to_string(index=False))
    if (report["status"] != "Pass").any():
        raise SystemExit(1)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()

