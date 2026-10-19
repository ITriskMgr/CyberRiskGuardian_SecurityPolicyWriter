# Information Security Policy Builder
## Comprehensive Product Requirements and Technical Implementation Specification

**Document ID:** ISP-BUILDER-PRD-001  
**Version:** 1.0 — October 19, 2026  
**Audience:** Product owner, security/GRC specialists, software developers, and Claude / Claude Code  
**Status:** Implementation-ready proposal; all example company data and thresholds are configurable  
**Primary deliverable:** A secure web application that interviews organizations, analyzes supporting documents, develops a tailored security policy architecture, and exports editable Microsoft Word (.docx) drafts.

---

# 1. Executive product definition

## 1.1 Product vision

Build a guided, evidence-informed, AI-assisted application that reduces the effort required to design and maintain an organization's information security policy framework. The application must be suitable for a small business with no existing policies and for a multinational enterprise seeking to modernize an established policy library. It must translate the organization's business context, risk profile, technology environment, legal and contractual requirements, and existing documentation into a coherent and practical hierarchy of governance documents.

The application is **not** a generic text generator or an automated legal adviser. It is an interactive policy-development workbench with structured discovery, traceable evidence, deterministic quality checks, controlled AI drafting, human decisions, version management, and Word export.

The central principle is **human accountability with AI assistance**. AI can suggest policy requirements, highlight gaps, and prepare first drafts; authorized organizational personnel must verify accuracy, approve normative decisions, and formally adopt policies.

## 1.2 Business outcomes

- An organization can create a credible first draft of an enterprise information security policy after a short intake interview, even if it has no starting documents.
- An experienced security manager can generate a **complete, consistent suite** of enterprise and subject-specific policies with standards and supporting procedures where requested.
- Existing policies and other uploaded materials can be reused while preserving their provenance and highlighting inconsistent or outdated requirements.
- Each significant policy clause can be traced to organizational decisions, supplied evidence, applicable obligations, or identified recommendations.
- The Word files can be edited outside the application and reimported in future iterations without losing the canonical policy identity.
- The application can help identify unaddressed policy topics, missing organizational decisions, and controls that need operational implementation.

## 1.3 Scope and exclusions

**Included in the initial product:** profile wizard; adaptive questioning; document upload and analysis; policy catalogue; applicability/priority engine; clause drafting; conflict/gap checking; document review; approval-ready metadata; export of individual and bundled .docx documents; project save/resume; audit history; English and French interface/document support.

**Later or optional:** connectors to SharePoint/Google Drive and ticketing systems; live regulatory content subscription; Microsoft 365 coauthoring; e-signature; employee policy attestations; control testing; automatic training content; ontology integration; multi-agent collaboration; automated policy change monitoring.

**Explicitly excluded from unreviewed automation:** making definitive legal applicability decisions; declaring certification or legal compliance; approving policies on behalf of leadership; inventing documented controls or operational practices; writing back to enterprise systems without explicit authorization.

# 2. Who uses the application

| Role | Permissions and primary workflow |
|---|---|
| Workspace administrator | Configure tenant, retention, integrations, model provider, security settings and user access. |
| Project owner / CISO / security manager | Complete questionnaire, choose policy package, decide policy positions, authorize drafts, request reviews. |
| Policy author / analyst | Upload evidence, review extracted facts, edit content, resolve comments and conflicts, export drafts. |
| Privacy / legal / compliance reviewer | Validate regulatory applicability and high-impact language; request changes or mark review complete. |
| Control owner / IT operations reviewer | Confirm that obligations are feasible, responsibilities are correct, and procedures match actual operations. |
| Executive approver | Review final content and formally approve a policy; must be a human actor. |
| Read-only auditor | Inspect source evidence, policy versions, decision logs, and mappings without changing records. |

Implement role-based access control (RBAC) at organization, project and document level; consider attribute-based access controls (ABAC) later for restricted documents.

# 3. Information security document hierarchy

The application **must** understand the distinction between a policy, standard, procedure, guideline and form. A company may use a different nomenclature, so permit administrators to rename levels without losing the logical hierarchy.

| Level | Document | Purpose | Typical authority |
|---|---|---|---|
| 0 | Security governance charter / security policy framework | Defines governance body, document hierarchy, decision rights, lifecycle, exceptions and overarching objectives. | Board, executive committee or authorized senior leadership |
| 1 | Enterprise Information Security Policy (EISP) | Establishes organization-wide principles, scope, accountability, risk-based expectations and binding high-level rules. | Executive leadership / board as appropriate |
| 2 | Topic-specific security policy | Sets enforceable requirements for a domain such as access control, data classification, incident response or third-party risk. | Delegated executive / CISO / policy committee |
| 3 | Standard / baseline | Specifies measurable, mandatory minimum requirements and defined parameters. | Policy owner / technical authority |
| 4 | Procedure / playbook | Explains who performs an activity, in which sequence, using which tools or forms and evidence. | Process owner |
| 5 | Guideline / job aid / template / record | Provides optional good practices, practical instructions, or evidence of implementation. | Designated owner |

**Non-hierarchical but linked:** risk management plan, incident response plan, disaster recovery plan, business continuity plan, privacy notice, control register, exception register, and training/attestation records. Such artifacts may be necessary, but must not automatically be treated as policies.

**Core rule:** Do not duplicate detailed technical parameters in the EISP if they are better maintained in standards. The EISP delegates to the relevant subordinate document. The policy builder must use parent-child relationships and references to prevent inconsistent language.

# 4. End-to-end experience and state machine

## 4.1 Recommended user journey

**Step A — Start a project.** The user chooses “Create a new policy framework,” “Create one policy,” “Improve existing policies,” or “Update a previous project.” They select the interface and document language, organization name, organization type and jurisdiction.

**Step B — Basic organization interview.** A brief set of about 12–15 questions creates an initial company profile. Offer simple-language tooltips, examples, “Unknown,” “Not applicable,” “Decide later,” and a visible completion indicator.

**Step C — Supporting evidence.** The user uploads existing policies, risk assessments, audits, contracts, compliance documents, organizational charts, inventories and other materials. The application parses each file, displays what it extracted, and lets users confirm or correct candidate facts.

**Step D — Adaptive requirements interview.** Follow-up questions depend on sector, locations, data types, systems, third-party relationships, regulatory candidates, existing controls, risk appetite and desired document depth. Each question explains why it is being asked.

**Step E — Analysis and proposed policy library.** Generate an organization profile and an applicability report that separates confirmed requirements, candidates needing legal review, good-practice recommendations and company decisions. Display a proposed hierarchy of documents, priority and gaps. Let the user add/remove items.

**Step F — Policy decisions and generation.** For unresolved material decisions, ask targeted questions before writing binding clauses. The user can generate a single document or the entire package. First generate a structured outline, then approved clause-level content, then the formatted files.

**Step G — Review and quality assurance.** Show a side-by-side preview with clause citations, provenance and flags: missing owner, unsupported claim, conflicting requirement, unverified law, ambiguous wording, infeasible control, duplicated rule, or incomplete cross-reference. Require explicit acknowledgment of critical unresolved items.

