from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from nutriai.rules import build_bloom_bits, row_block_tokens  # noqa: E402


DATA_DIR = ROOT / "data"


def allowed_for(kind: str) -> str:
    if kind == "vegan":
        return "vegan;vegetarian;pescatarian;non-vegetarian"
    if kind == "vegetarian":
        return "vegetarian;pescatarian;non-vegetarian"
    if kind == "pescatarian":
        return "pescatarian;non-vegetarian"
    return "non-vegetarian"


def row(
    recipe_id: str,
    name: str,
    meal_type: str,
    category: str,
    cuisine: str,
    kind: str,
    ingredients: str,
    shopping: str,
    cost: float,
    calories: int,
    protein: float,
    carbs: float,
    fat: float,
    fiber: float,
    iron: float,
    calcium: float,
    b12: float,
    vitamin_d: float,
    zinc: float,
    sodium: int,
    potassium: int,
    magnesium: int,
    gi: int,
    allergens: str = "",
    cross: str = "",
    risk_tags: str = "",
    ibs_safe: int = 1,
    gerd_safe: int = 1,
    diabetes_safe: int = 1,
    hypertension_safe: int = 1,
    is_fish: int = 0,
    tags: str = "",
) -> dict:
    data = {
        "recipe_id": recipe_id,
        "name": name,
        "meal_type": meal_type,
        "category": category,
        "cuisine": cuisine,
        "allowed_diets": allowed_for(kind),
        "ingredients": ingredients,
        "shopping_items": shopping,
        "grocery_category": category,
        "cost_usd": cost,
        "calories": calories,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
        "fiber_g": fiber,
        "iron_mg": iron,
        "calcium_mg": calcium,
        "b12_mcg": b12,
        "vitamin_d_mcg": vitamin_d,
        "zinc_mg": zinc,
        "sodium_mg": sodium,
        "potassium_mg": potassium,
        "magnesium_mg": magnesium,
        "gi": gi,
        "allergens": allergens,
        "cross_contact_risks": cross,
        "risk_tags": risk_tags,
        "ibs_safe": ibs_safe,
        "gerd_safe": gerd_safe,
        "diabetes_safe": diabetes_safe,
        "hypertension_safe": hypertension_safe,
        "is_fish": is_fish,
        "tags": tags,
    }
    data["bloom_bits"] = build_bloom_bits(row_block_tokens(data))
    return data


