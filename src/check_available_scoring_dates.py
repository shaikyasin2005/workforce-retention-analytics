from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "workforce_retention.db"

query = """
SELECT
    scoring_date,
    horizon_days,
    label_version,
    COUNT(*) AS outcome_records,
    SUM(
        CASE WHEN label_voluntary_attrition = 1 THEN 1 ELSE 0 END
    ) AS attrition_cases,
    SUM(
        CASE WHEN label_voluntary_attrition = 0 THEN 1 ELSE 0 END
    ) AS no_attrition_cases
FROM AttritionOutcome
WHERE outcome_status IN (
    'ObservedAttrition',
    'ObservedNoAttrition'
)
AND label_voluntary_attrition IN (0, 1)
GROUP BY scoring_date, horizon_days, label_version
ORDER BY scoring_date, horizon_days, label_version;
"""

with sqlite3.connect(DATABASE_PATH) as connection:
    rows = connection.execute(query).fetchall()

print("AVAILABLE SCORING DATES")
print("=" * 85)

if not rows:
    print("No valid observed outcome records found.")
else:
    for row in rows:
        print(
            f"Date: {row[0]} | Horizon: {row[1]} days | "
            f"Version: {row[2]} | Records: {row[3]} | "
            f"Attrition: {row[4]} | No attrition: {row[5]}"
        )