**Step H — Word export and maintenance.** Export individual .docx files or a ZIP collection. Preserve editable heading styles, document control tables, revision history, policy owners, review dates, and appendices. Save structured project data for future revision and reimport edited drafts when requested.

## 4.2 Workflow statuses

`PROJECT_CREATED -> DISCOVERY_IN_PROGRESS -> EVIDENCE_REVIEW -> APPLICABILITY_REVIEW -> LIBRARY_CONFIRMED -> OUTLINE_REVIEW -> DRAFT_GENERATED -> TECHNICAL_REVIEW -> LEGAL_REVIEW (when needed) -> EXECUTIVE_APPROVAL -> APPROVED -> PUBLISHED -> PERIODIC_REVIEW`

Allow `RETURNED_FOR_CHANGES`, `ON_HOLD`, `SUPERSEDED` and `ARCHIVED` transitions. Do not conflate a generated draft with an approved or operationally implemented policy. Publish and approval actions must show an explicit human identity and timestamp.

# 5. Guided discovery questionnaire — detailed functional requirements

## 5.1 General questionnaire mechanics

Questions are organized into themed sections. Every question is represented by a stable ID, text, explanation, data type, choices, validation, required/optional flag, display condition, source, and follow-up triggers. Users can answer in free text, multi-select, numerical form, structured tables or by selecting “Unknown” and “Not applicable.” They can change an earlier answer; downstream analyses must then be marked potentially stale and selectively regenerated.

Provide **Express mode** (12–15 high-value questions, draft with visible assumptions), **Standard mode** (35–50 questions for practical organizational tailoring), and **Comprehensive mode** (approximately 70–100 context-dependent questions for highly regulated or mature organizations). Count ranges are product guidance, not fixed requirements.

An explicit company answer should be authoritative for that company's stated practices **unless** contradicted by stronger evidence or by a recognized legal obligation; in conflicts the application asks the user to decide and records the resolution.

## 5.2 Section A — Basic company profile (always ask)

| ID | Question and input | Reason / default behavior |
|---|---|---|
| ORG-01 | What is the legal name, and what name should appear in the documents? [text] | Document identification and branding. |
| ORG-02 | What is the company's industry and subindustry? [sector picker + text] | Tailors risks and initial document catalogue. |
| ORG-03 | What does the organization do, and what are its critical products or services? [text] | Anchors policy to operational reality. |
| ORG-04 | How many employees, contractors and locations are there? [number bands] | Tailors complexity and accountability. |
| ORG-05 | Where are operations located and where are clients/data subjects located? [jurisdictions] | Identifies **candidate** laws and cross-border issues. |
| ORG-06 | Is the organization private, publicly traded, public sector, non-profit, educational, healthcare, or other? [select] | Governance and obligations. |
| ORG-07 | Who is completing the interview and who will own the policy framework? [role + name or TBD] | Assignment of responsibilities. |
| ORG-08 | Are you starting from scratch or updating existing documents? [select] | Determines document-analysis path. |
| ORG-09 | What are the primary objectives? [multi-select] | Governance, certification readiness, client assurance, audit response, standardization, incident prevention, etc. |
| ORG-10 | Which document languages are needed? [EN / FR / both / others later] | Language-specific templates. |
| ORG-11 | When should drafts be ready? [date optional] | Planning only; no fabricated timeline commitments. |
| ORG-12 | What is your current cybersecurity governance maturity? [unknown / informal / developing / documented / managed] | Adjusts feasible level of detail. |
| ORG-13 | Do you have a CISO/security team, IT manager, privacy officer and risk committee? [roles] | Owners and escalation. |
| ORG-14 | What business activities or technologies are mission-critical? [short text] | Priority and continuity. |
| ORG-15 | Would you like the starter policy package recommended by the app or a custom selection? [choice] | Package assembly. |

The app should permit users to generate a basic EISP using the answers available after this section, while labeling unresolved details as assumptions or decisions pending validation.

## 5.3 Section B — Information, data and privacy

**DATA-01** Categories of information held: employee, customer, payment, healthcare, research, intellectual property, financial, government, controlled technical, industrial, operational technology, personal or sensitive information.  
**DATA-02** Whether a classification taxonomy already exists; if so, names and handling rules.  
**DATA-03** Where data is stored, transferred and processed (on premises, SaaS, hosted cloud, third parties, countries).  
**DATA-04** Known retention obligations and disposal practices.  
**DATA-05** Data sharing, processors, outsourcing and cross-border transfers.  
**DATA-06** Personal data activities, consent, profiling, automated decisions and use of AI involving personal data.  
**DATA-07** Whether the organization maintains privacy notices, impact assessments and breach records.  
**DATA-08** Who is responsible for data ownership, stewardship and privacy governance.

## 5.4 Section C — Infrastructure and operating model

**TECH-01** Cloud providers, SaaS applications and on-premises infrastructure.  
**TECH-02** Remote, hybrid or onsite workforce and BYOD permissions.  
**TECH-03** Industrial control systems (OT/ICS), medical devices, IoT, point-of-sale or critical operational systems.  
**TECH-04** Identity provider, MFA, privileged access and joiner/mover/leaver practices.  
**TECH-05** Endpoint, server, network and mobile environments.  
**TECH-06** Software development, DevOps, AI-enabled development or outsourced application development.  
**TECH-07** Backups, restoration testing, resilience requirements and recovery objectives.  
**TECH-08** Logging, monitoring, outsourced SOC, security incident response and vulnerability management.  
**TECH-09** Important platform or vendor constraints that could make a proposed requirement unrealistic.

## 5.5 Section D — Governance, risks and controls

**GOV-01** Risk ownership, risk appetite/tolerance and escalation process.  
**GOV-02** Security roles, reporting lines, policy ownership, approval authority, board oversight and delegation.  
**GOV-03** Known high-priority cybersecurity risks and material past incidents (without requesting unnecessary sensitive details).  
**GOV-04** Existing security standards and control frameworks.  
**GOV-05** Current control maturity and any formal gap or risk assessments.  
**GOV-06** Exceptions, waivers, approval and compensating-control practices.  
**GOV-07** Security training, annual attestations and disciplinary approach.  
**GOV-08** Internal audit, external audit and customer assessment obligations.  
**GOV-09** Whether requirements should be aspirational, immediately enforceable, or split into current-state and target-state with action plans.  
**GOV-10** Target review cycle, trigger events and authority to approve changes.

## 5.6 Section E — Legal, regulatory and contractual context

**REG-01** Legal jurisdictions and geographic operations; **REG-02** public/private sector status; **REG-03** regulated services and licenses; **REG-04** industry certifications sought or held; **REG-05** contractual customer security obligations; **REG-06** service-provider and supply-chain obligations; **REG-07** applicable privacy and data-protection requirements as understood by the company; **REG-08** regulated government, defense or controlled data; **REG-09** retention, monitoring and employment-law constraints; **REG-10** legal counsel or compliance reviewer availability.

