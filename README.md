# CyberRiskGuardian Policy Builder

**AI-assisted Information Security Policy Management and Development System** — a companion application to
[CyberRiskGuardian](https://github.com/ITriskMgr/CyberRiskGuardian).

It interviews an organization about its business, industry and security context, optionally reads the
organization’s existing documents, recommends a policy hierarchy (enterprise policy → topic-specific
policies), asks for the decisions only the organization can make, and produces **editable Microsoft Word
drafts in English, French or both**. Every clause shows what it is based on, and every gap is a highlighted
placeholder rather than an invented fact.

> **Beta 0.2.0.** Generated documents are drafts. They are not legal advice and are not in force until the
> organization’s authorized people review and approve them. Framework references show the topics a clause
> addresses; they are not evidence of conformity.

*Version française plus bas.*

---

## What it does

| Step | What happens |
|---|---|
| 1. Project | Name, interview depth (Express ≈ 21 questions, Standard ≈ 59), document language (EN, FR, or both as separate native files). |
| 2. Interview | Company, industry, size, jurisdictions, data, technology, governance roles, objectives. Industry branches (healthcare, OT/manufacturing, SaaS, education/research, finance). Every question has *Unknown*, *Decide later* and, where relevant, *Not applicable*. |
| 3. Documents | Upload DOCX, PDF, TXT, Markdown, CSV, XLSX — and **scanned PDFs or images (PNG, JPEG, TIFF)**, read by on-device text recognition (OCR) after you ask for it, with a confidence score per page. Text is extracted locally with page/section locators, stored encrypted, and turned into **proposed** facts that quote their source passage. Contradictions between documents are flagged; nothing is applied until you confirm it. |
| 4. Profile | The confirmed organization profile, with the source of each answer (interview or document) and governance observations (e.g. “IT accepts business risk”, “no privacy officer listed”). |
| 5. Legal candidates | Candidate laws, guidelines, contracts and frameworks (Quebec P-39.1 / Law 25, A-2.1, G-1.03, PIPEDA, PHIPA, GDPR, HIPAA, PCI DSS, OSFI B-13, NIS2, client contracts, ISO/IEC 27001, NIST CSF 2.0). **None is ever treated as applicable until a named reviewer records a decision with a rationale.** Clauses that depend on a law are withheld until then. |
| 6. Policy library | 28 catalogue documents across four levels: the enterprise policy, 19 topic policies (14 with full bilingual clause libraries, 5 structure templates), **4 standards** (authentication and passwords, information handling matrix, cryptography, logging) and **4 procedures** (incident response, access provisioning and revocation, exception requests, backup restoration tests). Each has a priority score and the reasons it is — or is not — recommended; standards and procedures follow the package depth chosen in the interview and their parent policy. |
| 7. Decisions | 44 material decisions (MFA scope, leaver deadline, remediation timeframes, exception approver, RTO, monitoring, AI data rules…), each with a common-practice suggestion you may adopt explicitly. |
| 8. Drafts & review | Structured drafts with stable clause IDs, numbering, source badges, legal-review flags, open decisions, implementation gaps and assumptions. Edit any clause (creates a new version; earlier versions are kept). Review findings: unresolved placeholders, broken cross-references, evidence conflicts, legal review, stale drafts. Optional rewording with Claude, validated so it cannot drop placeholders, add numbers, change “must” to “should” or add clauses. |
| 9. Export | One document as `.docx`, or a ZIP package: `01_Governance`, `02_Policies`, `03_Standards`, `04_Procedures`, `05_Registers_Reports` (policy index, assumptions & open decisions, traceability summary + CSV, implementation-gap roadmap). |
| 10. Re-import | Edit a draft in Word, then bring it back: every modified, deleted or added clause is shown with a word-level comparison (and a warning when “should” became “must” or the reverse). You accept or reject each change; applying creates a new version and earlier versions stay intact. |

### The Word files

Native, editable `.docx` (python-docx): title block, red **DRAFT — NOT APPROVED** banner and header, document
control table (ID, version, status, owner, approver, parent, review cycle, dates left blank until approval),
revision history, approval table, updatable table of contents field, numbered clauses with real heading
styles, highlighted placeholders, Appendix A (open decisions), Appendix B (clause-level traceability) and
Appendix C (assumptions, implementation gaps). Document properties carry the policy ID, project document ID,
version and language for later re-import.

### Content sources

The clause libraries are original wording, structured from ISO/IEC 27001:2022 clause 5.2, ISO/IEC 27002:2022
control 5.1, NIST CSF 2.0 GV.PO, the author’s 2004 Quebec policy model and *Introduction to Cybersecurity
Governance* (business ownership of risk, time-bound exceptions approved by the risk owner, four-level
classification, usable role-specific policies). Standards are cited **by identifier only**; no licensed text
is included. The CyberRiskGuardian 0–1 risk-appetite scale is used for appetite statements.

---

## Quick start

Requirements: **Python 3.10+** (3.10 and 3.13 tested; the launcher finds a suitable Python by itself). No Node.js, no database server, no account elsewhere.

| System | Start |
|---|---|
| macOS | Double-click `start.command` (first start creates `.venv` and installs dependencies) |
| Windows | Double-click `start.bat` |
| Linux | `./start.sh` |

By hand:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python serve.py 8120          # opens http://localhost:8120/
```

The server listens on **127.0.0.1 only**. Create an account (it creates your workspace), then a project.
Data lives in `./data` (SQLite database, encrypted uploads, exports, encryption key `data/pb-key`, mode 600).

### Reading scanned documents (optional)

Text recognition runs on your computer; nothing is sent elsewhere. Install one engine:

| System | Command |
|---|---|
| macOS | `brew install tesseract tesseract-lang` |
| Windows | Tesseract installer from UB Mannheim (add it to PATH, or set `PB_TESSERACT` in `.env`) |
| Linux | `sudo apt install tesseract-ocr tesseract-ocr-fra` |
| Any (pure Python) | `pip install rapidocr-onnxruntime` |

Scanned files are stored but **not read until you click *Run text recognition*** in Documents. Recognized
passages carry their page and confidence (“p. 3 (OCR 92%)”), facts from them get a lower confidence, and
low-confidence pages are listed.

### Re-importing Word drafts

Every exported clause carries a hidden Word bookmark with its stable clause ID, and the file properties carry
the document ID and version. Edit freely in Word or LibreOffice (both preserve them), then use *Re-import an
edited Word draft* in Drafts and review. If a marker is lost, the clause is matched by its number and flagged.

### Using Claude (optional)

The app is fully usable offline: drafting is deterministic from the clause library. To enable Claude
rewording and AI fact extraction, copy `.env.example` to `.env` and set:

```
PB_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
PB_AI_MODEL=claude-sonnet-5-5
```

The key stays on the server. Uploaded documents are sent to the provider **only** if the project owner turns
on *Allow AI extraction from uploaded documents*; passages that look like instructions to an AI are never sent.
Each draft records provider, model, prompt version and timestamp — never the source text.

---

## Architecture

```
web/            dependency-free HTML/CSS/JS client (EN/FR interface)
app/main.py     FastAPI JSON API, security headers, CSRF guard, static files
app/security.py local accounts (PBKDF2), sessions, RBAC, tenant scoping, Fernet encryption, audit log
app/questionnaire/  versioned question bank (EN/FR) + condition engine, governance observations
app/ingestion/  safe type sniffing, extraction with locators, injection flagging, rule-based fact extraction
app/catalogue/  policy catalogue, decisions, priority engine, versioned ruleset of CANDIDATE obligations
app/drafting/   clause libraries (EN/FR), composer (tokens → facts/decisions/placeholders), AI provider interface
app/export/     Word renderer, reports, ZIP packaging
migrations/     Alembic (SQLite by default; PostgreSQL via PB_DATABASE_URL)
```

Design decisions are in [`docs/ADR-001-architecture.md`](docs/ADR-001-architecture.md); checkpoint status
and the backlog in [`docs/CHECKPOINTS.md`](docs/CHECKPOINTS.md); security model in
[`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md). The OpenAPI contract is served at `/openapi.json` while running.

