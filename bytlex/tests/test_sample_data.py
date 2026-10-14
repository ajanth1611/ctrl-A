import pandas as pd

from src.sample_data import ensure_demo_student_records


def test_demo_profiles_are_added_without_replacing_existing_rows():
    existing = pd.DataFrame(
        [{"student_id": "CIQ2022001", "name": "Synthetic Existing Student"}]
    )

    seeded = ensure_demo_student_records(existing)

    assert len(seeded) == 4
    assert seeded["student_id"].is_unique
    assert "CIQ2022001" in seeded["student_id"].values
    assert seeded.loc[seeded["student_id"] == "CIQ2022001", "name"].iloc[0] == (
        "Synthetic Existing Student"
    )
    assert {"STU2021002", "STU2021004", "STU2021007"}.issubset(
        set(seeded["student_id"])
    )


def test_demo_profiles_are_not_duplicated():
    existing = pd.DataFrame(
        [
            {"student_id": "STU2021002"},
            {"student_id": "STU2021004"},
            {"student_id": "STU2021007"},
        ]
    )

    seeded = ensure_demo_student_records(existing)

    assert len(seeded) == len(existing)
    assert seeded["student_id"].is_unique
