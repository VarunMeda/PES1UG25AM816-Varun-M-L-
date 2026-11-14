"""Hypothesis properties for the scholarship-awards input contract."""

import math

import pytest
from hypothesis import given, settings, strategies as st

from scholarship_awards import marks_average, parse_applicant, payable_award

finite_marks = st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)
finite_money = st.floats(min_value=0, max_value=1_000_000, allow_nan=False, allow_infinity=False)


@settings(max_examples=40, deadline=None)
@given(category=st.text(min_size=1).filter(lambda value: ":" not in value and value.strip()), marks=finite_marks)
def test_parse_applicant_valid_records(category, marks):
    result = parse_applicant(f" {category} : {marks} ")
    assert result == (category.strip().title(), float(marks))


@settings(max_examples=30, deadline=None)
@given(st.one_of(
    st.none(),
    st.text().filter(lambda value: value.count(":") != 1),
    st.sampled_from([":82", "merit:", "merit:abc", "merit:nan", "merit:inf", "merit:-1", "merit:101"]),
))
def test_parse_applicant_rejects_invalid_records(value):
    with pytest.raises((TypeError, ValueError)):
        parse_applicant(value)


@settings(max_examples=40, deadline=None)
@given(marks=st.lists(finite_marks, min_size=1, max_size=12))
def test_marks_average_returns_arithmetic_mean(marks):
    result = marks_average(",".join(str(mark) for mark in marks))
    assert math.isclose(result, sum(marks) / len(marks), rel_tol=1e-12, abs_tol=1e-12)


@settings(max_examples=30, deadline=None)
@given(st.one_of(
    st.none(),
    st.text().filter(lambda value: not value.strip() or any(part.strip() == "" for part in value.split(","))),
    st.sampled_from(["abc", "nan", "inf", "-1", "101", "0,xyz", "1,,2"]),
))
def test_marks_average_rejects_invalid_records(value):
    with pytest.raises((TypeError, ValueError)):
        marks_average(value)


@settings(max_examples=40, deadline=None)
@given(award=finite_money, deduction=finite_money)
def test_payable_award_applies_formula_and_floor(award, deduction):
    result = payable_award(f" {award} | {deduction} ")
    expected = max(award * 1.18 - deduction, 0.0)
    assert math.isclose(result, expected, rel_tol=1e-12, abs_tol=1e-12)


@settings(max_examples=30, deadline=None)
@given(st.one_of(
    st.none(),
    st.text().filter(lambda value: value.count("|") != 1),
    st.sampled_from(["|500", "500|", "abc|500", "500|xyz", "-1|0", "500|-1", "nan|0", "inf|0"]),
))
def test_payable_award_rejects_invalid_records(value):
    with pytest.raises((TypeError, ValueError)):
        payable_award(value)