def build_recipes() -> list[dict]:
    recipes: list[dict] = []

    ibs_breakfasts = [
        ("Low-FODMAP Oat Chia Bowl", "oats, chia, pumpkin seeds, blueberries", 420, 17, 58, 13, 10, 5.4, 340, 0.4, 3.2, 3.8, 120, 790, 185, 48),
        ("Spinach Egg Quinoa Plate", "eggs, quinoa, spinach, bell pepper", 455, 24, 42, 19, 7, 5.9, 280, 1.1, 3.8, 3.3, 230, 840, 170, 45),
        ("Buckwheat Berry Breakfast", "buckwheat, strawberries, hemp seeds, fortified oat milk", 435, 18, 61, 12, 9, 5.2, 410, 1.2, 4.0, 3.4, 150, 760, 190, 49),
        ("Rice Cake Egg Stack", "eggs, rice cakes, spinach, avocado", 410, 22, 39, 18, 6, 4.8, 230, 1.0, 3.6, 3.0, 260, 810, 150, 52),
        ("Kiwi Pumpkin Seed Porridge", "certified gluten-free oats, kiwi, pumpkin seeds", 430, 16, 63, 13, 10, 6.0, 300, 0.3, 2.6, 4.1, 110, 860, 210, 50),
        ("Egg White Millet Bowl", "egg whites, millet, spinach, carrots", 405, 27, 47, 10, 7, 5.0, 260, 0.8, 2.8, 3.2, 240, 780, 160, 51),
        ("Cinnamon Teff Bowl", "teff, chia, blueberries, fortified rice milk", 440, 18, 66, 12, 9, 6.4, 420, 1.1, 4.1, 4.0, 130, 790, 205, 48),
        ("Savory Polenta Egg Bowl", "polenta, eggs, kale, olive oil", 430, 21, 49, 17, 7, 5.7, 300, 1.0, 3.2, 3.1, 250, 830, 155, 54),
    ]
    for i, item in enumerate(ibs_breakfasts, 1):
        recipes.append(row(f"IBSB{i:02d}", item[0], "Breakfast", "Breakfast Bowls", "Student Prep", "vegetarian", item[1], f"{item[1]}:1 serving", 4.2, *item[2:], allergens="eggs" if "Egg" in item[0] else "", cross="gluten" if "Oat" in item[0] else "", tags="low fodmap iron rich dairy free"))

    ibs_lunches = [
        ("Quinoa Tofu Spinach Bowl", "quinoa, firm tofu, spinach, carrots", 610, 34, 72, 20, 11, 7.4, 430, 1.3, 3.6, 4.8, 420, 1180, 240, 47, "soy"),
        ("Egg Fried Rice Without Garlic", "rice, eggs, carrots, scallion greens", 590, 27, 76, 18, 6, 6.2, 290, 1.4, 3.2, 3.5, 470, 890, 160, 55, "eggs"),
        ("Millet Paneer-Free Power Bowl", "millet, pumpkin seeds, kale, cucumber", 575, 22, 74, 20, 10, 7.0, 450, 0.8, 3.0, 4.4, 360, 1060, 230, 50, ""),
        ("Tempeh Rice Noodle Bowl", "rice noodles, tempeh, bok choy, ginger", 620, 33, 78, 19, 8, 6.8, 360, 1.4, 3.1, 4.2, 500, 970, 210, 51, "soy"),
        ("Soba-Style Buckwheat Bowl", "100 percent buckwheat noodles, eggs, spinach", 600, 28, 82, 17, 9, 6.5, 310, 1.2, 3.4, 3.8, 430, 920, 205, 52, "eggs"),
        ("Chickpea-Free Greek Rice Bowl", "rice, eggs, cucumber, olives, spinach", 585, 25, 73, 20, 7, 6.0, 300, 1.2, 3.2, 3.4, 480, 880, 160, 53, "eggs"),
        ("Potato Kale Tofu Plate", "potatoes, firm tofu, kale, carrots", 610, 31, 70, 21, 10, 7.2, 420, 1.4, 3.7, 4.7, 390, 1250, 245, 54, "soy"),
        ("Quinoa Egg Bento", "quinoa, boiled eggs, spinach, pumpkin seeds", 600, 30, 68, 22, 9, 7.1, 350, 1.3, 3.8, 4.5, 410, 990, 225, 48, "eggs"),
    ]
    for i, item in enumerate(ibs_lunches, 1):
        recipes.append(row(f"IBSL{i:02d}", item[0], "Lunch", "Grain Bowls", "Student Prep", "vegetarian", item[1], f"{item[1]}:1 serving", 5.8, *item[2:16], allergens=item[16], tags="low fodmap iron rich meal prep"))

    ibs_dinners = [
        ("Low-FODMAP Tofu Rice Dinner", "firm tofu, jasmine rice, zucchini, carrots", 690, 36, 82, 24, 9, 7.5, 430, 1.5, 3.8, 4.9, 520, 1220, 250, 50, "soy"),
        ("Eggplant-Free Quinoa Skillet", "quinoa, eggs, spinach, bell pepper", 650, 31, 76, 22, 9, 7.0, 340, 1.4, 3.4, 4.1, 460, 1030, 225, 49, "eggs"),
        ("Millet Lentil-Free Curry", "millet, tofu, carrots, ginger", 675, 34, 80, 23, 8, 7.2, 390, 1.3, 3.5, 4.6, 500, 1080, 230, 51, "soy"),
        ("Polenta Spinach Egg Plate", "polenta, eggs, spinach, pumpkin seeds", 640, 29, 72, 24, 8, 7.6, 360, 1.5, 3.7, 4.5, 430, 980, 220, 54, "eggs"),
        ("Buckwheat Tofu Stir Plate", "buckwheat, tofu, bok choy, ginger", 665, 35, 78, 23, 10, 7.4, 410, 1.4, 3.8, 4.9, 480, 1130, 245, 47, "soy"),
        ("Rice Pasta Spinach Bake", "rice pasta, eggs, spinach, herbs", 680, 30, 88, 22, 7, 6.8, 330, 1.3, 3.2, 3.8, 500, 900, 190, 55, "eggs"),
        ("Teff Veggie Dinner Bowl", "teff, tofu, carrots, kale", 655, 34, 75, 22, 10, 7.8, 440, 1.3, 3.5, 5.0, 460, 1180, 255, 48, "soy"),
        ("Pumpkin Seed Risotto Bowl", "arborio rice, spinach, pumpkin seeds, eggs", 670, 28, 84, 24, 7, 7.5, 350, 1.2, 3.4, 4.2, 450, 990, 215, 53, "eggs"),
    ]
    for i, item in enumerate(ibs_dinners, 1):
        recipes.append(row(f"IBSD{i:02d}", item[0], "Dinner", "Warm Plates", "Student Prep", "vegetarian", item[1], f"{item[1]}:1 serving", 6.4, *item[2:16], allergens=item[16], tags="low fodmap high iron dairy free"))

    diabetes_breakfasts = [
        ("Steel-Cut Oats With Hemp", "steel-cut oats, hemp seeds, berries, fortified soy milk", 390, 20, 48, 13, 12, 5.2, 380, 1.8, 3.6, 3.5, 170, 760, 210, 42, "soy"),
        ("Tofu Veggie Breakfast Hash", "tofu, sweet potato, spinach, peppers", 410, 25, 44, 15, 10, 5.9, 420, 1.5, 3.2, 4.0, 310, 1120, 230, 45, "soy"),
        ("Lentil Breakfast Bowl", "lentils, quinoa, kale, nutritional yeast", 405, 24, 52, 10, 14, 6.2, 310, 2.0, 2.8, 4.3, 300, 980, 240, 36, ""),
        ("Chia Berry Soy Yogurt", "chia, berries, unsweetened soy yogurt", 370, 19, 38, 15, 13, 5.0, 360, 1.5, 3.0, 3.6, 210, 760, 220, 34, "soy"),
        ("Barley-Free Bean Toast Bowl", "black beans, corn tortilla, avocado", 420, 20, 54, 14, 15, 5.4, 250, 1.5, 2.6, 3.8, 330, 1080, 230, 40, ""),
        ("Quinoa Cinnamon Breakfast", "quinoa, flax, berries, fortified oat milk", 395, 18, 50, 14, 11, 5.5, 360, 1.7, 3.4, 3.5, 180, 820, 220, 43, ""),
        ("Savory Chickpea Scramble", "chickpea flour, spinach, nutritional yeast", 410, 23, 46, 13, 12, 6.0, 320, 2.1, 3.1, 4.1, 340, 1000, 235, 35, ""),
        ("Edamame Oat Bowl", "oats, edamame, blueberries, flax", 400, 24, 46, 14, 12, 5.4, 310, 1.4, 2.8, 3.7, 270, 860, 210, 44, "soy"),
    ]
    for i, item in enumerate(diabetes_breakfasts, 1):
        recipes.append(row(f"DIAB{i:02d}", item[0], "Breakfast", "Low-GI Breakfast", "Student Prep", "vegan", item[1], f"{item[1]}:1 serving", 4.6, *item[2:16], allergens=item[16], tags="low gi vegan high fiber b12 fortified"))

    diabetes_lunches = [
        ("Lentil Quinoa Power Bowl", "lentils, quinoa, kale, nutritional yeast", 540, 30, 67, 14, 18, 7.8, 360, 2.2, 3.4, 5.0, 430, 1280, 285, 38, ""),
        ("Black Bean Brown Rice Bowl", "black beans, brown rice, avocado, peppers", 560, 24, 78, 16, 17, 6.8, 290, 1.6, 2.6, 4.3, 460, 1300, 260, 45, ""),
        ("Tofu Veggie Quinoa Bowl", "tofu, quinoa, broccoli, sesame", 555, 35, 58, 20, 13, 7.0, 520, 1.7, 3.2, 4.8, 500, 1160, 260, 42, "soy"),
        ("Chickpea Cucumber Bowl", "chickpeas, farro-free quinoa, cucumber", 535, 24, 70, 15, 16, 6.9, 270, 1.5, 2.6, 4.2, 420, 1120, 245, 39, ""),
        ("Split Pea Soup Bowl", "split peas, carrots, spinach, herbs", 520, 29, 72, 10, 19, 7.2, 300, 1.5, 2.8, 4.6, 480, 1320, 275, 32, ""),
        ("Tempeh Buckwheat Bowl", "tempeh, buckwheat, greens, ginger", 565, 36, 58, 21, 13, 7.1, 360, 1.6, 3.0, 5.1, 520, 1080, 250, 44, "soy"),
        ("Bean Taco Salad", "pinto beans, corn tortilla, romaine, salsa verde", 545, 25, 72, 15, 18, 6.6, 280, 1.4, 2.4, 4.4, 470, 1220, 250, 41, ""),
        ("Mushroom Lentil Bowl", "lentils, mushrooms, millet, spinach", 550, 30, 68, 15, 17, 7.4, 330, 1.5, 2.9, 4.7, 450, 1240, 270, 37, ""),
    ]
    for i, item in enumerate(diabetes_lunches, 1):
        recipes.append(row(f"DIAL{i:02d}", item[0], "Lunch", "Low-GI Bowls", "Student Prep", "vegan", item[1], f"{item[1]}:1 serving", 5.2, *item[2:16], allergens=item[16], ibs_safe=0 if "chickpeas" in item[1] or "beans" in item[1] or "lentils" in item[1] else 1, tags="low gi vegan high fiber"))

    diabetes_dinners = [
        ("Bean Chili Without Sugar", "kidney beans, black beans, quinoa, peppers", 610, 31, 82, 14, 22, 8.4, 330, 1.8, 2.8, 5.3, 540, 1440, 305, 36, ""),
        ("Tofu Broccoli Brown Rice", "tofu, broccoli, brown rice, sesame", 625, 38, 66, 22, 13, 7.5, 540, 1.7, 3.2, 5.2, 520, 1260, 285, 48, "soy"),
        ("Lentil Millet Stew", "lentils, millet, spinach, carrots", 600, 32, 78, 13, 20, 8.0, 340, 1.7, 2.9, 5.0, 500, 1360, 300, 34, ""),
        ("Chickpea Cauliflower Curry", "chickpeas, cauliflower, brown rice", 620, 27, 82, 17, 18, 7.4, 300, 1.5, 2.6, 4.6, 560, 1260, 280, 42, ""),
        ("Tempeh Vegetable Plate", "tempeh, sweet potato, kale", 615, 37, 62, 24, 14, 7.2, 390, 1.6, 3.1, 5.4, 530, 1300, 290, 44, "soy"),
        ("Quinoa Stuffed Peppers", "quinoa, lentils, peppers, nutritional yeast", 600, 30, 76, 15, 19, 8.1, 350, 2.2, 3.0, 5.2, 490, 1290, 295, 39, ""),
        ("Black Bean Sweet Potato Plate", "black beans, sweet potato, greens", 615, 28, 84, 14, 21, 7.6, 310, 1.5, 2.7, 4.8, 520, 1500, 310, 46, ""),
        ("Pea Protein Pasta Bowl", "lentil pasta, spinach, mushrooms", 605, 36, 70, 17, 17, 7.8, 340, 1.4, 2.6, 5.0, 480, 1180, 270, 45, ""),
    ]
    for i, item in enumerate(diabetes_dinners, 1):
        recipes.append(row(f"DIAD{i:02d}", item[0], "Dinner", "Low-GI Dinners", "Student Prep", "vegan", item[1], f"{item[1]}:1 serving", 5.9, *item[2:16], allergens=item[16], ibs_safe=0, tags="low gi vegan high fiber b12 fortified"))

    gerd_breakfasts = [
        ("Banana Oat Egg Bowl", "gluten-free oats, banana, eggs", 500, 26, 62, 16, 7, 3.8, 280, 1.2, 3.8, 3.1, 220, 830, 170, 54, "eggs", "gluten"),
        ("Turkey Breakfast Rice", "turkey, rice, spinach, egg", 535, 36, 50, 18, 5, 4.2, 240, 1.8, 3.4, 4.4, 340, 860, 160, 55, "eggs", ""),
        ("Egg Potato Spinach Plate", "eggs, potatoes, spinach", 505, 27, 48, 22, 6, 4.8, 260, 1.4, 3.6, 3.5, 310, 1010, 170, 54, "eggs", ""),
        ("Chicken Breakfast Congee", "chicken, rice, ginger, bok choy", 520, 35, 58, 13, 4, 3.5, 180, 0.8, 1.4, 3.8, 360, 780, 140, 55, "", ""),
        ("Greek Yogurt Free Smoothie", "banana, pea protein, oat milk", 480, 30, 55, 14, 8, 4.6, 360, 1.2, 3.2, 3.4, 250, 870, 170, 51, "", ""),
        ("Salmon Egg Rice Cake", "salmon, eggs, rice cakes", 510, 34, 42, 22, 3, 3.4, 220, 3.5, 8.0, 3.6, 360, 760, 140, 53, "eggs;fish", ""),
        ("Turkey Quinoa Breakfast", "turkey, quinoa, spinach", 530, 38, 50, 16, 6, 4.4, 230, 1.0, 1.8, 4.2, 390, 890, 180, 50, "", ""),
        ("Egg Millet Bowl", "eggs, millet, zucchini", 500, 27, 56, 18, 6, 4.1, 230, 1.3, 3.6, 3.3, 300, 760, 160, 52, "eggs", ""),
    ]
    for i, item in enumerate(gerd_breakfasts, 1):
        recipes.append(row(f"GERB{i:02d}", item[0], "Breakfast", "Gentle Breakfast", "Student Prep", "non-vegetarian", item[1], f"{item[1]}:1 serving", 5.0, *item[2:16], allergens=item[16], cross=item[17], ibs_safe=0 if "banana" in item[1].lower() else 1, tags="gluten free gerd gentle b12"))

    gerd_lunches = [
        ("Chicken Quinoa Cucumber Bowl", "chicken, quinoa, cucumber, spinach", 690, 48, 72, 19, 8, 5.0, 260, 0.7, 1.5, 5.0, 520, 1100, 230, 50, ""),
        ("Turkey Rice Bowl", "turkey, brown rice, carrots", 710, 50, 78, 18, 7, 4.8, 220, 1.0, 1.5, 5.2, 560, 980, 210, 54, ""),
        ("Salmon Quinoa Plate", "salmon, quinoa, zucchini", 720, 46, 64, 28, 7, 4.6, 260, 4.8, 11.0, 4.9, 500, 1120, 220, 48, "fish"),
        ("Chicken Rice Noodle Bowl", "chicken, rice noodles, bok choy", 700, 45, 82, 16, 5, 4.0, 210, 0.6, 1.2, 4.5, 540, 900, 180, 55, ""),
        ("Turkey Potato Plate", "turkey, potatoes, spinach", 695, 49, 70, 18, 8, 5.4, 240, 1.0, 1.6, 5.1, 570, 1280, 230, 54, ""),
        ("Tuna Rice Bowl", "tuna, rice, cucumber, avocado", 680, 44, 73, 21, 6, 3.8, 190, 3.2, 6.5, 4.4, 560, 980, 190, 53, "fish"),
        ("Chicken Millet Bowl", "chicken, millet, spinach, carrots", 705, 47, 76, 18, 8, 5.2, 240, 0.6, 1.3, 4.8, 530, 1080, 220, 51, ""),
        ("Egg Turkey Bento", "turkey, eggs, rice, cucumber", 700, 50, 65, 23, 4, 4.1, 240, 2.1, 4.0, 5.0, 590, 870, 160, 54, "eggs"),
    ]
    for i, item in enumerate(gerd_lunches, 1):
        recipes.append(row(f"GERL{i:02d}", item[0], "Lunch", "Lean Plates", "Student Prep", "non-vegetarian", item[1], f"{item[1]}:1 serving", 6.8, *item[2:16], allergens=item[16], tags="gluten free gerd gentle lean protein", is_fish=1 if "fish" in item[16] else 0))

    gerd_dinners = [
        ("Baked Salmon Rice Dinner", "salmon, rice, green beans", 795, 50, 75, 30, 6, 4.5, 250, 5.2, 12.0, 5.1, 560, 1120, 220, 52, "fish"),
        ("Chicken Potato Dinner", "chicken, potatoes, spinach", 790, 55, 78, 24, 8, 5.0, 240, 0.8, 1.8, 5.3, 600, 1300, 240, 54, ""),
        ("Turkey Quinoa Dinner", "turkey, quinoa, carrots, zucchini", 780, 54, 76, 23, 8, 5.2, 230, 1.0, 1.6, 5.2, 580, 1100, 230, 50, ""),
        ("Cod Polenta Plate", "cod, polenta, spinach", 760, 48, 80, 20, 6, 4.8, 240, 2.5, 5.5, 4.6, 540, 980, 200, 54, "fish"),
        ("Chicken Brown Rice Bowl", "chicken, brown rice, bok choy", 785, 53, 82, 21, 7, 4.7, 220, 0.7, 1.4, 5.0, 570, 1060, 220, 53, ""),
        ("Turkey Millet Skillet", "turkey, millet, spinach, squash", 770, 52, 78, 22, 8, 5.1, 230, 1.0, 1.6, 5.2, 580, 1150, 235, 51, ""),
        ("Trout Rice Plate", "trout, rice, carrots, spinach", 790, 50, 74, 29, 6, 4.6, 240, 5.0, 12.0, 5.0, 560, 1070, 215, 52, "fish"),
        ("Chicken Quinoa Tray", "chicken, quinoa, zucchini, olive oil", 800, 55, 76, 25, 7, 5.0, 240, 0.8, 1.7, 5.4, 590, 1050, 225, 50, ""),
    ]
    for i, item in enumerate(gerd_dinners, 1):
        recipes.append(row(f"GERD{i:02d}", item[0], "Dinner", "Gentle Dinners", "Student Prep", "non-vegetarian", item[1], f"{item[1]}:1 serving", 7.4, *item[2:16], allergens=item[16], tags="gluten free gerd gentle b12", is_fish=1 if "fish" in item[16] else 0))

    ht_breakfasts = [
        ("Potassium Oat Banana Bowl", "oats, banana, chia, fortified oat milk", 470, 18, 69, 13, 11, 4.8, 370, 1.4, 3.4, 3.5, 120, 1180, 230, 50),
        ("Avocado Egg Potato Bowl", "eggs, potatoes, avocado, spinach", 500, 24, 54, 22, 10, 4.8, 260, 1.2, 3.6, 3.3, 280, 1420, 210, 54),
        ("Berry Hemp Breakfast", "oats, berries, hemp, fortified milk", 455, 19, 62, 14, 10, 4.6, 360, 1.3, 3.4, 3.6, 130, 1080, 220, 49),
        ("Spinach Mushroom Omelet", "eggs, spinach, mushrooms, potatoes", 490, 26, 46, 22, 7, 4.4, 260, 1.4, 3.8, 3.5, 290, 1240, 190, 52),
        ("Quinoa Breakfast Bowl", "quinoa, banana, flax, berries", 470, 17, 66, 14, 10, 4.7, 280, 0.5, 2.4, 3.4, 110, 1120, 235, 48),
        ("Sweet Potato Egg Plate", "sweet potato, eggs, kale", 485, 23, 52, 21, 8, 4.5, 240, 1.3, 3.5, 3.2, 280, 1330, 195, 53),
        ("Millet Fruit Bowl", "millet, banana, pumpkin seeds", 465, 18, 64, 14, 9, 5.0, 290, 0.4, 2.4, 3.8, 120, 1030, 230, 51),
        ("Low-Sodium Breakfast Hash", "potatoes, egg, kale, avocado", 495, 24, 50, 23, 9, 4.6, 260, 1.2, 3.5, 3.4, 260, 1400, 205, 52),
    ]
    for i, item in enumerate(ht_breakfasts, 1):
        recipes.append(row(f"HTB{i:02d}", item[0], "Breakfast", "DASH Breakfast", "Student Prep", "vegetarian", item[1], f"{item[1]}:1 serving", 4.8, *item[2:], allergens="eggs" if "Egg" in item[0] or "Omelet" in item[0] else "", cross="gluten" if "Oat" in item[0] else "", tags="dash low sodium potassium rich"))

    ht_lunches = [
        ("Salmon Sweet Potato Bowl", "salmon, sweet potato, spinach", 680, 43, 63, 26, 10, 4.6, 260, 4.8, 11.0, 4.5, 390, 1580, 260, 48, "fish"),
        ("Trout Quinoa Kale Bowl", "trout, quinoa, kale, avocado", 675, 44, 58, 28, 10, 4.8, 280, 5.0, 12.0, 4.8, 380, 1480, 270, 46, "fish"),
        ("Cod Potato Spinach Plate", "cod, potatoes, spinach", 650, 42, 70, 18, 9, 4.3, 240, 2.3, 5.0, 4.1, 360, 1530, 245, 52, "fish"),
        ("Tuna Avocado Rice Bowl", "tuna, brown rice, avocado, cucumber", 660, 43, 68, 22, 9, 4.0, 220, 3.4, 7.0, 4.2, 410, 1360, 230, 50, "fish"),
        ("Sardine-Free Pescatarian Bowl", "white fish, quinoa, greens, sweet potato", 670, 45, 64, 24, 10, 4.5, 260, 4.0, 9.0, 4.6, 370, 1550, 265, 47, "fish"),
        ("Chickpea Avocado Bowl", "chickpeas, quinoa, avocado, spinach", 650, 24, 78, 23, 17, 6.8, 280, 0.8, 2.4, 4.6, 390, 1460, 285, 42, ""),
        ("Egg Potato Greens Bowl", "eggs, potatoes, kale, avocado", 640, 28, 62, 28, 10, 5.0, 260, 1.4, 3.8, 3.7, 400, 1440, 230, 53, "eggs"),
        ("Quinoa Bean DASH Bowl", "black beans, quinoa, spinach, avocado", 655, 27, 82, 21, 18, 6.9, 290, 0.8, 2.5, 4.7, 380, 1520, 295, 43, ""),
    ]
    for i, item in enumerate(ht_lunches, 1):
        recipes.append(row(f"HTL{i:02d}", item[0], "Lunch", "DASH Bowls", "Student Prep", "pescatarian" if "fish" in item[16] else "vegetarian", item[1], f"{item[1]}:1 serving", 6.2, *item[2:16], allergens=item[16], ibs_safe=0 if "chickpeas" in item[1] or "beans" in item[1] else 1, tags="dash low sodium potassium rich", is_fish=1 if "fish" in item[16] else 0))

    ht_dinners = [
        ("Baked Salmon Potato Dinner", "salmon, potatoes, spinach, olive oil", 720, 46, 66, 30, 9, 4.6, 260, 5.2, 12.0, 4.9, 430, 1610, 270, 50, "fish"),
        ("Trout Sweet Potato Dinner", "trout, sweet potato, kale", 710, 45, 64, 29, 10, 4.7, 270, 5.0, 12.0, 4.8, 420, 1660, 275, 48, "fish"),
        ("Cod Quinoa Dinner", "cod, quinoa, spinach, avocado", 700, 44, 68, 24, 10, 4.5, 260, 2.5, 5.5, 4.4, 390, 1520, 260, 49, "fish"),
        ("Shrimp-Free Fish Rice Plate", "white fish, rice, greens, potatoes", 710, 45, 76, 22, 8, 4.3, 250, 3.0, 6.5, 4.3, 410, 1500, 240, 52, "fish"),
        ("Tuna Potato Kale Dinner", "tuna, potatoes, kale, avocado", 715, 46, 66, 28, 10, 4.4, 260, 3.6, 7.0, 4.7, 430, 1600, 265, 50, "fish"),
        ("Quinoa Lentil DASH Stew", "lentils, quinoa, spinach, sweet potato", 700, 32, 86, 18, 20, 8.0, 330, 0.9, 2.6, 5.0, 440, 1700, 320, 38, ""),
        ("Egg Kale Potato Dinner", "eggs, potatoes, kale, avocado", 690, 30, 68, 30, 11, 5.1, 280, 1.4, 3.8, 3.8, 430, 1540, 250, 52, "eggs"),
        ("Black Bean Quinoa Dinner", "black beans, quinoa, spinach, avocado", 705, 30, 86, 20, 20, 7.2, 300, 0.8, 2.5, 4.9, 420, 1680, 315, 42, ""),
    ]
    for i, item in enumerate(ht_dinners, 1):
        recipes.append(row(f"HTD{i:02d}", item[0], "Dinner", "DASH Dinners", "Student Prep", "pescatarian" if "fish" in item[16] else "vegetarian", item[1], f"{item[1]}:1 serving", 7.0, *item[2:16], allergens=item[16], ibs_safe=0 if "lentils" in item[1] or "beans" in item[1] else 1, tags="dash low sodium potassium rich", is_fish=1 if "fish" in item[16] else 0))

    unsafe_examples = [
        row("UNSAFE01", "Garlic Tomato Pasta", "Dinner", "Pasta", "Italian", "vegetarian", "wheat pasta, tomato sauce, garlic, parmesan", "wheat pasta:1 box; tomato sauce:1 jar", 5.5, 720, 24, 108, 18, 7, 4.0, 300, 0.4, 1.0, 2.5, 980, 720, 120, 70, allergens="gluten;dairy;lactose", risk_tags="garlic;tomato;high_fodmap;gerd_trigger", ibs_safe=0, gerd_safe=0, diabetes_safe=0, hypertension_safe=0, tags="excluded demo"),
        row("UNSAFE02", "Spicy Fried Chicken Sandwich", "Lunch", "Fast Food", "American", "non-vegetarian", "fried chicken, wheat bun, spicy sauce", "chicken:1; wheat bun:1", 8.5, 890, 38, 88, 42, 4, 3.2, 160, 0.6, 1.0, 3.0, 1580, 690, 110, 72, allergens="gluten;eggs", risk_tags="fried;spicy;gerd_trigger", ibs_safe=0, gerd_safe=0, diabetes_safe=0, hypertension_safe=0, tags="excluded demo"),
        row("UNSAFE03", "Soy Sauce Noodle Bowl", "Dinner", "Noodles", "Asian", "vegan", "wheat noodles, soy sauce, garlic, onion", "wheat noodles:1 pack; soy sauce:1 bottle", 6.0, 760, 26, 120, 14, 6, 4.0, 120, 0.0, 0.5, 2.4, 2100, 640, 130, 68, allergens="gluten;soy", risk_tags="garlic;onion;high_fodmap;high_sodium", ibs_safe=0, gerd_safe=0, diabetes_safe=0, hypertension_safe=0, tags="excluded demo"),
    ]
    recipes.extend(unsafe_examples)
    return recipes


