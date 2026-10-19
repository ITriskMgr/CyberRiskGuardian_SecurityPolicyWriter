# Implementation checkpoints and backlog

Status against the implementation prompt (`ISP-BUILDER-PRD-001`). “Done” means demonstrated by an automated
test or a reproducible manual path.

| Checkpoint | Status | Evidence |
|---|---|---|
| A — Repository, ADR, live skeleton | Done | `docs/ADR-001-architecture.md`, `serve.py`, `/api/health`, launchers |
| B — Organization/project model, guided interview, persistence | Done | Express (21) / Standard (59) questions EN/FR, conditions, Unknown / N/A / Decide later, save/resume; `test_api_flow`, `test_logic` |
| C — Document ingestion and fact confirmation with provenance | Done | DOCX/PDF/TXT/MD/CSV/XLSX, locators, encryption at rest, rule-based facts with quotes, conflicts, injection flags; `test_security`, `test_logic` |
| D — Policy library, applicability candidates, selection | Done | 20-entry catalogue with priority and reasons, 13-rule candidate ruleset, named-reviewer decisions |
| E — Outline and drafting pipeline (mock, then Claude) | Done (MVP) | Deterministic composer from 483 bilingual clause definitions, typed placeholders, gaps, QA checks; Claude adapter with validation; outline approval step not separate |
| F — Word export, ZIP, regression tests | Done | Native .docx, reports, CSV, ZIP; validated with the OOXML validator and LibreOffice rendering |
| G — Review, issues, versioning, roles | Partial | Issues with acknowledge/resolve, versions on regenerate and on edit, RBAC (admin/owner/author/reviewer/auditor). Missing: reviewer assignment, approval workflow, immutable approved snapshots |
| H — Hardening, bilingual generation, catalogue, operations docs | Partial | Bilingual generation done; threat model; missing: SSO, PostgreSQL deployment guide, job queue, OCR |

## Acceptance tests (spec §18)

| ID | Status | Test |
|---|---|---|
| AT-01 Small tech company, no documents | Pass | `test_full_vertical_slice`, `test_every_policy_composes_cleanly` |
| AT-02 Quebec SME with PI → candidates, not declarations | Pass | `test_candidates_never_applicable_without_decision` |
| AT-03 Healthcare conditional questions and candidates | Pass | `test_express_interview_is_short_and_standard_branches`, candidates test |
| AT-04 Uploaded approved policy → facts with locators | Pass | `test_full_vertical_slice` |
| AT-05 Old and new documents disagree on MFA | Pass | `test_contradictory_documents_surface_conflict` |
| AT-06 Only one topic policy | Pass | `test_single_policy_only` |
| AT-07 EISP + five policies ZIP | Pass | `test_full_vertical_slice` |
| AT-08 Approver unknown → placeholder, still exportable | Pass | `test_full_vertical_slice`, `test_no_invented_roles_or_approver` |
| AT-09 Injection in uploaded file | Pass | `test_prompt_injection_document_is_not_sent_or_followed` |
| AT-10 Cross-tenant access | Pass | `test_cross_tenant_access_denied` |
| AT-11 BYOD answer changes → stale → regenerate | Pass | `test_full_vertical_slice` |
| AT-12 French output | Pass | `test_bilingual_output` |
| AT-13 Deletion | Pass | `test_project_delete_removes_files` |
| AT-14 Unverified legal rule | Pass | candidates and obligation-gating tests |
| AT-15 Word regression | Pass (manual + validator) | LibreOffice render of sample package; OOXML validation |
| AT-16 Edit creates new revision, earlier kept | Pass (drafts) | `test_full_vertical_slice` — approval snapshots not yet built |

## Proposed next increments

1. Review and approval workflow: reviewer assignment, legal sign-off gate, executive approval by a named human,
   SHA-256-frozen approved versions (same model as the CyberRiskGuardian desktop ISP module).
2. Standards generation (level 3) for authentication, classification handling, cryptography and logging, so
   numeric parameters leave the policies.
3. Word re-import using the embedded document identifier; clause-level diff.
4. CyberRiskGuardian connector: read risk scenarios and KRIs to prioritize policies and map clauses to treated
   risks (`PolicyClause → addresses → ControlObjective`, `Control → treats → RiskScenario`) through the CRGO ontology.
5. Complete the five structure templates as full clause libraries; OCR with accuracy warnings.
