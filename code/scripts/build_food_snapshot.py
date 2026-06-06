from __future__ import annotations

import argparse
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

SOURCES = {
    "foundation_2026": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_2026-04-30.zip",
    "sr_legacy_2018": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip",
    "survey_2024": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_survey_food_csv_2024-10-31.zip",
}

NUTRIENT_IDS = {
    203: "protein_g",
    204: "fat_g",
    205: "carbs_g",
    208: "calories",
    291: "fiber_g",
    301: "calcium_mg",
    303: "iron_mg",
    304: "magnesium_mg",
    306: "potassium_mg",
    307: "sodium_mg",
    309: "zinc_mg",
    324: "vitamin_d_mcg",
    328: "vitamin_d_mcg",
    418: "b12_mcg",
    1008: "calories",
    1003: "protein_g",
    1005: "carbs_g",
    1004: "fat_g",
    1079: "fiber_g",
    1089: "iron_mg",
    1087: "calcium_mg",
    1178: "b12_mcg",
    1114: "vitamin_d_mcg",
    1095: "zinc_mg",
    1093: "sodium_mg",
    1092: "potassium_mg",
    1090: "magnesium_mg",
}


def download(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as response:
        path.write_bytes(response.read())


def read_member(zf: zipfile.ZipFile, suffix: str) -> pd.DataFrame:
    names = [name for name in zf.namelist() if Path(name).name == suffix]
    if not names:
        raise FileNotFoundError(suffix)
    with zf.open(names[0]) as fh:
        return pd.read_csv(fh, low_memory=False)


def process_archive(name: str, zip_path: Path) -> pd.DataFrame:
    print(f"Processing {name}")
    with zipfile.ZipFile(zip_path) as zf:
        food = read_member(zf, "food.csv")[["fdc_id", "data_type", "description", "food_category_id"]]
        nutrients = read_member(zf, "food_nutrient.csv")[["fdc_id", "nutrient_id", "amount"]]

    nutrients = nutrients[nutrients["nutrient_id"].isin(NUTRIENT_IDS)]
    pivot = (
        nutrients.pivot_table(index="fdc_id", columns="nutrient_id", values="amount", aggfunc="mean")
        .rename(columns=NUTRIENT_IDS)
        .reset_index()
    )
    pivot = pivot.T.groupby(level=0).first().T
    merged = food.merge(pivot, on="fdc_id", how="inner")
    merged["source_archive"] = name
    merged["description_norm"] = merged["description"].str.lower().str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()
    merged = merged.drop_duplicates("description_norm")
    return merged


def add_rule_metadata(df: pd.DataFrame) -> pd.DataFrame:
    text = df["description"].str.lower().fillna("")
    df = df.copy()
    df["contains_gluten_keyword"] = text.str.contains(r"\bwheat\b|\bbarley\b|\brye\b|\bspelt\b|\bflour\b|\bbread\b|\bpasta\b")
    df["contains_dairy_keyword"] = text.str.contains(r"\bmilk\b|\bcheese\b|\byogurt\b|\bcream\b|\bbutter\b|\blactose\b")
    df["contains_tree_nut_keyword"] = text.str.contains(r"almond|cashew|walnut|pistachio|pecan|hazelnut|macadamia")
    df["contains_soy_keyword"] = text.str.contains(r"\bsoy\b|tofu|tempeh|edamame")
    df["contains_egg_keyword"] = text.str.contains(r"\begg\b")
    df["contains_fish_keyword"] = text.str.contains(r"salmon|tuna|cod|trout|sardine|fish")
    df["ibs_trigger_keyword"] = text.str.contains(r"garlic|onion|wheat|milk|apple|pear|mango|cauliflower|mushroom")
    df["gerd_trigger_keyword"] = text.str.contains(r"tomato|citrus|orange|lemon|coffee|chocolate|pepper|fried|spicy")
    df["diabetes_caution"] = (df.get("fiber_g", 0).fillna(0) < 2) & (df.get("carbs_g", 0).fillna(0) > 35)
    df["hypertension_caution"] = df.get("sodium_mg", 0).fillna(0) > 600
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=12000)
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    for name, url in SOURCES.items():
        zip_path = RAW_DIR / f"{name}.zip"
        download(url, zip_path)
        frames.append(process_archive(name, zip_path))

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates("description_norm")
    required = ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "iron_mg", "calcium_mg", "sodium_mg"]
    for col in required:
        if col not in combined:
            combined[col] = 0
    combined = combined.dropna(subset=["calories", "protein_g", "carbs_g", "fat_g"])
    combined = add_rule_metadata(combined)
    combined = combined.sort_values(["source_archive", "fdc_id"]).head(args.limit)
    combined = combined.drop(columns=["description_norm"])
    out = DATA_DIR / "food_snapshot.csv"
    combined.to_csv(out, index=False)
    print(f"Wrote {len(combined):,} USDA-derived records to {out}")


if __name__ == "__main__":
    main()
