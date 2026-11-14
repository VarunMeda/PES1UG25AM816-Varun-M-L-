"""Validated scholarship-award calculations used by Lab 7 fuzz tests."""

import math

MIN_MARK = 0.0
MAX_MARK = 100.0


def _finite_number(value, field_name):
    """Convert *value* to a finite float or raise a useful validation error."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def parse_applicant(text):
    """Parse ``category:marks`` where marks are finite values from 0 to 100."""
    if not isinstance(text, str):
        raise TypeError("applicant record must be a string")
    if text.count(":") != 1:
        raise ValueError("applicant record must contain exactly one ':' separator")
    category, marks_text = (part.strip() for part in text.split(":", 1))
    if not category:
        raise ValueError("applicant category must not be empty")
    if not marks_text:
        raise ValueError("applicant marks must not be empty")
    marks = _finite_number(marks_text, "marks")
    if not MIN_MARK <= marks <= MAX_MARK:
        raise ValueError("marks must be between 0 and 100")
    return category.title(), marks


def marks_average(marks_csv):
    """Return the arithmetic mean of finite marks in the inclusive 0-100 range."""
    if not isinstance(marks_csv, str):
        raise TypeError("marks CSV must be a string")
    if not marks_csv.strip():
        raise ValueError("marks CSV must not be empty")
    raw_values = marks_csv.split(",")
    if any(not value.strip() for value in raw_values):
        raise ValueError("marks CSV must not contain empty values")
    marks = [_finite_number(value.strip(), "each mark") for value in raw_values]
    if any(not MIN_MARK <= mark <= MAX_MARK for mark in marks):
        raise ValueError("each mark must be between 0 and 100")
    return sum(marks) / len(marks)


def payable_award(text):
    """Calculate ``max(award * 1.18 - deduction, 0)`` for valid money values."""
    if not isinstance(text, str):
        raise TypeError("award record must be a string")
    if text.count("|") != 1:
        raise ValueError("award record must contain exactly one '|' separator")
    award_text, deduction_text = (part.strip() for part in text.split("|", 1))
    if not award_text or not deduction_text:
        raise ValueError("award and deduction must not be empty")
    award = _finite_number(award_text, "award")
    deduction = _finite_number(deduction_text, "deduction")
    if award < 0 or deduction < 0:
        raise ValueError("award and deduction must not be negative")
    return max(award * 1.18 - deduction, 0.0)


def main():
    print("==== Running parse_applicant ====")
    user_input = input("Enter category:marks (e.g. merit:82): ")
    result = parse_applicant(user_input)
    print("Category and Marks:", result)
    print("\n==== Running marks_average ====")
    user_input = input("Enter marks as CSV (e.g. 72,85,90): ")
    result = marks_average(user_input)
    print("Average Marks:", result)
    print("\n==== Running payable_award ====")
    user_input = input("Enter award|deduction (e.g. 5000|500): ")
    result = payable_award(user_input)
    print("Payable Award:", result)


if __name__ == "__main__":
    main()
