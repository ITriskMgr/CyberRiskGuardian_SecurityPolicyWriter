# Working on this repository

- Run `python -m pytest tests -q` before committing; `tests/e2e` needs Playwright + Chromium.
- Never invent organizational facts in clause text: use tokens (`{org}`, `{sec}`, `{p:DEC-…}`) or typed placeholders
  (`[DECISION: …]`, `[ROLE: …]`, `[VALUE: …]`; French: `[DÉCISION : …]`, `[RÔLE : …]`, `[VALEUR : …]`).
- Every clause exists in English and French with the same ID. Changing wording means bumping `LIBRARY_VERSION`.
- Laws are candidates only (`app/catalogue/rulesets.py`); clauses that depend on a law use `obligation=` gating.
- Cite ISO/IEC, NIST and CIS by identifier only. Do not add licensed standard text.
- Interface strings live in `web/i18n.js` (EN/FR). User-entered data is never translated.
- Schema changes need an Alembic migration in `migrations/versions/`.
