# Reflection

## 1. What static code analysis is and why it is useful

Static code analysis examines source code without executing every path. It quickly identifies maintainability problems, suspicious APIs, and patterns associated with defects. In this lab it exposed security risks that were easy to miss during the normal demonstration run, while manual testing exposed the daily-cap bug.

## 2. What Pylint, Bandit, and Flake8 contribute

Pylint checked naming, documentation, unused code, and suspicious constructs. Bandit focused on security-sensitive APIs, identifying MD5, unsafe XML parsing, automatic SSH host-key trust, and the Paramiko shell command. Flake8 enforced smaller style rules such as blank lines, unused imports, lambda assignment, and line length. They overlap usefully, but none replaces the others.

## 3. Issues fixed and resulting improvements

The final code uses `defusedxml`, SHA-256, verified SSH host keys, SFTP-only deployment, validated inputs, immutable defaults, and a real daily cap. It also prevents unknown-card and insufficient-balance operations. The original Pylint score was 5.80/10; the final score is 10.00/10. Flake8 went from 20 findings to zero. Bandit went from five findings to zero because the remote shell call was removed entirely.

## 4. Limitations of static analysis and need for runtime testing

Static tools cannot determine the intended fare-cap semantics, whether a card should be allowed to go negative, or whether a deployed SSH command succeeds on a real gate. They also cannot prove that a known-hosts file is administered correctly. The unit tests therefore cover fare boundaries, discounts, caps, cards, routes, checksums, hostile XML, and mocked SSH interactions. Real SSH deployment was intentionally not attempted.
