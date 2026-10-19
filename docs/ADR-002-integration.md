# ADR-002 — The Writer becomes a module of CyberRiskGuardian (option D)

**Status:** accepted, 19 October 2026 (Writer 0.1.0 Beta, CyberRiskGuardian Desktop 1.7.0 Beta). Supersedes ADR-001.

## Decision

The standalone Policy Builder (FastAPI, SQLite, own accounts) is retired. The policy writer becomes
**Governance → Security Policy Writer** inside CyberRiskGuardian Desktop, sharing its workspace, users and RACI,
menus, interface languages, AI routing and audit logs. **The Writer writes; ISP management manages.**

## Consequences

| Concern | Where it lives now |
|---|---|
| Data | The person's CyberRiskGuardian workspace (`ws.isp.writer`): answers with source, facts with quotes, legal decisions with reviewer, selection. The workspace data version does not change. |
| Engine | `crg_writer/`, Python standard library only, imported by the desktop helper (`serve.py`) and served on 127.0.0.1 at `/api/writer/<op>`. Stateless: every request carries what it needs. |
| Output | ISP management drafts (clauses, statements with modality and CRGO control identifiers, policy families). Approval, freezing, publication, acknowledgements and exceptions are ISP management's. |
| Legal applicability | CRGO evaluator state (Compliance → Legal applicability) as evidence; a named reviewer decides; law-gated clauses wait. |
| Risk link | Library clauses cite controls by identifier, converted to CRGO form; documents link to scenarios through shared controls (register and CRGO library). |
| Word | Standard-library .docx writer and reader in the helper; export of any ISP policy; re-import into drafts only. |
| OCR | Tesseract (with Poppler for PDFs) or optional Python packages, detected at run time, on the computer only. |
| AI | CyberRiskGuardian's routing policy and preview: features `writer_facts` (grounded quotes) and `writer_tailor` (validated rewording). |

## Rejected options

A — link the two applications; B — export/import packages between them; C — the Writer as a separate screen
served by its own server. Each kept two sources of truth for the organization, the users and the policies.
