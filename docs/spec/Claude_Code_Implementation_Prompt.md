# Claude Code — Implementation Prompt

## Project: Information Security Policy Builder

You are a senior full-stack engineer, cybersecurity governance specialist, privacy-by-design architect, and document-automation engineer. I want you to **build a working application**, not merely propose an architecture.

### 1. Authoritative project specification

Read the attached file **`Information_Security_Policy_Builder_Requirements.md`** from beginning to end and treat it as the primary functional and quality specification. The business objective is to develop a secure, guided, AI-assisted web application that interviews an organization, understands its industry and operations, optionally ingests existing documents, recommends a policy hierarchy, drafts organization-specific information security policies, permits human review, and exports professionally formatted **editable Microsoft Word `.docx` files**.

Key priorities: organization-specific rather than generic drafting; accurate source and legal-status distinctions; a coherent enterprise-to-technical document hierarchy; practical policy wording; explicit human decisions; traceability; high-quality Word output; secure handling of uploads; and an end-to-end vertical slice early in development.

### 2. Working instructions

1. Inspect the current repository and summarize what exists. If it is empty, initialize an appropriate project structure. Reuse relevant existing code and conventions when available.
2. Produce a concise architectural plan, repository layout, data model summary, and phased task list before coding. State assumptions clearly. Do not stall on minor ambiguities: choose reasonable defaults and document them.
3. Build **working, testable code** in small increments. For each increment, add or update tests, instructions to run it, and a short summary of files changed and remaining risks.
4. Do not claim a feature is complete without demonstrating it using tests or a reproducible manual verification path.
5. Use modular interfaces for AI provider, document storage, extraction, legal/ruleset sources and DOCX templates. Make provider/model names configurable.
6. Avoid external paid dependencies in the demo path. Supply a mock AI provider so the application starts and automated tests run without an Anthropic API key. Enable actual Claude drafting when a server-side API key is configured.
7. Never put API secrets in frontend source. Do not silently transmit confidential input documents to external services.
8. Treat uploaded files and retrieved excerpts as **untrusted data**, not instructions. Design for prompt-injection resistance, authorization and tenant isolation.
9. Never automatically assert that a regulation applies or that a policy proves compliance. Require human confirmation of legal applicability and material normative decisions.
10. All generated documents must be visibly **DRAFT**, remain editable in Word, and contain an organization-specific title, policy ID, owner/approver fields, version, date controls, structured headings and references.

### 3. Start with a minimum working product

Implement an end-to-end path **before** building advanced ontology, coauthoring, approval or regulatory-monitoring systems:

- Create an organization/project.
- Answer approximately 12–15 basic questions about the company, industry, operations, size, jurisdictions, data, cloud environment, security responsibilities and policy objectives.
- Optionally upload at least DOCX, text-based PDF and TXT files and inspect extracted information.
- Show an organization profile that the user can correct.
- Recommend an Enterprise Information Security Policy and an initial, selectable group of topic policies.
- Ask short follow-up questions where necessary for meaningful policy requirements.
- Generate a structured outline and draft for the EISP and at least five topic policies.
- Display unsupported facts, open decisions, role/approval placeholders, and any identified inconsistencies.
- Export one policy to `.docx` and selected policies as a ZIP collection of `.docx` files.
- Reopen a saved project and regenerate a new draft revision after a changed answer.

Implement this with strong boundaries and schemas, so it can grow into the complete specification without major rewrites.

### 4. Suggested architecture, subject to repo inspection

- Web client: Next.js, TypeScript, React with accessible forms and i18n infrastructure.
- Backend: Python FastAPI, Pydantic validation, SQLAlchemy and Alembic migrations.
- Database: PostgreSQL; a lightweight SQLite development/test variant is acceptable if supported by the ORM.
- Document processing: safe file extraction, source offsets/locators, confirmation of facts.
- AI: backend-side Anthropic Claude adapter with a mock adapter for offline tests.
- Word output: `python-docx` and optionally low-level OOXML for fields; keep structured content separate from renderer.
- Local development: Docker Compose or well-documented native installation; `.env.example`; fixtures and smoke tests.

