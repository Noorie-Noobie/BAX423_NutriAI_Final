# prompts.md

## Prompt 1: Project requirements summary

**Prompt:** "Final Exam - Individual Build Project... Can u help me work on the NutriAI. first summarize what the project requires and help me understand what is needed for the final."

**Purpose:** Used to extract the required deliverables, six core NutriAI capabilities, test personas, data expectations, deployment requirement, and ZIP structure from the provided project files.

## Prompt 2: Extension brainstorming

**Prompt:** "Is there anything that suggests that we can add more features to it if we want?"

**Purpose:** Used to identify optional extensions from the project brief, especially grocery lists, meal swaps, and adaptive learning.

## Prompt 3: Student restaurant extension

**Prompt:** "is there a way where i can go beyond it and look at local restaurants and calculate their nutrition level or what's safe to eat based on dietary restrictions"

**Purpose:** Used to design Restaurant Mode as a student-focused extension that ranks menu items as safer pick, caution, or avoid using the same safety filters as the meal planner.

## Prompt 4: Review data decision

**Prompt:** "maybe also look at reviews by customers for certain things or is that not recommended?"

**Purpose:** Used to decide not to rely on customer reviews for allergy/nutrition safety because reviews are subjective and incomplete. The final app uses menu/nutrition metadata instead.

## Prompt 5: Final build request

**Prompt:** "ok now help me finish the project"

**Purpose:** Used to implement the Streamlit application, data scripts, planner/ranking engine, grocery list, restaurant mode, persona tests, benchmarks, README, brief, and final ZIP-ready folder structure.

## Prompt 6: Implementation debugging

**Prompt:** "Patch the generated catalog script so every recipe row includes the full macro/micro profile and keeps allergens separate from cross-contact notes."

**Purpose:** Used during development to fix recipe tuple slicing and guarantee the generated catalog has complete nutrition and safety metadata.

## Prompt 7: Benchmark refinement

**Prompt:** "Make the benchmark comparison fair by counting persona-specific safety/nutrition flags on both the calorie-only baseline and the optimized ranker."

**Purpose:** Used to improve the benchmark script so the technical brief reports a clean comparison of ranking impact.

## Prompt 8: Calendar and household redesign

**Prompt:** "I want to change my app a bit. I don't like the table format. I want to make it visually more appealing, like a calendar, where you can add a person entry to the same meal plan so it can be shared in households. The questions should include diabetes, vegetarian, and the other filters. Also add a sample meal plan calendar with the option to rearrange meals, and make it an all-in-one app for meal planning and grocery planning while fulfilling the project requirements."

**Purpose:** Used to redesign the Streamlit interface into a visual household meal planner with empty household setup, add/remove people, shared safety filters, allergy color chips, week/day viewing, meal swap/replacement controls, interactive nutrition charts, grocery planning, restaurant mode, and a friendlier visual design while preserving the six required NutriAI capabilities.

## Prompt 9: Visual polish

**Prompt:** "Remove the monthly calendar. Make it look more visually appealing. Add images, characters, a nice light green theme, and make the app features look ready to use."

**Purpose:** Used to simplify the planner to week/day views, add a light green product theme, and replace fragile raw-HTML calendar rendering with native Streamlit cards.

## Prompt 10: Multi-week look-ahead

**Prompt:** "also add the capability to see beyond just the week we're focusing on."

**Purpose:** Used to add a 1-4 week planning horizon, week/day focus selectors, multi-week meal swap/replacement controls, nutrition week filtering, grocery aggregation across the selected horizon, and documentation that the first week remains the required no-repeat grading plan.

## Prompt 11: Professional UI polish

**Prompt:** "this looks too childish. not professional at all. I also only have 2 hours to submit this"

**Purpose:** Used to remove the cartoon-style illustration, tighten the header and empty state, and convert the app into a more professional clinical meal-planning dashboard without changing the tested project capabilities.

## Prompt 12: Usability refinements for nutrition, grocery, and recipes

**Prompt:** "i dont get the micro trend chart what is it for? per day for the week. its not really giving me anything useful. also for grocery list can i add it in a list format with the capability of clicking on each ingredient and seeing what recipes its used in. also for the meals in the calendar is it possible to click on it and see the recipe as well for that meal."

**Purpose:** Used to replace the raw micronutrient trend with a clearer weekly nutrient target check, convert groceries into an interactive shopping checklist, show which recipes use each ingredient, and make calendar meal cards expandable with recipe details.

## Prompt 13: SF restaurant extension scope

**Prompt:** "instead of sample can i use something for sf based restaurants i just want this as an added on wow feature so if its too complicated model i might wanna remove it entirely maybe"

**Purpose:** Used to scope Restaurant Mode as a representative San Francisco neighborhood menu snapshot instead of live APIs or customer reviews, keeping the extension local, explainable, and safe for a final-project submission.

## Prompt 14: Recipe instruction polish

**Prompt:** "the recipe for all of this is the same is there a way to customize it for each recipe or will that take a while?"

**Purpose:** Used to replace the generic meal-prep note with recipe-specific prep guidance derived from each meal's ingredients and meal type.