def restaurant_row(
    item_id: str,
    restaurant: str,
    item: str,
    cuisine: str,
    kind: str,
    calories: int,
    protein: float,
    carbs: float,
    fat: float,
    fiber: float,
    sodium: int,
    gi: int,
    allergens: str,
    risk_tags: str,
    ibs_safe: int,
    gerd_safe: int,
    diabetes_safe: int,
    hypertension_safe: int,
    confidence: float,
    is_fish: int = 0,
) -> dict:
    potassium = 700 + int(fiber * 55) + (350 if is_fish else 0)
    magnesium = 90 + int(fiber * 9)
    iron = 2.0 + fiber * 0.28
    calcium = 120 + fiber * 8
    b12 = 3.0 if is_fish else (1.1 if "eggs" in allergens else 0.4)
    vitamin_d = 8.0 if is_fish else 1.4
    zinc = 2.0 + protein * 0.05
    data = {
        "recipe_id": item_id,
        "restaurant": restaurant,
        "name": item,
        "meal_type": "Restaurant",
        "category": "Restaurant",
        "cuisine": cuisine,
        "allowed_diets": allowed_for(kind),
        "ingredients": item,
        "shopping_items": "",
        "grocery_category": "Restaurant",
        "cost_usd": 11.0,
        "calories": calories,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
        "fiber_g": fiber,
        "iron_mg": round(iron, 1),
        "calcium_mg": round(calcium, 1),
        "b12_mcg": round(b12, 1),
        "vitamin_d_mcg": round(vitamin_d, 1),
        "zinc_mg": round(zinc, 1),
        "sodium_mg": sodium,
        "potassium_mg": potassium,
        "magnesium_mg": magnesium,
        "gi": gi,
        "allergens": allergens,
        "cross_contact_risks": "gluten" if confidence < 0.8 and "gluten" not in allergens else "",
        "risk_tags": risk_tags,
        "ibs_safe": ibs_safe,
        "gerd_safe": gerd_safe,
        "diabetes_safe": diabetes_safe,
        "hypertension_safe": hypertension_safe,
        "is_fish": is_fish,
        "tags": "restaurant student extension",
        "confidence": confidence,
    }
    data["bloom_bits"] = build_bloom_bits(row_block_tokens(data))
    return data