The applicability engine may suggest candidates including Quebec private-sector privacy legislation (often called Law 25), PIPEDA where applicable, GDPR, HIPAA, PCI DSS, NIS2, DORA, contractual security addenda or sectoral rules. It **must not** mark any of these as legally applicable solely because a user selects an industry. Instead show applicability reasoning, necessary conditions, exceptions, jurisdiction and date, and a confirmation action for a responsible person.

## 5.7 Section F — Drafting and formatting preferences

**DOC-01** Output policy types and catalog selection; **DOC-02** package depth (high-level only; policies and standards; complete policies and procedures); **DOC-03** level of prescription; **DOC-04** default organization terminology; **DOC-05** branding and optional uploaded Word template; **DOC-06** numbering and document code; **DOC-07** policy clause voice (mandatory “shall/must” vs explanatory prose); **DOC-08** reviewer and approver names or positions; **DOC-09** language and translation style; **DOC-10** whether to include control mapping tables in appendices or a separate traceability report; **DOC-11** whether to generate implementation recommendations apart from binding policy language; **DOC-12** whether to include sign-off and acknowledgement pages.

## 5.8 Industry-specific branches

**Healthcare:** personal health information, clinical availability, connected medical devices, third-party care networks, downtime safety, clinical incident escalation.  
**Financial services:** critical operations, outsourced technology, payment systems, fraud, business continuity, risk reporting and sector-specific requirements.  
**Retail/e-commerce:** payment-card processing, digital commerce, customer data, fraud and third-party platforms.  
**Manufacturing/OT:** safety, change windows, segmentation, supplier access, safety-critical systems and IT/OT separation.  
**Education/research:** student records, research data, academic freedoms, shared laboratories, grant and contractual requirements.  
**Government/defense:** classified/controlled data where applicable, procurement contracts, security clearances, supply chains and data sovereignty.  
**SaaS/developer:** secure SDLC, CI/CD, cloud shared responsibility, API security, SBOM, secrets, tenant isolation and customer assurance.

Branch selection must never imply regulatory applicability without confirmation.

## 5.9 Adaptive question algorithm

1. Ask universal questions; store answers and confidence/source.
2. Derive candidate topics, legal conditions, potential high risks and decision gaps.
3. Rank follow-up questions using importance, ability to change the outcome, available evidence, and questionnaire burden.
4. Prefill answers from uploaded documents only as **proposed** responses with page/section attribution, requiring user confirmation where material.
5. Avoid asking questions already answered with adequate evidence unless there is a contradiction.
6. Ask the user to decide material normative parameters (such as MFA scope, exception approval or password handling) before encoding them as binding requirements.
7. When the user skips a question, preserve an explicit unknown or provisional assumption rather than generating a false factual claim.
8. Let the user return to any question; dependent policies become “needs regeneration/review.”

# 6. Supporting documents and evidence ingestion

## 6.1 Accepted sources

Initial supported upload types: **DOCX, selectable-text PDF, TXT, Markdown, CSV, XLSX** and optionally PPTX. Add image PDFs and scanned images in a later OCR-enabled phase with accuracy warnings. Implement web page ingestion by URL only through an allowlisted and separately authorized source connector, not arbitrary uncontrolled fetching.

Recognize documents such as corporate strategy, org charts, existing policies and procedures, ISO scope and Statement of Applicability, risk assessments, risk registers, business impact analyses, technology inventories, data maps, contracts, customer requirements, audit reports, privacy notices, incident lessons learned, security architecture, internal standards, regulator publications and sample policies. A user can designate an uploaded **.docx style/template file** separately from source evidence.

## 6.2 Intake and extraction

For each document: virus/malware scan; identify actual MIME type; enforce limits; securely extract text and tables; identify title, author (if available), version, effective date, section and page references; classify content; detect duplicate documents; chunk with section headings and stable offsets; provide previews; and index retrievable evidence. For scanned documents, request explicit permission for OCR and report uncertain extraction.

Each candidate fact includes source ID, filename, location/page, extracted quotation or concise paraphrase, confidence, extraction timestamp, review status and related organization field. Source files are untrusted inputs: retrieved instructions embedded in them must never be treated as application instructions.

## 6.3 Evidence source ranking and contradictions

Recommended hierarchy, **subject to applicability and explicit user resolution**: confirmed binding law/regulation; confirmed contractual requirement; authorized corporate governance decision; current approved policy/standard; confirmed user answer; other uploaded document; advisory framework; AI recommendation. A newer version of the same approved policy should typically supersede an older version, but never silently resolve contradictions without user awareness.

Display differences such as an old policy requiring a 90-day password rotation while newer guidelines specify risk-based authentication. The app should identify which is current, describe the conflict and ask the owner to decide; it should not automatically overwrite an approved company requirement.

## 6.4 Data protection and content licensing

Preserve tenant isolation and configurable document retention/deletion. Encrypt objects and derived text, restrict downloads, redact logs, and minimize third-party AI transmission. Clearly disclose when uploaded material will be passed to an LLM provider. Respect copyright and licensing, especially for ISO standards or paid regulatory research; do not ship copyrighted full texts as built-in unrestricted content. Store licensed content only within authorized scope and generate original policy prose rather than reproducing standards.

# 7. Policy library and recommendation engine

## 7.1 Initial recommended catalogue

Catalogue entries contain a stable document identifier, canonical name, type/level, prerequisites, parent/child links, triggering conditions, responsible role, priority, rationale and supported template. Recommended starter catalogue:

| Domain | Candidate policies and related documents |
|---|---|
| Enterprise governance | Enterprise Information Security Policy; governance charter; security roles and accountability; risk management; policy exception and waiver management; compliance and audit cooperation. |
| People | Acceptable use; personnel security; awareness and training; remote work and teleworking; mobile device/BYOD. |
| Information | Data classification and handling; privacy and personal information; records retention and secure disposal; encryption and key management; secure information transfer. |
| Identity and access | Identity and access management; privileged access; authentication/MFA standards; third-party and service-account access. |
| Infrastructure and operations | Asset management; secure configuration; vulnerability and patch management; change management; endpoint security; network security; logging and monitoring; malware prevention. |
| Architecture and development | Cloud security; secure software development; application/API security; artificial intelligence acceptable and secure use; secrets management. |
| Suppliers | Third-party security and supplier risk management; outsourcing; external connectivity; supplier access and termination. |
| Detection and recovery | Incident management; security incident response plan; backup and recovery; business continuity; disaster recovery; crisis communications. |
| Physical / specialized | Physical security; OT/ICS security (conditional); research data (conditional); payment security (conditional); healthcare/clinical system security (conditional); controlled information (conditional). |

**Important:** This is a catalogue, not a list of documents every organization must create. For a small company, closely related requirements can be consolidated. Highly regulated or complex organizations may need additional dedicated documents.

## 7.2 Priority formula and explanation