Structured JSON (`PolicyVersion.body`) plus normalized `PolicyClause` rows are the source of truth; `.docx`
files are rendered on demand.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q            # 41 tests incl. two browser walkthroughs; no network, no API key
python -m pytest tests/e2e -q        # browser walkthrough (Playwright + Chromium)
```

Covered: the full vertical slice (interview → upload → confirm facts → library → decisions → generate → Word
and ZIP export → change an answer → stale → regenerate v2 → manual edit v3), single-policy export, bilingual
output with identical clause IDs, project deletion removing files, cross-tenant access (404, no leakage),
unauthenticated access, CSRF header, auditor read-only, hostile uploads (disguised executable, legacy OLE,
macro-enabled, archive bomb, path traversal, duplicate), prompt-injection documents never sent to the AI,
ungrounded AI facts discarded, AI rewording that removes placeholders / adds numbers / weakens “must” /
injects clauses rejected, candidate laws never applicable without a named reviewer, obligation-gated clauses,
contradictory documents surfaced and not silently resolved, standards and procedures by package depth with
real Word tables, OCR only after consent on scanned PNG and PDF, oversized images refused, Word re-import
(bookmark match, number fallback, deletions, additions, requirement-strength change, apply as new version,
LibreOffice round-trip, foreign files refused), four synthetic organizations (Montreal SaaS,
Quebec food manufacturer with OT, multi-jurisdiction healthcare network, university) in both languages, PDF
and XLSX extraction, Anthropic wire format, mobile layout without horizontal scroll.

## Limitations (beta)

- OCR quality depends on the scan; handwriting and complex layouts are not reliable. French OCR needs the Tesseract
  French language data (`fra`).
- Four standards and four procedures are provided; five topic entries are still structure templates.
- Re-import compares clause text; edits inside tables (RACI, handling matrix, algorithm list) and heading changes are
  not imported — change those in the application.
- Review/approval workflow (reviewer assignment, executive approval, immutable approved snapshots) is not built:
  every document stays DRAFT.
- SSO, PostgreSQL deployment hardening and a job queue are backlog items.
- Rulesets and reference URLs are dated (2026-10-19) and must be re-verified; they are candidates, never legal conclusions.

## Licence

© 2026 Marc-André Léger. Released under **Creative Commons Attribution-NonCommercial 4.0 International
(CC BY-NC 4.0)**, like CyberRiskGuardian — see [`LICENSE.md`](LICENSE.md).

---

# Français

**Système d’élaboration et de gestion des politiques de sécurité de l’information assisté par l’IA**, compagnon
de CyberRiskGuardian. L’application mène une entrevue sur l’organisation et son secteur, lit au besoin ses
documents existants, recommande une hiérarchie de politiques, demande les décisions qui reviennent à
l’organisation et produit des **ébauches Word modifiables en français, en anglais ou dans les deux langues**
(fichiers distincts partageant les mêmes identifiants de clauses). Chaque clause indique son fondement; chaque
lacune devient un espace réservé surligné plutôt qu’un fait inventé.

> **Bêta 0.2.0.** Les documents produits sont des ébauches. Ils ne constituent pas un avis juridique et n’entrent
> pas en vigueur avant leur révision et leur approbation par les personnes autorisées de l’organisation.

**Démarrage** : double-cliquez sur `start.command` (macOS), `start.bat` (Windows) ou lancez `./start.sh`
(Linux); l’application s’ouvre à `http://localhost:8120/`. Le serveur n’écoute que sur 127.0.0.1. L’interface
offre une bascule EN/FR sur tous les écrans; les données saisies par l’utilisateur ne sont jamais traduites.

**Lois et référentiels** : les lois (Loi 25 / P-39.1, A-2.1, G-1.03, LPRPDE, etc.) sont proposées comme
*candidates*. Aucune n’est considérée applicable avant qu’un réviseur nommé consigne une décision motivée.

**Normes, procédures, ROC et réimportation** : l’application produit aussi 4 normes et 4 procédures (niveaux 3 et 4),
lit les PDF numérisés et les images par reconnaissance de texte locale (après votre autorisation), et réimporte une
ébauche modifiée dans Word en présentant chaque modification pour acceptation ou refus.

**IA** : hors ligne par défaut. Claude peut être activé côté serveur (clé dans `.env`); les documents
téléversés ne lui sont transmis que si le responsable du projet l’autorise explicitement.
