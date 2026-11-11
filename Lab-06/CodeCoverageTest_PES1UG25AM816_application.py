import pytest

from scholarship_awards import application_status, award_amount, is_eligible


@pytest.mark.parametrize(
    "category, marks, expected",
    [
        ("merit", 74, 0),
        ("merit", 75, 0),
        ("merit", 76, 60),
        ("sports", 59, 0),
        ("sports", 60, 0),
        ("sports", 61, 60),
        ("arts", 64, 0),
        ("arts", 65, 0),
        ("arts", 66, 60),
    ],
)
def test_award_amount_category_cutoffs_for_nonrenewals(category, marks, expected):
    assert award_amount(category, marks, "standard", False) == expected


@pytest.mark.parametrize(
    "category, marks, expected",
    [
        ("merit", 70, 0),
        ("merit", 71, 60),
        ("arts", 60, 0),
        ("arts", 61, 60),
        ("sports", 60, 0),
        ("sports", 61, 60),
    ],
)
def test_award_amount_renewal_cutoffs(category, marks, expected):
    assert award_amount(category, marks, "standard", True) == expected


@pytest.mark.parametrize(
    "income_level, is_renewal, expected",
    [
        ("low", False, 1500),
        ("low", True, 3200),
        ("standard", False, 900),
        ("standard", True, 2000),
    ],
)
def test_award_amount_additional_rate_for_marks_above_15(income_level, is_renewal, expected):
    assert award_amount("merit", 90, income_level, is_renewal) == expected


@pytest.mark.parametrize("category", ["merit", "sports", "arts"])
def test_award_amount_low_income_base_rate(category):
    cutoff = {"merit": 75, "sports": 60, "arts": 65}[category]
    assert award_amount(category, cutoff + 5, "low", False) == 500


def test_award_amount_invalid_category_raises_value_error():
    with pytest.raises(ValueError, match="unknown category"):
        award_amount("science", 80, "low", False)


def test_award_amount_negative_marks_raises_value_error():
    with pytest.raises(ValueError, match="invalid marks"):
        award_amount("merit", -1, "low", False)


@pytest.mark.parametrize(
    "attendance, backlogs, is_special_quota, expected",
    [
        (90, 0, False, True),
        (75, 0, False, True),
        (74.99, 0, False, False),
        (90, 1, False, True),
        (90, 2, False, False),
        (50, 2, True, True),
        (50, 0, True, True),
        (50, 3, True, False),
    ],
)
def test_is_eligible_boundary_and_quota_rules(
    attendance, backlogs, is_special_quota, expected
):
    assert is_eligible(attendance, backlogs, is_special_quota) is expected


@pytest.mark.parametrize(
    "days_left, is_renewal, is_paper, expected",
    [
        (20, False, False, "open"),
        (19, False, False, "closing"),
        (5, False, False, "closing"),
        (4, False, False, "closed"),
        (30, True, False, "open"),
        (29, True, False, "closing"),
        (15, True, False, "closing"),
        (14, True, False, "closed"),
        (30, False, True, "open"),
        (29, False, True, "closing"),
        (15, False, True, "closing"),
        (40, True, True, "open"),
        (39, True, True, "closing"),
        (25, True, True, "closing"),
        (24, True, True, "closed"),
    ],
)
def test_application_status_cutoffs_and_application_types(
    days_left, is_renewal, is_paper, expected
):
    assert application_status(days_left, is_renewal, is_paper) == expected