The recommendation engine proposes priority using weighted dimensions: confirmed applicability (0–5), risk exposure (0–5), current maturity gap (0–5), dependency on other documents (0–5), business criticality (0–5), and requested scope (0–5). Illustrative weights are 25%, 25%, 15%, 15%, 15%, and 5%; **these are configurable product heuristics and not claims from a standard**. A confirmed time-sensitive binding obligation can supersede the numeric score. Display the reasons, not just a number.

Default package for a modest general organization: EISP, acceptable use, access control, asset/data classification and handling, incident response, backup/recovery, third-party security, vulnerability/change management and risk/exception governance. More specific policies may be generated only if interview answers justify them.

## 7.3 Dependency consistency

For each child policy record: parent policy ID, referenced definitions, delegated standards, overlapping topics, related controls and coverage. Global constraints include: consistent role names; one canonical data-classification scheme; consistent incident severity definitions; consistent exception approval; consistent review periods; no conflicting risk ownership; no contradictory third-party access rules; common normative language; no undocumented fabricated control. Include a policy-library matrix that identifies coverage and dependencies.

# 8. Requirements and framework mapping

## 8.1 Source types

- **Legislation/regulation:** candidate obligations with jurisdiction, applicability conditions, effective/updated date, primary source URL, and legal review status.
- **Contract:** customer/supplier contract requirement with clause/section and legal review status.
- **Mandatory organization decision:** approved business rule, security posture or governance requirement.
- **Framework/control:** best-practice guidance or a mandated framework requirement **only when adoption is confirmed**, with standard and version identifier.
- **Assessment observation:** audit finding, risk, gap or incident lesson learned; not a binding requirement on its own.
- **AI recommendation:** suggested practice with rationale and explicit non-binding status.

## 8.2 Reference frameworks, version-aware

Initial mappings: ISO/IEC 27001:2022 (including applicable amendment tracking), ISO/IEC 27002:2022, NIST CSF 2.0, NIST SP 800-53 Rev. 5 / Release 5.2.0, CIS Controls v8.1, COBIT 2019, and other frameworks licensed/authorized and explicitly selected by the organization. NIST CSF 2.0 **GV.PO-01 and GV.PO-02** are especially relevant to establishing and periodically updating policies. Add industry-specific modules as optional rule packs rather than hardcoding all rules into prompts.

Framework mapping is not proof of conformance. A policy may **address** a control concept while the organization has not implemented or tested any supporting control. Store separate fields for “policy coverage,” “implementation evidence,” “operating effectiveness” and “review status.”

## 8.3 Traceability ledger

Every material drafted clause should carry:

`clause_id | document_id | clause_text | source_class | source_ids | source_locator | framework_refs | applicable_jurisdiction | applicability_status | rationale | assumptions | confidence | reviewer_status | last_reviewed_at`

Use a structured internal model; place references in the Word appendix or separate review report, not necessarily after every sentence in the policy body. Show the full traceability ledger in the application.

# 9. Authoring engine and drafting guardrails

## 9.1 Two-pass generation

**Pass 1: architecture and outline.** Determine target audience, document purpose, scope, owners, key decisions, minimum sections, references, dependent documents, contradictions and missing evidence. The user may approve/edit the outline before full drafting.

**Pass 2: clause generation.** Draft in small sections using structured inputs, retrieved evidence, approved policy positions and authorized source references. Use consistent clause numbering and stable clause IDs. Never generate the entire document family as one unvalidated, unstructured model response.

## 9.2 Policy drafting rules

1. Write enforceable and testable obligations where a policy is intended to be mandatory. Use defined actors and verbs such as “must” or “shall” consistently.
2. Avoid unbounded phrases such as “as soon as possible,” “regularly,” “strong encryption” or “appropriate security” unless a linked standard or risk-based approval mechanism defines the parameters.
3. Do not create invented facts about products, staffing, monitoring, audits, control deployments or legal compliance.
4. Distinguish **current state** from **desired future requirements** and list implementation tasks separately. If a rule requires capabilities that do not yet exist, flag the implementation gap.
5. Ensure feasibility with organization size, budget, outsourcing, available tools, safety constraints and operations.
6. Name the policy owner and approver only when known; otherwise use clear placeholders such as `[POLICY OWNER — CONFIRM]`.
7. Where needed, distinguish employees, contractors, suppliers, subsidiaries and visitors in applicability statements.
8. Include exceptions and risk acceptance with delegated approval, expiration and compensating controls; avoid blanket, ungoverned exemptions.
9. Preserve meaningful organizational terminology, department names and language conventions.
10. Do not claim a policy is ISO certified, GDPR compliant or legally sufficient simply because it refers to a framework.

## 9.3 Mandatory document sections

**Enterprise policy:** cover/document control; approval status; purpose and objectives; organizational scope; definitions and interpretation; governance principles; leadership commitment; risk management; information ownership/classification; people and third-party obligations; control domains and delegated documents; roles/responsibilities; exceptions; monitoring and compliance; review cycle and triggers; references; approval and revision history.

**Topic-specific policy:** document control; purpose; scope; governing principles; authoritative roles; defined mandatory requirements; exceptions; oversight/measurement; nonconformance and escalation; related standards/procedures; definitions where needed; references; revision history.

**Standard:** scope; mandatory measurable parameters; system/asset applicability; ownership; evidence; exception route; cross-reference to enabling policy; review process.

**Procedure:** trigger; prerequisites; inputs; roles/RACI; sequential actions; branches/escalation; records/evidence; deadlines; testing and maintenance.

Do not pad a short, high-level policy with irrelevant generic text. Use a modular section schema so users can include or exclude sections with an explanation.

## 9.4 Controlled placeholders

Allow only explicit placeholders typed as `ROLE`, `DATE`, `VALUE`, `SOURCE`, `DECISION`, `APPROVER`, or `TECHNICAL_DETAIL`. Every placeholder must be inventoried in the draft-review screen and reflected in a separate **Open Decisions and Implementation Actions** report. Block “ready for formal approval” status when high-severity placeholders remain unresolved, while permitting draft export.

## 9.5 Multi-document coherence check

After drafting each document and again before package export, run deterministic checks and LLM-assisted semantic review for definitions, identifiers, review cycle, responsibilities, cross-references, key standards, parameter conflicts, inappropriate duplicate text, applicable audience and regulatory caveats. Present findings with source/context, severity, suggested fix and user accept/reject decision. AI must not silently change policies that the user already approved.

# 10. Word document generation and templates

## 10.1 First-class DOCX output

The .docx is a primary product artifact, not a PDF converted to Word. Generate native Word documents with real paragraph/heading styles, editable text, numbered sections, tables, headers/footers, page numbers and accessible document structure. Use `python-docx` or an equivalent native OOXML library; use a templating system for approved organization-branded layouts.

The default template should contain: company name/logo, title, unique policy number, version, **DRAFT** status, classification, owner, approver, effective date (blank until approved), next review date, revision-control table, approvals/sign-off, table of contents (updatable Word field), clear headings, definitions, policy clauses, reference documents and appendices.

## 10.2 Output bundle

