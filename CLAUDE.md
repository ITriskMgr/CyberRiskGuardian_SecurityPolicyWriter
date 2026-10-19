# Working on this repository

This repository is the source of the **CyberRiskGuardian Security Policy Writer** engine (`crg_writer/`).
CyberRiskGuardian Desktop (`ITriskMgr/CyberRiskGuardian_ThreatIntel`, `desktop/app/`) carries a copy that its
local helper serves at `/api/writer/<operation>`; the screens live there (`js/writer.js`, `js/panels/writer*.js`).

- `crg_writer/` uses the **Python standard library only** (the desktop helper has no dependencies). Optional
  tools (Tesseract, Poppler, pypdfium2, rapidocr) are detected at run time, never required.
- Run `python -m pytest tests -q` before committing. After a change, copy the engine to the desktop with
  `python3 tools/sync_to_desktop.py <desktop/app>` and run the desktop check tools there.
- The engine is stateless: everything the person enters lives in their CyberRiskGuardian workspace. Never add
  storage, network calls or telemetry to it.
- Never invent organizational facts in clause text: use tokens (`{org}`, `{sec}`, `{p:DEC-…}`) or typed placeholders
  (`[DECISION: …]`, `[ROLE: …]`, `[VALUE: …]`; French: `[DÉCISION : …]`, `[RÔLE : …]`, `[VALEUR : …]`).
- Every clause exists in English and French with the same ID. Changing wording means bumping `LIBRARY_VERSION`.
- Laws are candidates only (`crg_writer/rulesets.py`); CRGO's evaluator state is evidence, never the decision.
  Clauses that depend on a law use `obligation=` gating and appear only after a named reviewer records it applies.
- Cite ISO/IEC, NIST and CIS by identifier only (converted to CRGO identifiers by `crg_writer/crgo.py`). Do not
  add licensed standard text.
- Bump `VERSION` in `crg_writer/__init__.py` and `WRITER_VERSION` in the desktop's `js/version.js` together.
