from __future__ import annotations

import io

import pandas as pd


def build_plan_pdf(plan: pd.DataFrame, daily: pd.DataFrame, profile: dict, generation_time: float, diversity_score: float) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception:
        return fallback_text_pdf(plan, daily, profile, generation_time, diversity_score)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("NutriAI 7-Day Plan", styles["Title"]))
    story.append(
        Paragraph(
            f"Diet: {profile['diet']} | Conditions: {', '.join(profile.get('conditions', [])) or 'None'} | "
            f"Generated in {generation_time:.2f}s | Diversity score: {diversity_score:.2f}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 12))

    meal_rows = [["Day", "Meal", "Recipe", "Calories", "Protein", "Fiber", "Sodium"]]
    for _, row in plan.iterrows():
        meal_rows.append(
            [
                int(row["day"]),
                row["meal_type"],
                row["name"],
                round(float(row["calories"])),
                round(float(row["protein_g"]), 1),
                round(float(row["fiber_g"]), 1),
                round(float(row["sodium_mg"])),
            ]
        )
    table = Table(meal_rows, repeatRows=1, colWidths=[34, 60, 220, 55, 55, 45, 55])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F3EF")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))

    daily_rows = [["Day", "Calories", "Protein", "Fiber", "Iron", "B12", "Sodium", "Potassium"]]
    for _, row in daily.iterrows():
        daily_rows.append(
            [
                int(row["day"]),
                round(float(row["calories"])),
                round(float(row["protein_g"]), 1),
                round(float(row["fiber_g"]), 1),
                round(float(row["iron_mg"]), 1),
                round(float(row["b12_mcg"]), 1),
                round(float(row["sodium_mg"])),
                round(float(row["potassium_mg"])),
            ]
        )
    daily_table = Table(daily_rows, repeatRows=1)
    daily_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4EFE3")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(daily_table)
    doc.build(story)
    return buffer.getvalue()


def fallback_text_pdf(plan: pd.DataFrame, daily: pd.DataFrame, profile: dict, generation_time: float, diversity_score: float) -> bytes:
    text = io.StringIO()
    text.write("NutriAI 7-Day Plan\n")
    text.write(f"Diet: {profile['diet']} | Generated in {generation_time:.2f}s | Diversity {diversity_score:.2f}\n\n")
    plan[["day", "meal_type", "name", "calories", "protein_g", "fiber_g", "sodium_mg"]].to_csv(text, index=False)
    text.write("\nDaily totals\n")
    daily.to_csv(text, index=False)
    return text.getvalue().encode("utf-8")