1. One `.docx` for each selected policy or supporting artifact.
2. A ZIP folder with an organized structure: `/01_Governance`, `/02_Policies`, `/03_Standards`, `/04_Procedures`, `/05_Registers_Reports`.
3. A **Policy Library Index** (`.docx` and optional CSV) listing IDs, titles, owners, statuses and dependencies.
4. A **Drafting Assumptions & Open Decisions** report (`.docx`) distinguishing confirmed facts from assumptions.
5. A **Requirements and Traceability Matrix** (CSV/XLSX optional; Word summary required in MVP) listing mapped sources and review status.
6. An **Implementation Gap and Roadmap** (`.docx`, optional in MVP), identifying policy requirements that need people, process or technical work before enforcement.

For bilingual export, generate **separate native English and French files**, sharing canonical clause IDs, and flag translation discrepancies requiring review. Do not assume that automatic translation guarantees legal equivalence.

## 10.3 Reimport and compare

Post-MVP: permit reimport of a Word document using its embedded ID/version metadata; parse headings and stable clause IDs; show additions, deletions and wording changes; reconcile conflicts with structured canonical text; never overwrite prior versions without a save/confirm action.

# 11. Application UX: screens and interactions

| Screen | Required elements |
|---|---|
| Home / workspace | Project list, new project, resume, export history, recent changes. |
| Project setup | New/single-policy/modernization mode; language, company, industry and jurisdictions. |
| Organization interview | Progress bar, sections, contextual help, defaults, save/back, skip with explicit unknown, conditional questions. |
| Documents & evidence | Drag-and-drop, file categorization, status, extraction preview, source confidentiality, metadata and deletion. |
| Confirmed organization profile | AI-extracted proposed facts, answer/source comparison, confidence and approve/correct controls. |
| Applicability review | Confirmed / candidate / not applicable regulations, applicability factors, responsible reviewer, links, timestamps. |
| Policy catalogue | Hierarchical tree with suggested policies, reason, priority, effort, required decisions and toggle selection. |
| Policy settings / outline | Document depth, owners, approval authority, outline, shared definitions and dependencies. |
| Draft editor | Section navigator, editable text, clause provenance, comments, proposed revisions, unresolved fields. |
| Quality dashboard | Findings, severity, cross-document conflicts, missing data, controls vs evidence, readiness score explanation. |
| Review and approval | Reviewer assignments, approvals/rejections, immutable versions, audit trail. |
| Export center | DOCX individual, ZIP package, optional matrix and reports; export snapshot, labels and user-selected template. |
| Settings | Roles, document templates, rulesets, retention, AI provider configuration and security options. |

### UX details

Never display a monolithic questionnaire. Keep roughly 4–8 questions per step, show estimated progress, explain relevance and allow users to exit and resume. Make the “Generate basic EISP draft now” action available once minimum profile information is completed. Show why each suggested document is relevant, and show an **edit selection** option before generation.

# 12. Data model and persistence

At minimum, design these normalized entities (UUID primary keys; creation/update timestamps; actor IDs; per-tenant scoping):

| Entity | Essential fields / relationships |
|---|---|
| `Organization` | legal_name, display_name, sector, jurisdictions, headcount_band, languages, confidentiality_settings. |
| `Workspace` and `Project` | tenant, creator, mode, workflow_state, project_version, target_language, assumptions_policy. |
| `MemberRole` | principal, organization_id, project_id, role, authorization scope. |
| `QuestionDefinition` | code, version, section, type, allowed_values, condition_expression, help, priority. |
| `Answer` | question_code, value, answer_status, source, confidence, author, updated_at. |
| `SourceDocument` | blob_id, filename, hash, MIME, classification, version, provenance, ingestion_state, retention. |
| `EvidenceSegment` | source_id, section/page/offset, text or excerpt pointer, embedding_id, extraction_confidence. |
| `OrganizationFact` | fact_type, value, evidence_links, confirmation_state, conflict_group. |
| `Obligation` | source_type, identifier, version, text/summary, jurisdiction, applicability_criteria, verified_date, reviewer. |
| `ApplicabilityDecision` | obligation_id, applies/candidate/not_applicable, rationale, reviewer, date. |
| `PolicyTemplate` | policy_code, type, hierarchy, scope, section schema, prerequisites, version. |
| `PolicyDocument` | canonical_policy_id, project_id, title, hierarchy_level, owner, status, current_version. |
| `PolicyVersion` | document_id, version, outline, body, creator, AI_model_metadata, draft_status. |
| `PolicyClause` | stable clause_id, version, section_id, normative_text, owner, applicability, related clauses. |
| `ClauseSource` | clause_id, obligation_id/evidence_id/answer_id, relation_type, confidence. |
| `Issue` | type, severity, evidence, related documents, proposed fix, resolution, decision_maker. |
| `ReviewTask` | document_version, reviewer_role, assigned_user, outcome, rationale, timestamp. |
| `Approval` | immutable version, approver identity, approval date, action, scope and signature method. |
| `ExportJob` | package version, template, language, generated files, hash, creator, expiry. |
| `AuditEvent` | entity/action/actor/timestamp, before/after metadata, correlation_id, non-sensitive details. |

Retain section text as structured JSON plus normalized clause rows; rendered Word files are **derived artifacts**, not the sole source of truth. Use explicit migration versions and optimistic locking.

## 12.1 Canonical structured policy document example

```json
{
  "policy_id": "POL-IAM-001",
  "policy_type": "topic_policy",
  "title": "Identity and Access Management Policy",
  "language": "en-CA",
  "status": "DRAFT",
  "parent_policy_id": "POL-EISP-001",
  "owner_role": "Information Security Manager",
  "approver_role": "Executive Sponsor",
  "scope": ["employees", "contractors", "managed systems"],
  "sections": [
    {
      "section_id": "SEC-ACCESS-REQ",
      "heading": "Access requirements",
      "clauses": [
        {
          "clause_id": "POL-IAM-001-C012",
          "normative_text": "Access to organizational systems must be authorized by an accountable system or information owner before provisioning.",
          "source_type": "organization_decision",
          "source_ids": ["ANSWER-GOV-02"],
          "review_status": "needs_owner_confirmation",
          "assumptions": []
        }
      ]
    }
  ],
  "open_decisions": [
    {"id": "D-017", "prompt": "Confirm which role authorizes access to third-party SaaS systems."}
  ]
}
```

This is an **illustrative schema and clause**, not a claim that a specific company has adopted that requirement.

# 13. System architecture and technology recommendation

## 13.1 Pragmatic reference stack

