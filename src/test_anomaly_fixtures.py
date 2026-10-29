"""
Isolated anomaly fixtures for workforce-retention validation.

These tests use in-memory SQLite tables and never modify the
main workforce_retention.db database.
"""

import sqlite3


def main():
    connection = sqlite3.connect(":memory:")

    try:
        # 1. Missing survey must remain missing, not become a negative score.
        connection.execute("""
            CREATE TABLE survey_fixture (
                employee_id TEXT PRIMARY KEY,
                response_status TEXT,
                engagement_score REAL
            )
        """)

        connection.execute("""
            INSERT INTO survey_fixture
            VALUES ('TEST-001', 'Missing', NULL)
        """)

        missing_survey = connection.execute("""
            SELECT COUNT(*)
            FROM survey_fixture
            WHERE response_status = 'Missing'
              AND engagement_score IS NULL
        """).fetchone()[0]

        # 2. High workload alone must not automatically imply attrition.
        connection.execute("""
            CREATE TABLE workload_fixture (
                employee_id TEXT PRIMARY KEY,
                workload_category TEXT,
                workload_hours_per_week REAL
            )
        """)

        connection.execute("""
            INSERT INTO workload_fixture
            VALUES ('TEST-002', 'High', 60)
        """)

        high_workload = connection.execute("""
            SELECT COUNT(*)
            FROM workload_fixture
            WHERE workload_category = 'High'
              AND workload_hours_per_week >= 60
        """).fetchone()[0]

        # 3. Detect an outcome window that does not match its horizon.
        connection.execute("""
            CREATE TABLE outcome_fixture (
                employee_id TEXT PRIMARY KEY,
                scoring_date TEXT,
                outcome_window_end TEXT,
                horizon_days INTEGER
            )
        """)

        connection.execute("""
            INSERT INTO outcome_fixture
            VALUES ('TEST-003', '2026-07-30', '2026-10-20', 90)
        """)

        invalid_window = connection.execute("""
            SELECT COUNT(*)
            FROM outcome_fixture
            WHERE date(outcome_window_end) !=
                  date(scoring_date, '+' || horizon_days || ' days')
        """).fetchone()[0]

        # 4. Detect future information used as a model feature.
        connection.execute("""
            CREATE TABLE feature_fixture (
                employee_id TEXT,
                scoring_date TEXT,
                feature_date TEXT
            )
        """)

        connection.execute("""
            INSERT INTO feature_fixture
            VALUES ('TEST-004', '2026-07-30', '2026-08-15')
        """)

        future_feature = connection.execute("""
            SELECT COUNT(*)
            FROM feature_fixture
            WHERE date(feature_date) > date(scoring_date)
        """).fetchone()[0]

        # 5. Detect a voluntary attrition label inconsistent with
        #    the presence of a termination date.
        connection.execute("""
            CREATE TABLE label_fixture (
                employee_id TEXT PRIMARY KEY,
                outcome_status TEXT,
                termination_date TEXT,
                termination_type TEXT,
                label_voluntary_attrition INTEGER
            )
        """)

        connection.execute("""
            INSERT INTO label_fixture
            VALUES ('TEST-005', 'ObservedAttrition', NULL, 'Voluntary', 1)
        """)

        invalid_label = connection.execute("""
            SELECT COUNT(*)
            FROM label_fixture
            WHERE outcome_status = 'ObservedAttrition'
              AND (
                  termination_date IS NULL
                  OR termination_type != 'Voluntary'
                  OR label_voluntary_attrition != 1
              )
        """).fetchone()[0]

        # 6. Verify that recommendations have an explanation and
        #    a human-review status before being acted upon.
        connection.execute("""
            CREATE TABLE recommendation_fixture (
                employee_id TEXT PRIMARY KEY,
                explanation TEXT,
                review_status TEXT
            )
        """)

        connection.executemany("""
            INSERT INTO recommendation_fixture
            VALUES (?, ?, ?)
        """, [
            ('TEST-006', 'Low engagement and rising workload', 'Pending'),
            ('TEST-007', '', 'Approved')
        ])

        invalid_recommendation = connection.execute("""
            SELECT COUNT(*)
            FROM recommendation_fixture
            WHERE explanation IS NULL
               OR TRIM(explanation) = ''
               OR review_status NOT IN ('Pending', 'Approved', 'Rejected')
        """).fetchone()[0]

        print("ISOLATED ANOMALY FIXTURE REPORT")
        print("-" * 45)
        print(f"Missing survey detected: {missing_survey}")
        print(f"High workload case detected: {high_workload}")
        print(f"Invalid temporal window detected: {invalid_window}")
        print(f"Future feature leak detected: {future_feature}")
        print(f"Invalid attrition label detected: {invalid_label}")
        print(
            "Invalid recommendation records detected: "
            f"{invalid_recommendation}"
        )

        assert missing_survey == 1
        assert high_workload == 1
        assert invalid_window == 1
        assert future_feature == 1
        assert invalid_label == 1
        assert invalid_recommendation == 1

        print("\nAll isolated anomaly fixture tests passed.")
        print("Main database was not modified.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()