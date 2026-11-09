# Changelog — CyberRiskGuardian Security Policy Writer

## 0.1.1 Beta — 8 November 2026

Shipped in CyberRiskGuardian Desktop **1.9.2 Beta**. Author decision D1 (8 November 2026): **the desktop copy of
`crg_writer/` is canonical**; this repository is synced *from* it (`tools/sync_to_desktop.py`, desktop → here by default,
refuses to overwrite a diverged tree without `--force` and prints the differences) and the desktop pins the engine tree
(`WRITER_TREE_HASH` in its `js/version.js`, `tools/writer_tree_hash.py`). The two copies had drifted (NV-W01: « appétence »
in the desktop, « appétit » here); this release makes them byte-identical again. Findings of the 8 November 2026 test
campaign (`next-version-spec.md` v6) and of the independent review of Desktop 1.9.2:

- **NV-009 — untrusted document text.** New operation `ai_text`: every document line that looks like an instruction to an
  AI (NBSP and repeated spaces normalised) is set aside before the AI payload is built; `op_ground` drops quotes matching
  the injection patterns (kept in step with the desktop page's). **Review L3**: `ai_text` and `segments` also scan adjacent
  line pairs and paragraph blocks (`injected_lines`), so an instruction split over two lines is set aside with both lines.
- **NV-W02** — a conflict between two documents is resolved by confirming one value (*Use this value*).
- **NV-W03** — R-22.1 (Quebec, Loi 25 regulation) and C-1.1 clauses with their quality checks (QC-R22.1, QC-C1.1); a
  CRGO-applicable instrument without a clause in the library is listed to the reviewer as a candidate (`INSTRUMENT_LABEL`).
- **NV-W04** — ORG-10 (language of the documents) is a preference that drives generation.
- **NV-W05 / X-5** — confirmations and *Accept all suggestions* need a named person.
- **NV-W06** — the Writer reports the CRGO release actually bundled with the desktop (`crgo_release()` reads
  `data/crgo-snapshot.json`; stand-alone, the constant `CRGO_RELEASE`, now **v0.11.1**).
- **NV-W07** — « Si aucune n'est approuvée » (GOV-01 help, FR); « appétence pour le risque » everywhere.
- **NV-W08** — undetermined P-39.1 conditions are printed, never silently dropped.
- Tests: `meta` pinned to 0.1.1 / v0.11.1; new `test_french_appetence_wording`.

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
