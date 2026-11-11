# L6_L7_44 — Scholarship Awards

Lab 6: Code and Branch Coverage

## About

A small Python module that works out scholarship award amounts by category, marks, income level and renewal, checks applicant eligibility and reports application status.

## Files

| File | Description |
|------|-------------|
| `scholarship_awards.py` | The module under test |
| `test_scholarship_awards.py` | Starter test file |
| `CodeCoverageTest_PES1UG25AM816_application.py` | Dedicated line-coverage tests |
| `BranchCoverageTest_PES1UG25AM816_application.py` | Dedicated branch-coverage tests |
| `code_coverage_screenshot.png` | Terminal output for line coverage |
| `branch_coverage_screenshot.png` | Terminal output for branch coverage |

## Coverage results

The dedicated code-coverage suite passes 47 tests and achieves 100% line coverage for `scholarship_awards.py`.

The dedicated branch-coverage suite passes 30 tests and achieves 100% branch coverage: 26 branches covered and 0 missing.

## Run the coverage suites

From this directory, activate the repository environment and run the following commands:

```powershell
..\.venv\Scripts\Activate.ps1

python -m coverage erase
python -m coverage run --source=scholarship_awards -m pytest -q CodeCoverageTest_PES1UG25AM816_application.py
python -m coverage report -m

python -m coverage erase
python -m coverage run --branch --source=scholarship_awards -m pytest -q BranchCoverageTest_PES1UG25AM816_application.py
python -m coverage report -m
```

Keep all your Lab 6 work in this `LAB6` folder. Lab 7 will be added to this repo later.

Refer to the lab handout for instructions.
