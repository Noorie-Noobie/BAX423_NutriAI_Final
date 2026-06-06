# NutriAI AI Development Prompts

This file documents the primary AI-assisted prompts used during the design, implementation, testing, and refinement of the NutriAI final project. The prompts below are summarized in professional form rather than copied verbatim from every working exchange.

## Prompt 1: Requirements Interpretation

**Prompt summary:** Review the NutriAI project brief and summarize the required deliverables, grading-critical capabilities, dataset expectations, deployment requirements, and final ZIP structure.

**Purpose:** Established the implementation checklist for the six required NutriAI capabilities: clinical filtering, allergy exclusion, dietary preferences, diversity, macro/micronutrient analysis, and sub-60-second generation.

## Prompt 2: Data Pipeline Design

**Prompt summary:** Design a data pipeline using USDA FoodData Central as the nutrition data source and create an offline snapshot that satisfies the project requirement for a reusable food database.

**Purpose:** Guided the creation of `food_snapshot.csv`, including nutrient-field selection, deduplication, and rule-oriented metadata fields for allergens and clinical caution flags.

## Prompt 3: Recipe Catalog Structure

**Prompt summary:** Define a structured recipe catalog that converts nutrition and clinical requirements into complete meal records with diet tags, allergens, GI estimates, sodium/potassium/magnesium, grocery fields, and clinical safety flags.

**Purpose:** Created the schema and logic behind `recipe_catalog.csv`, allowing the planner to safely filter and rank complete meals rather than raw ingredient records.

## Prompt 4: Safety-First Recommendation Model

**Prompt summary:** Implement a hybrid rule-based and ranking model that first removes unsafe meals, then scores remaining candidates using nutrition fit, clinical fit, diversity, cost, and user preferences.

**Purpose:** Established the main NutriAI model architecture: hard filtering for safety, followed by scoring and diversity-aware meal assignment.

## Prompt 5: Clinical Rule Implementation

**Prompt summary:** Translate IBS, GERD, Type 2 Diabetes, and Hypertension requirements into app-level food rules such as low-FODMAP screening, GERD trigger exclusion, low-GI preference, sodium limits, and DASH-style nutrient checks.

**Purpose:** Ensured that health conditions from the brief were represented as explicit and explainable filtering/ranking logic.

## Prompt 6: Persona-Based Testing

**Prompt summary:** Build automated tests for the required NutriAI personas to verify clinical filtering, allergy exclusion, dietary compatibility, diversity score, nutrient analysis, and runtime.

**Purpose:** Produced `docs/persona_test_results.csv` and validated that Priya, Ravi, Mei, and James pass the grading-critical requirements.

## Prompt 7: Benchmark and BAX-423 Technique Reporting

**Prompt summary:** Compare the optimized ranking model against simpler baselines and document relevant BAX-423 techniques such as feature engineering, Bloom-filter screening, hash embeddings, ranking, and evaluation.

**Purpose:** Supported the technical brief with measurable evidence for model design and course-relevant analytics techniques.

## Prompt 8: Household Planner Interface

**Prompt summary:** Redesign the app from a table-based output into a household meal planner where users can add/remove members, combine filters, generate shared safe plans, and view meals by week or day.

**Purpose:** Created the main Streamlit workflow with household profiles, shared safety constraints, week/day planning, and meal swap/replacement controls.

## Prompt 9: Grocery Planning Extension

**Prompt summary:** Add an interactive grocery planner that aggregates ingredients from the generated meal plan, supports checklist-style shopping, and shows which recipes use each ingredient.

**Purpose:** Added a practical meal-prep feature while keeping grocery output tied directly to the generated meal calendar.

## Prompt 10: Nutrition Dashboard Refinement

**Prompt summary:** Improve the nutrition dashboard so users can compare daily totals against clear nutrient targets instead of viewing raw field names or unclear trend charts.

**Purpose:** Replaced confusing micronutrient labels with a weekly nutrient target-check view and macro split visualization.

## Prompt 11: Restaurant Mode Scope

**Prompt summary:** Design an optional student-focused Restaurant Mode that applies the same safety rules to representative San Francisco neighborhood menu items while clearly labeling results as risk estimates.

**Purpose:** Added a local-use extension without depending on unreliable customer reviews or incomplete live restaurant API data.

## Prompt 12: UI Professionalization

**Prompt summary:** Refine the visual design so the application feels like a polished clinical/student meal-planning tool rather than a prototype.

**Purpose:** Improved the app’s layout, theme, empty state, cards, labels, and interaction flow while preserving the required model behavior.

## Prompt 13: Recipe Detail Usability

**Prompt summary:** Make meal cards expandable so users can inspect recipe ingredients, nutrition values, GI, safety notes, grocery items, and recipe-specific prep guidance.

**Purpose:** Improved transparency and made the calendar more useful during a walkthrough or real meal-planning session.

## Prompt 14: Deployment and Submission Packaging

**Prompt summary:** Prepare the final project for deployment and Canvas submission, including GitHub repository setup, Streamlit deployment, technical brief links, prompts documentation, and final ZIP packaging.

**Purpose:** Ensured the submitted ZIP includes `code/`, `data/`, `brief.pdf`, `prompts.md`, requirements/setup files, the deployed app URL, and the source repository link.
