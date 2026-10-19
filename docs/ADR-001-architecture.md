# ADR-001 — Architecture of the standalone Policy Builder (superseded by ADR-002)

**Status:** Accepted for the MVP · **Date:** 2026-10-19 · **Author:** Marc-André Léger (product owner), drafted with Claude

## Context

The specification `ISP-BUILDER-PRD-001` and the implementation prompt ask for a secure, guided, AI-assisted
application that interviews an organization, optionally ingests its documents, recommends a policy
hierarchy, drafts organization-specific information security policies and exports editable Word files.
The suggested stack is Next.js + FastAPI + PostgreSQL. The application is a companion to CyberRiskGuardian
(CRG), whose desktop edition runs locally: a small Python server bound to `127.0.0.1`, launched with
`start.command` / `start.bat` / `start.sh`, no installer, no account, EN/FR interface.

## Decisions

| # | Decision | Reason |
|---|---|---|
| D1 | **Backend: Python FastAPI + Pydantic + SQLAlchemy 2.** | As specified. Same language as the Word, PDF and spreadsheet tooling. |
| D2 | **Frontend: dependency-free HTML/CSS/JavaScript (ES modules) served by FastAPI** instead of Next.js. | Deviation. Removes the Node build step and keeps the CRG launch model (one Python process, `start.command`). The API is the contract: a Next.js client can replace `web/` later without backend change. |
| D3 | **Database: SQLite by default, PostgreSQL by `PB_DATABASE_URL`.** Alembic migrations in `migrations/`. | SQLite gives a zero-setup local install; the ORM keeps PostgreSQL a configuration change. |
| D4 | **Tenancy: Workspace = tenant.** Every project, source, fact, policy, issue, export and audit row carries `workspace_id`; every query goes through `scoped()` helpers that filter by the caller's workspace. Cross-tenant access returns 404 (no existence leak). | Spec §14.1, AT-10. |
| D5 | **Authentication: local accounts** (PBKDF2-SHA256, 310 000 iterations), opaque session token in an HttpOnly, SameSite=Strict cookie, server-side session table. OIDC/SAML is a later adapter. | Works offline; no secret in the client. |
| D6 | **RBAC roles:** `admin`, `owner`, `author`, `reviewer`, `auditor` (read-only). Enforced on the server per endpoint. | Spec §2. |
| D7 | **Structured JSON is the source of truth** for policy bodies (`PolicyVersion.body`) with normalized `PolicyClause` rows. `.docx` files are derived exports. | Spec §6, §12. |
| D8 | **Deterministic drafting core + optional AI.** Policies are assembled from versioned clause libraries (EN/FR) driven by interview answers and decisions. Unanswered material decisions become typed placeholders (`[DECISION: …]`, `[ROLE: …]`). The AI provider (mock or Claude) may only *tailor wording* of a section and must return the same clause IDs and placeholders; the result is schema-validated and rejected if it drops a placeholder or a clause. | Prevents invented facts and keeps every clause traceable. Works with no API key. |
| D9 | **AI provider interface** (`app/drafting/ai.py`): `MockProvider` (default, offline) and `AnthropicProvider` (server-side key `ANTHROPIC_API_KEY`, model `PB_AI_MODEL`). Prompt templates are versioned; model ID, prompt version and timestamp are stored with each version, never the source text. | Spec §13.3. |
| D10 | **Uploaded documents never go to an AI provider by default.** A per-project switch (`ai_on_sources`, default off, recorded in the audit log) is required, and the UI states what is sent. Extracted text is wrapped as untrusted data; instructions inside documents are detected, flagged and never executed. | Spec §6.4, §14.1, AT-09. |
| D11 | **Encryption at rest** of uploaded files and extracted text with Fernet (AES-128-CBC + HMAC-SHA256); key in `data/pb-key` (mode 600) or `PB_ENCRYPTION_KEY`. | Spec §6.4. |
| D12 | **Legal applicability is never automatic.** Rulesets produce *candidates* with reasoning, conditions, a reference URL and "verification required"; only a named human can set `applies` / `not_applicable` / `needs_legal_review`. | Spec §5.6, AT-02, AT-14. |
| D13 | **Bind to 127.0.0.1** by default; `PB_HOST` to change. | CRG convention. |
| D14 | **Licence:** CC BY-NC 4.0, © 2026 Marc-André Léger, consistent with CyberRiskGuardian. | Owner decision. |

## Consequences

- No Node.js needed; Python 3.11+ and `pip install -r requirements.txt`.
- Synchronous in-process jobs (generation, export) — acceptable for one organization at a time; a queue
  (RQ/Celery) is a later change behind the same service functions.
- Framework standards are cited by **identifier only** (e.g. ISO/IEC 27002:2022 5.15, NIST CSF 2.0 GV.PO-01);
  no licensed text is shipped.
