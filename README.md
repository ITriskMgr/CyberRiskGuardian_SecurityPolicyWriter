# CyberRiskGuardian Security Policy Writer

**The policy-writing module of [CyberRiskGuardian](https://github.com/ITriskMgr/CyberRiskGuardian_ThreatIntel).**
It interviews the organization, reads its documents, takes legal applicability from the CyberRiskGuardian
Ontology (CRGO), and writes the enterprise information security policy, topic-specific policies, standards and
procedures — in **English, French or both**. CyberRiskGuardian's **ISP management** then manages them: review,
approval frozen with a SHA-256 hash, publication, assignments, acknowledgements and exceptions.

**The Writer writes; CyberRiskGuardian manages.**

> **Beta 0.1.0**, shipped in CyberRiskGuardian Desktop **1.7.0 Beta** (Governance → Security Policy Writer).
> Drafts are not legal advice and are not in force until the organization's authorized people approve and
> publish them. A control reference shows the topic a statement addresses; it is never evidence of compliance.

*Version française plus bas.*

## What it does (in CyberRiskGuardian)

| Step | What happens |
|---|---|
| Start | Document languages (EN, FR, both with the same statement identifiers); Express (≈ 22 questions) or Standard (≈ 59) interview. **Propose answers from the profile and the documents** reads the workspace's organization profile, crown jewels and context documents. |
| Interview | Company, sector, size, jurisdictions, data, technology, governance roles; industry branches. Each answer shows its source: you, a document, the organization profile, or an accepted default. |
| Documents & facts | Facts proposed from the documents with their **quote and locator** (document, page, paragraph); conflicts between documents; passages that look like AI instructions set aside; **OCR of scanned PDFs and images on the computer** (Tesseract). Also available when a workspace is created from documents. |
| Legal applicability | Candidate laws and frameworks. For the seven instruments CRGO evaluates (P-39.1, A-2.1, R-22.1, PIPEDA, OSFI B-13, GDPR, C-1.1) the CRGO evaluator's state is shown as evidence; interview answers can be added to the CRGO profile. **A named reviewer decides**; law-dependent clauses wait for that decision. |
| Library | 28 documents (enterprise policy, 19 topic policies, 4 standards, 4 procedures) with priority, reasons, and the **risk scenarios** each addresses through CRGO control identifiers — in the workspace's register and in the CRGO library. |
| Decisions | 44 decisions with suggestions. **Accept all suggestions** (globally or per document) fills only unanswered decisions, records each as *default accepted by X on date*, and leaves legal-review and no-suggestion decisions open, listed. |
| Generate drafts | Creates or refreshes **ISP management drafts**: purpose and scope, a clause per section, a statement per requirement with modality (*must*, *must not*, *should*, *may*) and CRGO control refs; policy families per topic. Only drafts change; frozen versions never do; edits made after generation are kept. Bilingual quality checks; optional AI rewording validated against placeholders, numbers, modal verbs and length. |
| Word export & re-import | Native .docx of any ISP policy (document control, contents, numbered statements, open decisions, traceability). Re-import matches statements by hidden bookmarks (or numbers), shows word-level changes and modality changes, applies only accepted changes, to the draft. |

## This repository

| Path | What it is |
|---|---|
| `crg_writer/` | The engine, Python standard library only: questionnaire, catalogue, 606 bilingual clause definitions, composer, CRGO mapping, ISP mapping, quality checks, evidence and fact extraction, OCR, Word writer and reader, re-import. `api.handle(op, body)` is what the desktop helper calls. |
| `tests/` | `python -m pytest tests -q` (python-docx and Pillow are optional cross-checks; Tesseract and LibreOffice tests run when installed). |
| `tools/sync_to_desktop.py` | Copies the engine into a CyberRiskGuardian Desktop folder. |
| `tools/make_samples.py`, `samples/` | Word drafts for the fictional Northstar company. |
| `docs/` | Architecture decisions, threat model, original specification. |

The previous standalone application (*CyberRiskGuardian Policy Builder* 0.2.0, FastAPI) is preserved at the
branch `legacy/policy-builder-0.2.0`; it is retired in favour of the integrated Writer.

## Licence

© 2026 Marc-André Léger. [CC BY-NC 4.0](LICENSE.md) under the CyberRiskGuardian licensing policy: students and
non-profits free; colleges and universities as institutions need an educational licence; any commercial use
needs a separate licence.

---

# CyberRiskGuardian Security Policy Writer (français)

**Le module de rédaction de politiques de CyberRiskGuardian.** Il interroge l'organisation, lit ses documents,
tire l'applicabilité juridique de l'ontologie CyberRiskGuardian (CRGO) et rédige la politique d'entreprise de
sécurité de l'information, les politiques thématiques, les normes et les procédures — en **anglais, en
français ou dans les deux langues**. La **gestion des PSI** de CyberRiskGuardian les gère ensuite : révision,
approbation figée par une empreinte SHA-256, publication, affectations, prises de connaissance et dérogations.
**Le rédacteur rédige; CyberRiskGuardian gère.**

> **Bêta 0.1.0**, livrée dans CyberRiskGuardian Desktop **1.7.0 bêta** (Gouvernance → Rédacteur de politiques de
> sécurité). Les brouillons ne constituent pas un avis juridique et ne sont pas en vigueur tant que les personnes
> autorisées de l'organisation ne les ont pas approuvés et publiés.

Étapes : Départ · Entrevue · Documents et faits (citations, conflits, ROC sur l'ordinateur) · Applicabilité
juridique (évaluateur CRGO comme preuve, décision d'un réviseur nommé) · Bibliothèque (28 documents, scénarios de
risque liés par les mesures CRGO) · Décisions (**Accepter toutes les suggestions**, consignées comme valeurs par
défaut acceptées) · Générer les brouillons (brouillons de la gestion des PSI; seuls les brouillons changent; les
modifications sont conservées) · Exportation et réimportation Word.

Ce dépôt contient le moteur (`crg_writer/`, bibliothèque standard Python seulement), ses tests et ses outils.
L'ancienne application autonome (*Policy Builder* 0.2.0) est conservée dans la branche `legacy/policy-builder-0.2.0`.
