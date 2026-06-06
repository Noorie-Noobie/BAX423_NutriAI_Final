# NutriAI

NutriAI is a Streamlit application for the BAX-423 final build project. It generates a personalized household meal calendar with clinical filtering, allergy exclusion, diet handling, diversity scoring, macro/micronutrient analytics, grocery-list export, safe meal swap/replacement controls, a 1-4 week planning horizon, and a student-oriented restaurant mode. The first 7 days remain the required rubric plan; longer horizons let users look ahead for meal prep while reusing safe meals only when the safe candidate pool is exhausted.

## Run Locally

```bash
pip install -r requirements.txt
python scripts/build_catalogs.py
python scripts/build_food_snapshot.py
streamlit run app.py
```

If `data/food_snapshot.csv`, `data/recipe_catalog.csv`, and `data/restaurant_menu_snapshot.csv` already exist, the app can be started directly:

```bash
streamlit run app.py
```

## Deploy

The fastest public deployment path is Streamlit Community Cloud:

1. Push this project to GitHub.
2. Create a new Streamlit app.
3. Set the app entry point to `code/app.py`.
4. Make sure the repo includes the `data/` folder and `code/requirements.txt`.

## Project Structure

- `app.py`: Streamlit UI.
- `nutriai/`: filtering, ranking, restaurant, and export logic.
- `scripts/build_catalogs.py`: builds the curated recipe and restaurant snapshots.
- `scripts/build_food_snapshot.py`: downloads and preprocesses USDA FoodData Central CSV archives.