**Frontend:** Next.js / React / TypeScript with accessible UI components, typed forms, i18n, tree catalog, rich-text editor and preview.  
**API/application:** Python FastAPI with Pydantic data validation and a documented OpenAPI contract.  
**Persistence:** PostgreSQL (tenant-scoped data, JSONB as needed); PostgreSQL full-text search, and pgvector only if semantic retrieval is justified.  
**Asynchronous processing:** a Redis-backed queue with Celery/RQ for extraction, AI drafting and DOCX export; use an in-process synchronous job path for the simplest local prototype.  
**File storage:** private S3-compatible blob storage with tenant-scoped prefixes; encrypted local filesystem for development.  
**AI gateway:** Anthropic Claude API through a provider-agnostic interface; secure server-side credentials; configurable model name, token budgets and feature-specific policy.  
**Document services:** python-docx / native OOXML for DOCX, a safe PDF text parser, openpyxl for spreadsheets, strong MIME validation, malware scanning.  
**Deployment:** containerized services using Docker Compose for development and a hardened production deployment with secrets, TLS, backups and monitoring.

This is a **recommendation**, not a requirement to use the named framework. If Claude is working in an existing codebase, it should inspect the repository and reuse compatible patterns before introducing new infrastructure.

## 13.2 Component boundaries

1. Identity, organizations and RBAC.
2. Guided interview and adaptive question rules.
3. Source file upload, parsing, classification and evidence repository.
4. Organization profile reconciliation.
5. Framework, obligation and applicability knowledge base (versioned rule packs).
6. Policy catalogue and dependency graph.
7. AI orchestration with typed inputs and structured outputs.
8. Clause editor, review and QA checks.
9. DOCX/template rendering and ZIP export.
10. Audit log, monitoring, administration and scheduled policy-review reminders (optional).

**AI must not be the source of truth for deterministic data.** The application decides project state, user permissions, required sections, document IDs, source metadata, approved requirements and export rules. Models generate proposed text and semantic analysis in strict structured formats; all changes are validated by application logic.

## 13.3 AI workflow

`user answers + verified evidence -> structured context object -> candidate applicability / recommendations -> user confirmations -> policy architecture -> outline -> per-section clause generation -> schema validation -> deterministic checks -> semantic consistency review -> user review -> Word rendering`

Use separate prompts/tasks for extraction, fact reconciliation, applicability **candidate** identification, package selection, outline generation, clause drafting, cross-document review and user-facing explanations. Version prompt templates, record the AI model version and generation timestamp, and validate every JSON response. Use retrieval restricted to the current tenant's authorized project sources. Place strict upper bounds on chunks, number of retries and cost.

## 13.4 Potential API surface

`POST /projects`, `GET /projects/{id}`, `PATCH /projects/{id}`  
`GET /questions?project_id=...`, `PUT /projects/{id}/answers/{question_code}`  
`POST /projects/{id}/sources`, `GET /projects/{id}/sources`, `DELETE /sources/{id}`  
`GET /projects/{id}/facts`, `POST /facts/{id}/confirm`  
`GET /projects/{id}/applicability`, `POST /applicability/{id}/decision`  
`GET /projects/{id}/catalogue`, `PUT /projects/{id}/selection`  
`POST /projects/{id}/outline`, `POST /projects/{id}/drafts`  
`GET /policies/{id}/versions`, `PATCH /policies/{id}/clauses/{clause_id}`  
`POST /policies/{id}/validate`, `POST /policies/{id}/reviews`  
`POST /projects/{id}/exports`, `GET /exports/{job_id}`

All endpoints require tenant authorization, documented schemas, input constraints and consistent error handling; downloads should use expiring, authenticated retrieval rather than public object URLs.

# 14. Security, privacy and safety requirements for the application

## 14.1 Minimum security controls

- OIDC/SAML SSO where available, MFA for privileged users, RBAC and strict tenant isolation in data, search, cache, prompt context, jobs and exported files.
- TLS everywhere, encryption at rest, key management, environment-based secrets and no API keys in client code.
- File-type sniffing, malware scanning, size limits, archive-bomb protection, parser isolation, strict upload allowlists and sanitized filenames.
- Source documents treated as untrusted data; prompt-injection defenses, content delimiters, no model-driven arbitrary code execution, no model-driven URLs or privileged tool use.
- No automatic external web retrieval triggered by uploaded instructions; validated allowlisted research tools if later added.
- Data minimization, per-project delete/export, configurable retention, secure disposal and clear AI provider data-processing disclosures.
- Auditable sensitive actions; logs must avoid raw source content, secrets and large prompt payloads by default.
- Secure background jobs, idempotent generation actions, rate limits, quotas and cancellation; safe errors without sensitive data leakage.
- Explain use of AI and forbid representing machine-generated drafts as authorized policies.

## 14.2 Model quality and legal safeguards

Treat external legal or standards knowledge as dated reference material. Record the version and source URL. Show “verification required” for uncertain jurisdictional scope and legal obligations. Do not infer statutory status from control-mapping labels. Provide an optional **legal/compliance sign-off gate**, especially for privacy, employee monitoring, records retention, cross-border transfers, payment data, financial institutions, health information and government/defense matters.

If the model lacks a reliable source for a statement, it should say **“Not verified — reviewer confirmation required”** or omit the claim. It must not fabricate citations, clause numbers, or framework mappings.

## 14.3 Risks to threat-model and test

Prompt injection in uploaded documents; cross-tenant retrieval leakage; hallucinated legal requirements; indirect prompt compromise of document output; unauthorized approvals; malicious office files; access to deleted project content through embeddings/caches; source content exfiltration; data poisoning; export of an outdated draft as approved; document generation denial-of-service; reviewer confusion caused by inconsistent translations; concealed contradictions across policies.

# 15. Review, approval and quality management

## 15.1 Validation categories

**Structural:** mandatory sections, policy ID/version, purpose, scope, owner, approval state, definitions, references and revision history.  
**Normative quality:** testability, specific actor, action, exception mechanism, unambiguous requirement, non-conflicting words.  
**Evidentiary:** support for company-specific facts, reliable source locators, no invented organization decisions, candidate legal rules disclosed.  
**Coherence:** compatible roles, parameters, classifications, standards, cross-document links, dates and escalation channels.  
**Operational feasibility:** known tools, current capabilities, outsourced responsibilities, significant rollout gaps.  
**Document quality:** spelling, accessible styles, consistent numbering, branding, working Word structure, editable content and no broken fields.

A readiness indicator is useful only if accompanied by specific findings. Do not create an opaque 'compliance score' that implies an audit opinion. Proposed thresholds are product defaults, not recognized standards.

## 15.2 Review lifecycle

Draft author review -> control/process owner review -> privacy/legal review when flagged -> delegated governance review -> executive approval -> publication/attestation (where configured). Each review records identity, document version, date, findings and decision. Any material post-approval change creates a new version and requires renewed approval according to organization-defined rules.

Provide a policy maintenance mechanism: periodic review date plus event-driven triggers such as material legal change, incident, major system deployment, acquisition, new jurisdiction, new vendor model or significant risk change. Review reminders should not automatically modify approved text.

# 16. Product backlog and prioritized requirements

## 16.1 P0 — Must have for an end-to-end MVP