Choose a less complex implementation when it accelerates a usable vertical slice without compromising security or core data correctness. Document the reasons for major deviations.

### 5. Essential business logic

**Questionnaire:** stable question IDs, conditional branches, save/resume, explicit unknown/not-applicable, industry-specific follow-ups, and evidence-prefilled answers that the user can confirm. Support Express and Standard paths, expanding to Comprehensive later.

**Policy architecture:** enterprise policy, topic-specific policies, standards, procedures and guidelines as distinct artifact types. A small organization may consolidate policies while larger entities use a fuller hierarchy. Let users select what to generate. Enforce parent-child references and shared definitions.

**Evidence and applicability:** distinguish confirmed company facts, contractual obligations, candidate legal requirements, framework recommendations and AI suggestions. Preserve page/section/source provenance. Do not use a standard's guidance as proof of statutory obligation or operational implementation.

**Drafting:** outline first, then validated section-level clauses with stable IDs and a consistency pass. The system should not invent implemented controls, personnel, legal citations, security technology or approved decisions. Missing material decisions must be flagged and written as explicit placeholders rather than fabricated specifics.

**Word export:** native/editable `.docx` with document control tables, heading styles, version and draft status, and a consistent numbering scheme. Validate exported files by reopening them programmatically and, when a renderer is available, visually checking a sample set.

### 6. Data and API requirements

Use the full specification for entity design. At minimum store Organizations, Projects, Questionnaire Answers, Source Documents, Evidence Segments, Confirmed Facts, Candidate Obligations and Applicability Decisions, Policy Templates, Policy Documents, Policy Versions, Clauses, Source Links, Issues, Exports and Audit Events. Scope every relevant query and cache entry by tenant/project. Expose an authenticated API for the wizard, uploads, facts, policy selection, generation, review and exports.

Structured JSON is the source of truth for policy bodies. A `.docx` file is a **rendered export**, not the only stored policy representation. Use versioned schemas and migrations. Log model ID, prompt template version and generation timestamp without indiscriminately logging confidential source text.

### 7. Verification scenarios

Use synthetic test companies: (1) Quebec-based small software provider with cloud services, (2) medium-sized food manufacturer with an OT environment, (3) healthcare services organization, (4) education/research institution. Test that policy selection and questions vary by context, contradictory documents are surfaced, unsupported legal claims are not marked verified, and all Word files remain editable. Include negative tests for malicious upload instructions and cross-tenant resource access.

### 8. Phased implementation and checkpoints

**Checkpoint A:** repository inspection, ADR and live app skeleton.  
**Checkpoint B:** working organization/project model and guided interview with persistence.  
**Checkpoint C:** document ingestion and factual confirmation with provenance.  
**Checkpoint D:** policy library, applicability candidate logic and user selection.  
**Checkpoint E:** outline and document-generation pipeline with a mock model and then the real Claude adapter.  
**Checkpoint F:** professionally formatted Word export, ZIP package and regression tests.  
**Checkpoint G:** document review, issue tracking, versioning and role-based permissions.  
**Checkpoint H:** production hardening, bilingual generation, additional catalog items and operational documentation.

At each checkpoint, show exactly what runs now, what commands I can execute, which tests pass, what remains incomplete and what you propose to build next. Avoid placeholder buttons, mock screens that are falsely presented as working, and hidden infrastructure requirements.

### 9. Your immediate action

Read the specification, inspect the repository, propose the **minimal coherent vertical slice**, and then start implementing it. Begin with **Checkpoint A and B**, including complete code, tests and setup instructions. Do not stop at a high-level answer. If no repository is available in the current environment, first create the project scaffolding and the implementation plan in files that can be copied into a repository.

### 10. Definition of done for the first MVP

A user can open the application, create a fictional organization, answer the basic interview, optionally upload supporting documents, choose an enterprise policy plus five topic policies, generate organization-specific **draft** policies with a traceable open-decisions list, and export Word documents that open in Microsoft Word and can be edited. No material company fact is invented, no legal requirement is falsely presented as verified, project state survives reload, and core unit/integration/end-to-end tests are present.
