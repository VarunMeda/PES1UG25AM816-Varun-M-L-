import pytest

from scholarship_awards import application_status, award_amount, is_eligible


@pytest.mark.parametrize(
    "category, marks, income_level, is_renewal, expected",
    [
        ("merit", 75, "standard", False, 0),
        ("sports", 60, "standard", True, 0),
        ("merit", 71, "standard", True, 60),
        ("arts", 61, "low", True, 100),
        ("sports", 76, "standard", False, 1600),
        ("merit", 90, "standard", False, 900),
        ("merit", 90, "low", False, 1500),
        ("merit", 90, "low", True, 3200),
    ],
)
def test_award_amount_exercises_rate_and_cutoff_branches(
    category, marks, income_level, is_renewal, expected
):
    assert award_amount(category, marks, income_level, is_renewal) == expected


@pytest.mark.parametrize("category", ["merit", "sports", "arts"])
def test_award_amount_nonrenewal_categories_use_their_own_cutoffs(category):
    cutoff = {"merit": 75, "sports": 60, "arts": 65}[category]
    assert award_amount(category, cutoff + 1, "standard", False) == 60


def test_award_amount_invalid_category_and_marks_raise_value_error():
    with pytest.raises(ValueError, match="unknown category"):
        award_amount("unknown", 80, "low", False)
    with pytest.raises(ValueError, match="invalid marks"):
        award_amount("merit", -1, "low", False)


@pytest.mark.parametrize(
    "attendance, backlogs, is_special_quota, expected",
    [
        (50, 2, True, True),
        (50, 3, True, False),
        (74, 0, False, False),
        (75, 0, False, True),
        (90, 1, False, True),
        (90, 2, False, False),
    ],
)
def test_is_eligible_exercises_quota_attendance_and_backlog_branches(
    attendance, backlogs, is_special_quota, expected
):
    assert is_eligible(attendance, backlogs, is_special_quota) is expected


@pytest.mark.parametrize(
    "days_left, is_renewal, is_paper, expected",
    [
        (20, False, False, "open"),
        (19, False, False, "closing"),
        (4, False, False, "closed"),
        (30, True, False, "open"),
        (29, True, False, "closing"),
        (14, True, False, "closed"),
        (30, False, True, "open"),
        (15, False, True, "closing"),
        (14, False, True, "closed"),
        (40, True, True, "open"),
        (25, True, True, "closing"),
        (24, True, True, "closed"),
    ],
)
def test_application_status_exercises_all_cutoff_branches(
    days_left, is_renewal, is_paper, expected
):
    assert application_status(days_left, is_renewal, is_paper) == expected
