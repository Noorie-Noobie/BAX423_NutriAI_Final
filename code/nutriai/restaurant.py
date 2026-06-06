from __future__ import annotations

from pathlib import Path

import pandas as pd

from .rules import explain_exclusion, parse_tags


def load_restaurant_menu(data_dir: Path) -> pd.DataFrame:
    return pd.read_csv(data_dir / "restaurant_menu_snapshot.csv")


def restaurant_risk_label(row: pd.Series, profile: dict) -> tuple[str, str]:
    reasons = explain_exclusion(row, profile, profile.get("diet", "Non-Vegetarian"))
    caution_notes = []
    if float(row.get("confidence", 0.75)) < 0.8:
        caution_notes.append("Nutrition/allergen data is estimated from menu labels.")
    if "Hypertension" in profile.get("conditions", []) and float(row.get("sodium_mg", 0)) > 700:
        caution_notes.append("High sodium for a DASH-style meal.")
    if "Type 2 Diabetes" in profile.get("conditions", []) and float(row.get("gi", 100)) > 55:
        caution_notes.append("GI estimate is above the low-GI target.")

    if reasons:
        return "Avoid", "; ".join(reasons)
    if caution_notes or parse_tags(row.get("cross_contact_risks", "")):
        return "Caution", "; ".join(caution_notes or ["Possible cross-contact risk. Ask staff before ordering."])
    return "Safer Pick", "Matches the declared diet, allergy, and clinical filters based on available menu data."


def rank_restaurant_items(menu: pd.DataFrame, profile: dict, cuisine: str | None = None) -> pd.DataFrame:
    filtered = menu.copy()
    if cuisine and cuisine != "Any":
        filtered = filtered[filtered["cuisine"].str.lower() == cuisine.lower()]
    labels = []
    notes = []
    scores = []
    for _, row in filtered.iterrows():
        label, note = restaurant_risk_label(row, profile)
        labels.append(label)
        notes.append(note)
        score = {"Safer Pick": 3, "Caution": 2, "Avoid": 0}[label]
        score += min(float(row.get("protein_g", 0)) / 35, 1)
        score += min(float(row.get("fiber_g", 0)) / 10, 1)
        score -= min(float(row.get("sodium_mg", 0)) / 1500, 1)
        score += float(row.get("confidence", 0.75))
        scores.append(score)
    ranked = filtered.assign(risk_label=labels, why=notes, score=scores)
    return ranked.sort_values(["risk_label", "score"], ascending=[False, False])

