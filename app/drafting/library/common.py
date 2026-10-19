"""Clause-library primitives and the sections shared by every topic-specific policy.

Clause text tokens (resolved by app/drafting/composer.py):
  {org} {sec} {owner} {approver} {privacy} {committee} {review} {class_levels} {class_top} {parent_title}
  {exc_ref}  reference to the exception mechanism (RISK policy if selected, else EISP section)
Typed placeholders allowed in text (spec §9.4): [ROLE: …] [DECISION: …] [VALUE: …] [DATE: …]
  [SOURCE: …] [APPROVER: …] [TECHNICAL_DETAIL: …]

A clause may depend on a decision ("by") and provide one text per decision value ("variants") plus a
"_none" variant containing a [DECISION: …] placeholder used while the decision is open.
"""
from __future__ import annotations


def C(cid, en=None, fr=None, mod="must", src="framework", refs=(), inputs=(), when=None, by=None,
      variants=None, legal=False, gap=None, obligation=None):
    """Define a clause.
    src: framework (good-practice recommendation) | answer (states a company fact) | decision (encodes a
         company decision) | obligation (only included when the obligation is confirmed as applicable)
    gap: (question_code, values_meaning_gap, {en, fr} description) — implementation-gap detector
    """
    return {"id": cid, "text": {"en": en, "fr": fr} if en else None, "modality": mod, "src": src, "refs": list(refs),
            "inputs": list(inputs), "when": when, "by": by, "variants": variants, "legal": legal, "gap": gap,
            "obligation": obligation}


def V(en, fr):
    return {"en": en, "fr": fr}


def S(sid, en, fr, clauses, when=None):
    return {"id": sid, "title": {"en": en, "fr": fr}, "clauses": clauses, "when": when}


def topic_frame(purpose: list, scope_extra: list, roles: list, requirements: list, refs=()) -> list:
    """Assemble the standard topic-policy structure (spec §9.3) around policy-specific content."""
    return [
        S("SEC-PURPOSE", "Purpose", "Objet", purpose),
        S("SEC-SCOPE", "Scope and applicability", "Portée et application", [
            C("SC01", "This policy applies to all employees, contractors, consultants, temporary staff and other persons who access {org}’s information or information systems, wherever they work.",
              "La présente politique s’applique à tous les employés, contractuels, consultants, personnes temporaires et autres personnes qui accèdent à l’information ou aux systèmes d’information de {org}, où qu’elles travaillent.",
              mod="info"),
            C("SC02", "It covers information in all forms and all systems owned, leased, operated or used on behalf of {org}, including cloud services and systems operated by suppliers.",
              "Elle vise l’information sous toutes ses formes et tous les systèmes possédés, loués, exploités ou utilisés pour le compte de {org}, y compris les services infonuagiques et les systèmes exploités par des fournisseurs.",
              mod="info"),
            *scope_extra,
        ]),
        S("SEC-AUTHORITY", "Authority and related documents", "Autorité et documents connexes", [
            C("AU01", "This policy is issued under the {parent_title}, which prevails in case of inconsistency. Detailed parameters may be set in standards and procedures approved under this policy.",
              "La présente politique est adoptée en vertu de la {parent_title}, qui prévaut en cas d’incohérence. Des paramètres détaillés peuvent être fixés dans des normes et procédures approuvées en vertu de la présente politique.",
              mod="info"),
        ]),
        S("SEC-ROLES", "Roles and responsibilities", "Rôles et responsabilités", roles),
        *requirements,
        S("SEC-EXCEPTIONS", "Exceptions", "Dérogations", [
            C("EX01", "Any departure from this policy requires an exception approved in advance through {exc_ref}. An exception states the requirement not met, the reason, its duration, the compensating controls and the residual risk.",
              "Tout écart à la présente politique exige une dérogation approuvée au préalable selon {exc_ref}. La dérogation précise l’exigence non respectée, la raison, sa durée, les mesures compensatoires et le risque résiduel.",
              refs=["ISO 27002:2022 5.36", "NIST CSF 2.0 GV.RM"]),
            C("EX02", "An exception cannot set aside a legal, regulatory or contractual obligation.",
              "Une dérogation ne peut écarter une obligation légale, réglementaire ou contractuelle."),
        ]),
        S("SEC-COMPLIANCE", "Compliance monitoring and non-conformance", "Suivi de la conformité et non-conformité", [
            C("CM01", "{owner} monitors the application of this policy and reports significant non-conformities and trends to {committee}.",
              "{owner} assure le suivi de l’application de la présente politique et signale les non-conformités importantes et les tendances à {committee}.",
              refs=["ISO 27002:2022 5.36", "NIST CSF 2.0 GV.OV"]),
            C("CM02", "Non-compliance may lead to the withdrawal of access and to administrative or disciplinary measures proportionate to its seriousness, in accordance with applicable employment rules and contracts.",
              "Le non-respect peut entraîner le retrait des accès et des mesures administratives ou disciplinaires proportionnées à sa gravité, conformément aux règles d’emploi et aux contrats applicables.",
              refs=["ISO 27002:2022 6.4"], legal=True),
            C("CM03", "Having this policy is not evidence that its requirements are met; compliance is demonstrated by evidence that controls operate effectively.",
              "L’existence de la présente politique ne prouve pas que ses exigences sont respectées; la conformité se démontre par des preuves que les mesures fonctionnent efficacement.",
              mod="info"),
        ]),
        S("SEC-REVIEW", "Review", "Révision", [
            C("RV01", "This policy is reviewed {review} and whenever a significant change occurs, such as a new legal requirement, a major incident, a significant technology or organizational change, or a new use of artificial intelligence.",
              "La présente politique est révisée {review} et lors de tout changement important, notamment une nouvelle exigence légale, un incident majeur, un changement technologique ou organisationnel important ou une nouvelle utilisation de l’intelligence artificielle.",
              src="answer", inputs=["GOV-10"], refs=["ISO 27002:2022 5.1", "NIST CSF 2.0 GV.PO-02"]),
        ]),
    ]