def build_restaurants() -> list[dict]:
    return [
        restaurant_row("R001", "Campus Mediterranean", "Grilled Salmon Rice Bowl", "Mediterranean", "pescatarian", 680, 42, 70, 24, 8, 620, 50, "fish", "", 1, 1, 1, 1, 0.86, 1),
        restaurant_row("R002", "Campus Mediterranean", "Garlic Falafel Pita", "Mediterranean", "vegan", 760, 23, 98, 28, 14, 1180, 62, "gluten", "garlic;onion;high_fodmap", 0, 0, 0, 0, 0.74),
        restaurant_row("R003", "Campus Mediterranean", "Rice Lentil Bowl No Sauce", "Mediterranean", "vegan", 610, 25, 86, 14, 18, 480, 42, "", "", 0, 1, 1, 1, 0.80),
        restaurant_row("R004", "Sushi Study Hall", "Salmon Avocado Roll", "Japanese", "pescatarian", 520, 25, 72, 16, 5, 640, 56, "fish", "", 1, 1, 0, 1, 0.78, 1),
        restaurant_row("R005", "Sushi Study Hall", "Tofu Poke Bowl", "Japanese", "vegan", 650, 28, 82, 20, 9, 1220, 55, "soy", "high_sodium", 1, 1, 1, 0, 0.76),
        restaurant_row("R006", "Sushi Study Hall", "Plain Tuna Cucumber Bowl", "Japanese", "pescatarian", 590, 39, 66, 17, 5, 520, 51, "fish", "", 1, 1, 1, 1, 0.84, 1),
        restaurant_row("R007", "Taco Study Hall", "Black Bean Corn Bowl", "Mexican", "vegan", 630, 22, 88, 18, 17, 760, 45, "", "", 0, 1, 1, 1, 0.77),
        restaurant_row("R008", "Taco Study Hall", "Chicken Tomato Salsa Burrito", "Mexican", "non-vegetarian", 890, 42, 112, 28, 9, 1480, 70, "gluten", "tomato;spicy", 0, 0, 0, 0, 0.74),
        restaurant_row("R009", "Taco Study Hall", "Fish Taco Bowl No Tortilla", "Mexican", "pescatarian", 670, 37, 70, 22, 8, 690, 52, "fish", "", 1, 1, 1, 1, 0.80, 1),
        restaurant_row("R010", "Salad Lab", "Egg Quinoa Spinach Bowl", "American", "vegetarian", 560, 27, 58, 22, 10, 520, 48, "eggs", "", 1, 1, 1, 1, 0.86),
        restaurant_row("R011", "Salad Lab", "Tree Nut Crunch Salad", "American", "vegetarian", 620, 20, 52, 36, 9, 610, 46, "tree_nuts;dairy", "", 1, 1, 1, 1, 0.88),
        restaurant_row("R012", "Salad Lab", "Low Sodium Potato Salmon Plate", "American", "pescatarian", 640, 40, 62, 22, 9, 430, 51, "fish", "", 1, 1, 1, 1, 0.83, 1),
        restaurant_row("R013", "Noodle Corner", "Soy Sauce Wheat Noodles", "Asian", "vegan", 820, 24, 124, 20, 6, 2100, 73, "gluten;soy", "garlic;onion;high_sodium", 0, 0, 0, 0, 0.82),
        restaurant_row("R014", "Noodle Corner", "Rice Noodle Ginger Chicken", "Asian", "non-vegetarian", 700, 38, 92, 18, 5, 740, 58, "", "", 1, 1, 0, 1, 0.73),
        restaurant_row("R015", "Noodle Corner", "Rice Noodle Tofu Bowl", "Asian", "vegan", 690, 27, 96, 18, 7, 860, 57, "soy", "", 1, 1, 0, 1, 0.72),
        restaurant_row("R016", "Breakfast Commons", "Certified GF Oat Bowl", "American", "vegan", 420, 14, 66, 10, 9, 150, 50, "", "", 1, 1, 1, 1, 0.70),
        restaurant_row("R017", "Breakfast Commons", "Egg Potato Spinach Plate", "American", "vegetarian", 540, 25, 52, 24, 7, 420, 54, "eggs", "", 1, 1, 1, 1, 0.84),
        restaurant_row("R018", "Breakfast Commons", "Chocolate Latte Muffin Combo", "American", "vegetarian", 780, 18, 110, 30, 4, 720, 76, "gluten;dairy;lactose;eggs", "chocolate;caffeine", 0, 0, 0, 0, 0.88),
    ]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    recipes = build_recipes()
    restaurants = build_restaurants()
    write_csv(DATA_DIR / "recipe_catalog.csv", recipes)
    write_csv(DATA_DIR / "restaurant_menu_snapshot.csv", restaurants)
    print(f"Wrote {len(recipes)} recipes and {len(restaurants)} restaurant menu items.")


if __name__ == "__main__":
    main()