- Multi-project creation, save/resume and basic authentication.
- One-organization guided intake with Express and Standard questioning.
- Basic industry-based branching and profile summary.
- Upload DOCX/PDF/TXT and extract source-attributed text.
- User confirmation/correction of extracted company facts.
- Seed policy catalogue; user-controlled selection.
- Draft EISP plus at least **five** core topic-specific policies from structured templates.
- Model provider abstraction and typed, validated AI generation.
- Document control, clause IDs, placeholders and explicit DRAFT markings.
- Essential QA for missing data and policy inconsistencies.
- Native Word export for single policy and ZIP export for selected package.
- Tenant scoping, access control, encryption, safe document handling and audit records.
- Core automated tests plus a realistic end-to-end scenario.

## 16.2 P1 — Production-worthy capabilities

- Comprehensive adaptive interview with industry packs.
- Formal applicability decisions and versioned framework mappings.
- Source-level traceability, semantic retrieval and contradiction management.
- In-browser clause-level editor, comments and review assignment.
- Technical/legal/executive approval workflow; immutable revisions.
- Comprehensive document catalogue; configurable templates; EN and FR outputs.
- Implementation-gap report and organizational standards/procedures.
- Strong production deployment, observability, backups, import/export and security assessments.

## 16.3 P2 — Enhancements

- Word reimport/round-trip and true tracked-change comparison.
- Connector integrations and policy attestation/e-signature.
- Enterprise-wide policy lifecycle monitoring and regulatory watch feeds.
- Ontology-driven reasoning and synchronization with external GRC/risk platforms.
- Policy metrics, advanced analytics and evidence-based control implementation tracking.

# 17. Implementation plan for Claude / Claude Code

## Phase 0 — Clarify operating assumptions and prepare repository

Produce a short architecture decision record (ADR) defining deployment mode, database, auth, model provider interface, source handling, languages, document retention and target personas. Inspect an existing repo before choosing patterns. Initialize source control, environment examples, lint/formatter, package lock files, basic CI, and local setup instructions. Do not request production API keys for development; use mocks.

**Exit:** app boots locally, health endpoints work, configuration is documented, CI runs.

## Phase 1 — Model the policy domain and structured inputs

Implement entities, database migrations, questionnaire definitions, policy-template schemas, project state machine and seed catalog. Include versioned examples, migrations, and audit events. Use JSON Schema/Pydantic or equivalent to validate all model-facing payloads.

**Exit:** can create organizations/projects, record answers and retrieve seeded policy trees without using AI.

## Phase 2 — Guided interview UX

Implement project wizard, adaptive display conditions, typed answers, save/resume, uncertainty choices, summary, and Express/Standard paths. Include tooltips, basic accessibility and language infrastructure.

**Exit:** complete a saved interview in a browser and see a structured organization profile.

## Phase 3 — Document ingestion and evidence confirmation

Implement secure upload, file store, parsing, metadata/segments, classification preview, citation pointers and fact-confirmation UI. Add contradiction flags and deletion behavior. No vector DB is necessary until straightforward full-text search is insufficient.

**Exit:** uploaded material can support a proposed fact with a traceable document locator, and the user can accept/reject it.

## Phase 4 — Applicability candidates and policy selection

Create versioned rulesets for jurisdiction/sector/framework candidates, explicitly distinguish confirmed vs unverified applicability, implement prioritized document catalogue and dependency validation.

**Exit:** app produces an explainable proposed policy library, the user can amend it, and decisions persist.

## Phase 5 — Structured drafting

Build the LLM provider interface and mock model; create independent prompts for outline and clause drafting; add deterministic checks, per-section generation, citations to organizational facts, decision placeholders, idempotency, retries and cost logging. Seed EISP plus five topic templates first.

**Exit:** app generates a structured, reviewable EISP and five topic policies from the same company profile without obvious contradictions.

## Phase 6 — Native Word export

Implement company-branded template styles, document-control table, headings, numbering, references, revision table, approval placeholder, updated Word TOC field and ZIP package. Test with Word and LibreOffice rendering, and visually inspect a generated set for layout defects.

**Exit:** files open, are truly editable, and render correctly; document metadata and IDs match the application records.

## Phase 7 — Review, consistency and governance

Create issue lists, reviewer decisions, document snapshots, diff/versioning, permissions and optional approval gates. Add cross-document controls and a package index/assumptions report.

**Exit:** a reviewer can trace a key clause, find gaps, request correction and export a new revision without corrupting prior versions.

## Phase 8 — Hardening, testing and handover

Conduct tenant-isolation tests, prompt injection tests, upload malicious-content tests, load/cost tests, access-control tests, document rendering tests, accessibility review, dependency scanning and external security review where appropriate. Prepare install/ops/admin/user guides and maintenance runbooks.

**Exit:** reproducible deployment, automated regression suite and documented residual risks/limitations.

## 17.1 Development cadence

Deliver vertical slices. Every phase should include running code, migrations, fixtures, unit tests, a short change log, and instructions to validate the result locally. Avoid generating an entire untested architecture in one pass. After the MVP works end-to-end, enrich catalog depth, language support and enterprise governance features.

# 18. Acceptance criteria and tests

| Test ID | Scenario | Pass condition |
|---|---|---|
| AT-01 | Small technology service company, no documents | Express interview leads to coherent EISP draft with pending decisions, not invented facts. |
| AT-02 | Quebec private-sector SME with personal information | App proposes privacy-governance considerations and requests confirmation, rather than falsely declaring the entire legal landscape applicable. |
| AT-03 | Healthcare provider, critical systems | Conditional interview emphasizes sensitive data, clinical uptime and sectoral rules; applicability remains reviewable. |
| AT-04 | User uploads an approved access policy | Relevant clauses are extracted with source location and reviewable proposed facts. |
| AT-05 | Old and new documents disagree on MFA | User sees a conflict; neither value is silently chosen. |
| AT-06 | User selects only one topic policy | Single .docx is produced, with parent-policy reference as applicable and no unrequested package. |
| AT-07 | User selects EISP plus five policies | ZIP contains all selected editable .docx files, naming/index, shared terminology and matching versions. |
| AT-08 | User leaves the policy approver unknown | Draft remains exportable but contains an explicit unresolved approver placeholder. |
| AT-09 | Uploaded PDF contains instruction to reveal data or ignore user | AI treats it as untrusted source text and does not follow the instruction. |
| AT-10 | Cross-tenant query for sources or exports | Access is denied; no file content or metadata leaks. |
| AT-11 | Company changes from no-BYOD to BYOD permitted | Relevant questions and document dependencies are refreshed and drafts are marked stale. |
| AT-12 | French output | French policy has native headings/styles, correct metadata and the same canonical clause identities. |
| AT-13 | User requests deletion | Original documents and derived indexes/artifacts are deleted or scheduled for deletion under the disclosed retention policy. |
| AT-14 | Binding regulatory rule lacks authoritative citation | It cannot be presented as verified or automatically confirmed. |
| AT-15 | Word regression | Generated documents render without overlapping, clipped or corrupted tables and remain editable in Word. |
| AT-16 | Existing approved version edited | New revision is created; approved snapshot/audit record remains intact. |

## 18.1 Sample reference organizations for QA

