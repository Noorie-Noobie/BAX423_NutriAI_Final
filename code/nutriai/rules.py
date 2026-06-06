from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


ALLERGENS = [
    "gluten",
    "dairy",
    "lactose",
    "tree_nuts",
    "peanuts",
    "shellfish",
    "soy",
    "eggs",
    "fish",
]

CONDITIONS = ["IBS", "GERD", "Type 2 Diabetes", "Hypertension"]

DIETS = ["Vegan", "Vegetarian", "Pescatarian", "Non-Vegetarian"]


CONDITION_RULES = {
    "IBS": "Low-FODMAP screen: excludes onion, garlic, wheat-heavy foods, high-lactose dairy, and other high-FODMAP triggers.",
    "GERD": "GERD screen: excludes tomato/citrus, caffeine, chocolate, fried foods, spicy foods, and very high-fat meals.",
    "Type 2 Diabetes": "Diabetes screen: requires low glycaemic index meals, low added sugar, and fiber-forward choices.",
    "Hypertension": "DASH screen: requires low sodium, lower saturated fat, and potassium/magnesium-forward choices.",
}


NUTRIENT_COLUMNS = [
    "calories",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "iron_mg",
    "calcium_mg",
    "b12_mcg",
    "vitamin_d_mcg",
    "zinc_mg",
    "sodium_mg",
    "potassium_mg",
    "magnesium_mg",
]


def parse_tags(value: object) -> set[str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return set()
    text = str(value).strip()
    if not text:
        return set()
    return {part.strip().lower() for part in re.split(r"[;,|]", text) if part.strip()}


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def diet_allowed(row: pd.Series, diet: str) -> bool:
    allowed = parse_tags(row.get("allowed_diets", ""))
    return diet.lower() in allowed


def cultural_allowed(row: pd.Series, restrictions: Iterable[str]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    recipe_tags = parse_tags(row.get("allergens", "")) | parse_tags(row.get("risk_tags", ""))
    for restriction in restrictions:
        key = normalize_token(restriction)
        if key in {"no_pork", "halal"} and "pork" in recipe_tags:
            reasons.append("Contains pork, which conflicts with the declared restriction.")
        if key in {"no_beef", "hindu"} and "beef" in recipe_tags:
            reasons.append("Contains beef, which conflicts with the declared restriction.")
    return not reasons, reasons


def rda_targets(age: int, sex: str) -> dict[str, float]:
    """Compact adult RDA/AI table used for project benchmarking.

    Values are standard adult targets sufficient for course-level comparison.
    The app flags days below 80 percent of these values.
    """
    female = sex.lower().startswith("f")
    older = age >= 51
    return {
        "protein_g": 46.0 if female else 56.0,
        "fiber_g": 25.0 if female else 38.0,
        "iron_mg": 8.0 if older else (18.0 if female else 8.0),
        "calcium_mg": 1200.0 if older else 1000.0,
        "b12_mcg": 2.4,
        "vitamin_d_mcg": 15.0,
        "zinc_mg": 8.0 if female else 11.0,
        "potassium_mg": 2600.0 if female else 3400.0,
        "magnesium_mg": 320.0 if female else 420.0,
        "sodium_mg": 1500.0,
    }


class BloomFilter:
    def __init__(self, size: int = 256, hashes: int = 4) -> None:
        self.size = size
        self.hashes = hashes
        self.bits = 0

    def _positions(self, token: str) -> list[int]:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        positions = []
        for i in range(self.hashes):
            start = i * 4
            positions.append(int.from_bytes(digest[start : start + 4], "big") % self.size)
        return positions

    def add(self, token: str) -> None:
        for pos in self._positions(token):
            self.bits |= 1 << pos

    def might_contain(self, token: str) -> bool:
        return all(self.bits & (1 << pos) for pos in self._positions(token))


def build_bloom_bits(tokens: Iterable[str]) -> int:
    bloom = BloomFilter()
    for token in tokens:
        bloom.add(token)
    return bloom.bits


def bloom_might_contain(bits: int, token: str, size: int = 256, hashes: int = 4) -> bool:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    for i in range(hashes):
        start = i * 4
        pos = int.from_bytes(digest[start : start + 4], "big") % size
        if not bits & (1 << pos):
            return False
    return True


def row_block_tokens(row: pd.Series) -> set[str]:
    tokens = set()
    for allergen in parse_tags(row.get("allergens", "")):
        tokens.add(f"allergen:{allergen}")
    for risk in parse_tags(row.get("risk_tags", "")):
        tokens.add(f"risk:{risk}")
    for condition in CONDITIONS:
        col = condition_flag_col(condition)
        if int(row.get(col, 1)) == 0:
            tokens.add(f"unsafe:{normalize_token(condition)}")
    return tokens


def condition_flag_col(condition: str) -> str:
    return {
        "IBS": "ibs_safe",
        "GERD": "gerd_safe",
        "Type 2 Diabetes": "diabetes_safe",
        "Hypertension": "hypertension_safe",
    }[condition]


def blocked_profile_tokens(profile: dict) -> set[str]:
    tokens = {f"allergen:{a}" for a in profile.get("allergies", [])}
    for condition in profile.get("conditions", []):
        tokens.add(f"unsafe:{normalize_token(condition)}")
    return tokens


def hash_embedding(text: str, dims: int = 128) -> np.ndarray:
    vector = np.zeros(dims, dtype=float)
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]+", text.lower())
    for token in tokens:
        digest = hashlib.md5(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % dims
        sign = 1 if digest[4] % 2 else -1
        vector[idx] += sign
    norm = np.linalg.norm(vector)
    if norm:
        vector /= norm
    return vector


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if not np.any(a) or not np.any(b):
        return 0.0
    return float(np.dot(a, b))


@dataclass
class Exclusion:
    recipe_id: str
    name: str
    meal_type: str
    reasons: list[str]


def explain_exclusion(row: pd.Series, profile: dict, meal_diet: str | None = None) -> list[str]:
    reasons: list[str] = []
    diet = meal_diet or profile.get("diet", "Non-Vegetarian")
    if not diet_allowed(row, diet):
        reasons.append(f"Not compatible with {diet.lower()} mode.")

    allergens = parse_tags(row.get("allergens", ""))
    cross = parse_tags(row.get("cross_contact_risks", ""))
    for allergen in profile.get("allergies", []):
        if allergen in allergens:
            reasons.append(f"Contains {allergen.replace('_', ' ')}.")
        if profile.get("strict_cross_contact", True) and allergen in cross:
            reasons.append(f"Cross-contamination risk for {allergen.replace('_', ' ')}.")

    for condition in profile.get("conditions", []):
        flag_col = condition_flag_col(condition)
        if int(row.get(flag_col, 1)) == 0:
            if condition == "IBS":
                triggers = [t.replace("High-FODMAP: ", "") for t in profile.get("clinical_triggers", []) if str(t).startswith("High-FODMAP: ")]
                if triggers:
                    reasons.append(f"{CONDITION_RULES[condition]} Active high-FODMAP flags: {', '.join(triggers)}.")
                else:
                    reasons.append(CONDITION_RULES[condition])
            else:
                reasons.append(CONDITION_RULES[condition])

    ok, cultural_reasons = cultural_allowed(row, profile.get("cultural_restrictions", []))
    if not ok:
        reasons.extend(cultural_reasons)

    return reasons
