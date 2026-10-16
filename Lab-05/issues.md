# Lab 5 issues

| Issue | Type | Line(s) | Description | Fix Approach |
|---|---|---:|---|---|
| XML parser accepted unsafe input | Security (Bandit B406/B317) | 2, 75 | The original `xml.sax` parser could process hostile XML input. | Use `defusedxml.sax` and reject unsupported entities. |
| Unknown SSH hosts were trusted | Security (Bandit B507) | 80 | `AutoAddPolicy` allowed a man-in-the-middle host key. | Load known host keys and use `RejectPolicy`. |
| Remote command used input directly | Security (Bandit B601) | 82 | Concatenating `fare_file` into a shell command allowed command injection. | Remove remote shell execution entirely. Deploy by SFTP to the fixed gate-owned destination `/var/lib/transit-fares.txt`; no untrusted value is interpreted by a shell. |
| MD5 ticket checksum | Security (Bandit B303) | 60 | MD5 is collision-prone and unsuitable for integrity-oriented checksums. | Use SHA-256. |
| Daily cap was never applied | Functional bug | 35-41 | The loop reassigned a local `f`, then returned the uncapped total; the sample output was 208.0. | Return `min(total, DAILY_CAP)`. |
| Mutable default categories | Code quality (Pylint W0102) | 46 | `categories=[]` shared mutable state between calls. | Use an immutable empty tuple default. |
| Missing card and input validation | Reliability | 43-54 | Unknown cards caused `KeyError`, invalid times/categories were accepted, and cards could go negative. | Validate values and raise clear `ValueError`s. |
| Naming, documentation, and formatting | Code quality (Pylint/Flake8) | 1-100 | The original used non-snake-case names, a lambda alias, missing docstrings, an unused import, and spacing/line-length violations. | Rename APIs, add documentation, remove dead code, and format consistently. |