Use **synthetic** fixtures: (A) 35-person Montreal software firm using AWS/Microsoft 365, (B) 600-person Quebec food manufacturer with plants and outsourced IT, (C) 2,000-person multi-jurisdiction healthcare services network, and (D) university with research and student records. Include deliberately incomplete answers and conflicting documents in tests. No fixture is a factual assertion about a real enterprise.

# 19. Example first-run experience and sample decisions

**Sample user answers:** “Northstar Digital Services Inc.” (fictional), Canadian private technology services firm, 85 staff, operates in Quebec and Ontario, cloud-first, handles employee and customer data, has limited policy maturity, uses outside SaaS vendors, wants EN/FR policies, wants a first draft for executive review.

**System summary:** “We recommend starting with an Enterprise Information Security Policy, Acceptable Use, Information Classification and Handling, Identity and Access Management, Incident Response, Third-Party Security, Backup and Recovery, and Risk/Policy Exceptions. We also identified candidate privacy requirements that should be reviewed for applicability. Your IT/security roles and policy approver are not fully specified.”

**Adaptive follow-up:** “Does the company permit personally owned devices to access work email or client data?” If yes, offer a BYOD policy or dedicated standard; if no, avoid creating an elaborate BYOD program by default. Ask “Who may approve a temporary exception to MFA requirements?” before drafting the exceptions mechanism. Ask whether employee data and customer data are stored outside Canada to clarify cross-border documentation needs, **not** to conclude automatically that a particular statute applies.

**Draft excerpt, contingent on confirmation:** “Access to organizational information systems must be granted according to documented business need and an approved access request. The designated system owner is responsible for approving access consistent with assigned job responsibilities.” The app records the user confirmation/decision supporting this language and flags any unresolved system owner designation.

**Export result:** Six to eight separate editable Word drafts, a policy index, a list of open governance decisions, an optional requirements matrix, and an explicit “Draft — not approved” legend until the company completes its own review process.

# 20. Optional integration with CyberRiskGuardian and a GRC ontology

Build the system as a **standalone application first**, with a documented integration interface. A later connector can read risk registers, assets, control objectives, security maturity, risk appetite, incidents, audit findings, business processes and regulatory mappings from an existing GRC decision-support application or ontology. The policy system should return policy IDs, clauses, mapped controls, owners, revision status, gaps and proposed risk treatment requirements.

For an ontology-backed integration, represent relationships such as:

`Organization -> hasRisk -> RiskScenario`  
`Policy -> governs -> SecurityDomain`  
`PolicyClause -> addresses -> ControlObjective`  
`PolicyClause -> supportedBy -> StandardOrProcedure`  
`Control -> treats -> RiskScenario`  
`PolicyClause -> derivedFrom -> EvidenceOrRequirement`  
`Policy -> ownedBy -> OrganizationalRole`  
`PolicyVersion -> approvedBy -> AuthorizedPerson`  
`RegulatoryRequirement -> appliesTo -> OrganizationalContext (only after confirmation)`

Use stable identifiers and JSON-LD or RDF/OWL adapters where practical. Avoid making an ontology, external risk platform, or live regulatory feed a prerequisite to the MVP. Never let imported risk scores automatically dictate mandatory legal text; retain human judgment and provenance.

# 21. Reporting and future lifecycle functionality

After creation, the system may offer a policy maintenance dashboard: inventory, percentage of policies with assigned owners, age since last review, overdue reviews, unresolved decisions, pending exceptions, missing training/attestation, recent regulatory source updates, newly introduced risks and changes in technology. This dashboard reflects documented state rather than asserting compliance or control effectiveness.

Optional future features include Microsoft Word tracked changes during reimport, collaboration/commenting, approval workflows, publication to intranet, employee acknowledgement, audit evidence requests, policy impact analysis for changes in a risk scenario and AI-based review of policy clarity. Automated reminders require user-configured scheduling and permission checks.

# 22. Delivery package expected from the implementation agent

The Claude development project should produce:

1. A running web application and clearly described local installation/deployment procedure.
2. Database schema/migrations, seed policy catalogue and questionnaire definitions.
3. Secure backend API with OpenAPI documentation.
4. Modular, testable AI prompts and provider abstraction; mock provider for development.
5. Source ingestion and evidence/provenance model.
6. Word templates, DOCX generation code and sample synthetic output documents.
7. Automated tests (unit, integration, security and end-to-end) with sample fixtures.
8. Developer architecture and data model docs; user/admin guides.
9. Known limitations, legal-review reminders, licensed-content constraints, threat model and backlog.
10. A clear demonstration that an organization with no uploaded documents can create a draft EISP and that an organization with documents can produce a more evidence-informed draft.

# 23. Authoritative source and reference register (reviewed October 19, 2026)

These URLs provide primary reference points for building versioned framework/ruleset metadata. They are **not** a substitute for licensed standard texts, jurisdiction-specific legal assessment or a live regulatory service.

| Source | Use in application | URL |
|---|---|---|
| ISO/IEC 27001:2022 | ISMS requirements and overarching governance context | https://committee.iso.org/standard/27001 |
| ISO/IEC 27002:2022 | Security controls and topic-specific policy concepts | https://www.iso.org/standard/75652.html |
| NIST CSF 2.0 | Governance, policies, risk management; GV.PO | https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf |
| NIST SP 800-53 Rev. 5 (Release 5.2.0) | Versioned security/privacy control catalogue | https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final |
| NIST CPRT | Machine-readable control/reference data where licensed/open | https://csrc.nist.gov/projects/cprt/catalog?element=SC-26 |
| CIS Controls v8.1 | Prioritized safeguards and implementation groups | https://www.cisecurity.org/controls/v8-1 |
| CIS policy templates | Example policy topics; license/use terms to be verified | https://www.cisecurity.org/controls/policy-templates |
| Quebec CAI — Law 25 changes | Sector-sensitive Quebec privacy governance rules | https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25 |
| Quebec CAI — private-sector privacy officer | Governance responsibilities for private-sector entities | https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/responsable-protection-renseignements-personnels-entreprise |
| OPC Canada — PIPEDA accountability | Privacy management policies and practices | https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/principles/p_accountability/ |
| OWASP LLM01:2025 | Prompt-injection threat modelling | https://genai.owasp.org/llmrisk/llm01-prompt-injection/ |

# 24. Instructions to Claude: decision priorities

When implementing, optimize first for: **(1) correctness of the organization's profile; (2) trustworthy provenance and legal applicability status; (3) coherent policy hierarchy; (4) editable Word output; (5) user control and transparent review; (6) security and privacy; (7) operational feasibility; (8) feature richness**.

Design the app so its first complete vertical slice works with no prior documents: start -> answer basic questions -> select EISP and several policies -> generate structured drafts -> inspect issues -> export editable DOCX. Then add evidence ingestion and adaptive questioning, rather than building sophisticated agents before the end-to-end flow works.

**Definition of success:** A security professional can use the application to create a realistic, internally consistent and clearly labeled first draft policy framework reflecting company-specific facts and decisions, while retaining full control over all final requirements and approvals.
