# Threat model (beta 0.1.0)

Scope: a single-computer deployment (server bound to 127.0.0.1) used by one organization or a consultant with
several workspaces. Assets: organization answers, uploaded documents (often confidential), drafts, exports,
the Anthropic API key.

| Threat (spec §14.3) | Control in this version | Residual risk / next step |
|---|---|---|
| Prompt injection in uploaded documents | Passages matching instruction patterns are flagged, shown to the user, and never sent to the AI; documents are wrapped as `<untrusted_document>`; AI facts must quote text that exists verbatim in the passage; outputs are schema-validated; the model has no tools. | Pattern detection is heuristic; AI extraction is off by default per project. |
| Indirect compromise of generated policy text | AI may only reword existing clauses: same IDs, same placeholders, no new numbers, same modal verbs, bounded length; otherwise the deterministic text is kept and a finding is recorded. | A subtle meaning change without new numbers is possible — every clause still needs human review. |
| Hallucinated legal requirements | Laws are candidates from a versioned ruleset; only a named reviewer can mark one applicable; law-specific clauses are withheld until then; “Not verified” label. | Ruleset dated 2026-10-19; URLs must be re-verified. |
| Cross-tenant leakage | Every row carries `workspace_id`; lookups go through `get_project` / `scoped_get`; other tenants receive 404; files stored under workspace/project prefixes. | Tested for projects, sources, facts, policies, exports, audit. |
| Unauthorized approvals | No approval function exists yet; every document is DRAFT in the app and in Word. | Approval workflow is backlog. |
| Malicious office files / parser attacks | Content sniffing, macro-enabled and legacy OLE refused, archive bomb limits (entries, size, ratio), 500-page PDF limit, row limits, upload size limit, sanitized file names, no execution of embedded content. | Parsers run in-process (no sandbox); malware scanning is not included — scan files before upload in high-risk settings. |
| Access to deleted content | Project deletion removes DB rows (cascade), encrypted files and exports; source deletion removes segments and facts. | SQLite free pages may retain data until VACUUM; backups are the operator’s responsibility. |
| Source exfiltration via logs | Audit records hold IDs, hashes and counts, never document text; prompts are not logged. | — |
| Data at rest | Uploaded files and extracted text encrypted with Fernet; key in `data/pb-key` (mode 600) or `PB_ENCRYPTION_KEY`. | Database fields other than evidence text (answers, drafts) are not encrypted; use full-disk encryption. |
| Session theft / CSRF / XSS | HttpOnly SameSite=Strict cookie, server-side sessions, custom header required on state-changing calls, strict CSP (`script-src 'self'`), all dynamic HTML escaped. | Set `PB_SECURE_COOKIES=1` behind TLS. |
| Export of an outdated draft as approved | Exports always say DRAFT; stale drafts are flagged; version and generation time are in the document. | — |
| Generation denial of service | Synchronous jobs, upload and row limits, AI token and timeout limits. | Add rate limits before any multi-user network exposure. |
| Inconsistent translations | EN and FR share clause IDs; editing one language opens a translation-review finding for the other. | Legal equivalence of translations is never assumed. |
