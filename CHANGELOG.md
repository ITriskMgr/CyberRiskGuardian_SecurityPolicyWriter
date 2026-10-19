# Changelog — CyberRiskGuardian Security Policy Writer

## 0.1.0 Beta — 19 October 2026

First release of the Writer as a module of CyberRiskGuardian Desktop (1.7.0 Beta). It replaces the standalone
*CyberRiskGuardian Policy Builder* 0.2.0 (branch `legacy/policy-builder-0.2.0`).

- **Integrated into CyberRiskGuardian** (Governance → Security Policy Writer): shared workspace, users and RACI,
  menus, EN/FR interface, AI routing and preview. The engine runs in the local helper, standard library only.
- **The Writer writes; ISP management manages**: generated documents are ISP management drafts (clauses,
  statements with modality and CRGO control identifiers, policy families). Frozen versions are never changed;
  statements edited after generation are kept on regeneration.
- **CRGO**: control identifiers in CRGO form; legal candidates carry the CRGO evaluator's state as evidence; the
  interview proposes values for the CRGO applicability profile; documents show the register and CRGO-library
  scenarios they address.
- **Start from documents**: facts with quotes and page/paragraph locators from the workspace's context documents
  and organization profile, conflicts, injection-looking passages set aside, OCR of scanned files on the computer;
  also offered when a workspace is created from documents.
- **Accept all suggestions** in Decisions (globally or per document): unanswered decisions only, recorded as
  defaults accepted by a person on a date; legal-review and no-suggestion decisions stay open and are listed.
- **Word**: a standard-library .docx writer and reader; export of any ISP policy, frozen or draft; re-import into
  the draft with per-change acceptance and modality-change flags.
