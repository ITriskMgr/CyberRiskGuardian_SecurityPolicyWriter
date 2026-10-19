"""Versioned ruleset of CANDIDATE legal, regulatory, contractual and framework obligations.

Nothing here declares that a law applies. Each rule yields a *candidate* with the conditions observed in
the interview, the conditions that still need confirmation, and a reference URL to verify. Only a named
person can record a decision (applies / not applicable / needs legal review). Spec §5.6, §8, §14.2.
Reference URLs were current at ruleset date and must be re-verified before reliance.
"""
from __future__ import annotations

from .engine import Profile

RULESET_VERSION = "2026.10-1"
RULESET_DATE = "2026-10-19"


def _t(en, fr):
    return {"en": en, "fr": fr}


OBLIGATIONS = [
    {"code": "QC-P39.1", "kind": "law", "jurisdiction": "Quebec",
     "name": _t("Act respecting the protection of personal information in the private sector (CQLR c. P-39.1), as amended by Law 25",
                "Loi sur la protection des renseignements personnels dans le secteur privé (RLRQ c. P-39.1), modifiée par la Loi 25"),
     "url": "https://www.legisquebec.gouv.qc.ca/en/document/cs/P-39.1",
     "url2": "https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25",
     "when": lambda p: p.handles_pi and (p.has("ORG-05", "QC") or p.has("ORG-05B", "QC")) and p.value("ORG-06") not in ("public_sector",),
     "observed": _t("Personal information held; operations or individuals in Quebec; not a public body.",
                    "Renseignements personnels détenus; activités ou personnes au Québec; pas un organisme public."),
     "confirm": _t("Confirm the organization is an “enterprise” under the Act and which activities are covered; confirm the person in charge of the protection of personal information.",
                   "Confirmer que l’organisation est une « entreprise » au sens de la Loi et les activités visées; confirmer la personne responsable de la protection des renseignements personnels."),
     "policies": ["PRIV", "IR", "TPRM", "CLASS", "AI"]},
    {"code": "QC-A2.1", "kind": "law", "jurisdiction": "Quebec",
     "name": _t("Act respecting access to documents held by public bodies and the protection of personal information (CQLR c. A-2.1)",
                "Loi sur l’accès aux documents des organismes publics et sur la protection des renseignements personnels (RLRQ c. A-2.1)"),
     "url": "https://www.legisquebec.gouv.qc.ca/en/document/cs/A-2.1",
     "when": lambda p: p.has("ORG-05", "QC") and p.value("ORG-06") in ("public_sector", "education", "healthcare"),
     "observed": _t("Quebec operations and a public, educational or healthcare status.", "Activités au Québec et statut public, d’enseignement ou de santé."),
     "confirm": _t("Confirm whether the organization is a “public body” within the meaning of the Act.", "Confirmer si l’organisation est un « organisme public » au sens de la Loi."),
     "policies": ["PRIV", "IR", "CLASS"]},
    {"code": "QC-G1.03", "kind": "law", "jurisdiction": "Quebec",
     "name": _t("Act respecting the governance and management of the information resources of public bodies and government enterprises (CQLR c. G-1.03) and the Government directive on information security",
                "Loi sur la gouvernance et la gestion des ressources informationnelles des organismes publics et des entreprises du gouvernement (RLRQ c. G-1.03) et Directive gouvernementale sur la sécurité de l’information"),
     "url": "https://www.legisquebec.gouv.qc.ca/en/document/cs/G-1.03",
     "when": lambda p: p.has("ORG-05", "QC") and p.value("ORG-06") == "public_sector",
     "observed": _t("Quebec public-sector status.", "Statut d’organisme public québécois."),
     "confirm": _t("Confirm coverage by the Act and the current government directive, standards and roles (e.g., organizational information security lead).",
                   "Confirmer l’assujettissement à la Loi et à la directive, aux normes et aux rôles gouvernementaux en vigueur (p. ex. chef organisationnel de la sécurité de l’information)."),
     "policies": ["EISP", "IR", "RISK"]},
    {"code": "CA-PIPEDA", "kind": "law", "jurisdiction": "Canada (federal)",
     "name": _t("Personal Information Protection and Electronic Documents Act (PIPEDA)", "Loi sur la protection des renseignements personnels et les documents électroniques (LPRPDE)"),
     "url": "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/principles/p_accountability/",
     "when": lambda p: p.handles_pi and p.has("ORG-05", "QC", "ON", "BC", "AB", "CA_OTHER") and p.value("ORG-06") in ("private", "public_listed", "other", None),
     "observed": _t("Private-sector organization in Canada holding personal information.", "Organisation du secteur privé au Canada détenant des renseignements personnels."),
     "confirm": _t("Confirm commercial activity, interprovincial or international data flows, and interaction with provincial laws declared substantially similar.",
                   "Confirmer l’activité commerciale, les flux interprovinciaux ou internationaux et l’interaction avec les lois provinciales jugées essentiellement similaires."),
     "policies": ["PRIV", "IR", "TPRM"]},
    {"code": "ON-PHIPA", "kind": "law", "jurisdiction": "Ontario",
     "name": _t("Personal Health Information Protection Act, 2004 (Ontario)", "Loi de 2004 sur la protection des renseignements personnels sur la santé (Ontario)"),
     "url": "https://www.ontario.ca/laws/statute/04p03",
     "when": lambda p: p.has("DATA-01", "health") and p.has("ORG-05", "ON"),
     "observed": _t("Health information and Ontario operations.", "Renseignements de santé et activités en Ontario."),
     "confirm": _t("Confirm health-information-custodian or agent status.", "Confirmer le statut de dépositaire de renseignements sur la santé ou de mandataire."),
     "policies": ["PRIV", "IR", "IAM", "LOG"]},
    {"code": "EU-GDPR", "kind": "law", "jurisdiction": "European Union",
     "name": _t("General Data Protection Regulation (EU) 2016/679", "Règlement général sur la protection des données (UE) 2016/679"),
     "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
     "when": lambda p: p.handles_pi and (p.has("ORG-05", "EU") or p.has("ORG-05B", "EU")),
     "observed": _t("Operations in, or individuals located in, the EU/EEA.", "Activités dans l’UE/EEE ou personnes qui s’y trouvent."),
     "confirm": _t("Confirm establishment in the EU or targeting/monitoring of individuals in the EU (territorial scope).",
                   "Confirmer un établissement dans l’UE ou le ciblage ou le suivi de personnes dans l’UE (champ territorial)."),
     "policies": ["PRIV", "IR", "TPRM"]},
    {"code": "US-HIPAA", "kind": "law", "jurisdiction": "United States",
     "name": _t("HIPAA Privacy and Security Rules (45 CFR Parts 160 and 164)", "Règles de confidentialité et de sécurité HIPAA (45 CFR parties 160 et 164)"),
     "url": "https://www.hhs.gov/hipaa/for-professionals/security/index.html",
     "when": lambda p: p.has("DATA-01", "health") and (p.has("ORG-05", "US") or p.has("ORG-05B", "US")),
     "observed": _t("Health information and a United States presence or clients.", "Renseignements de santé et présence ou clientèle aux États-Unis."),
     "confirm": _t("Confirm covered-entity or business-associate status.", "Confirmer le statut d’entité visée ou d’associé d’affaires."),
     "policies": ["PRIV", "IR", "IAM", "LOG", "TPRM"]},
    {"code": "PCI-DSS", "kind": "contractual_standard", "jurisdiction": "Card brands (contractual)",
     "name": _t("PCI DSS v4.0.1 (Payment Card Industry Data Security Standard)", "PCI DSS v4.0.1 (norme de sécurité des données de l’industrie des cartes de paiement)"),
     "url": "https://www.pcisecuritystandards.org/standards/",
     "when": lambda p: p.has("DATA-01", "payment_card") or p.has("TECH-03", "pos") or p.has("REG-04", "pci"),
     "observed": _t("Payment card data, point-of-sale terminals or PCI selected.", "Données de cartes, terminaux de point de vente ou PCI sélectionnée."),
     "confirm": _t("Confirm whether cardholder data is stored, processed or transmitted, merchant/service-provider level, and scope reduction (e.g., hosted payment page).",
                   "Confirmer si des données de titulaires sont stockées, traitées ou transmises, le niveau de commerçant ou de fournisseur et la réduction de portée (p. ex. page de paiement hébergée)."),
     "policies": ["CLASS", "VULN", "LOG", "IAM", "TPRM"]},
    {"code": "CA-OSFI-B13", "kind": "guideline", "jurisdiction": "Canada (federal financial)",
     "name": _t("OSFI Guideline B-13 — Technology and Cyber Risk Management", "Ligne directrice B-13 du BSIF — Gestion des risques liés à la technologie et au cyberrisque"),
     "url": "https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/technology-cyber-risk-management",
     "when": lambda p: p.has("ORG-02", "financial") and p.value("IND-FIN-01") == "yes",
     "observed": _t("Financial services organization reporting a financial supervisor.", "Organisation de services financiers déclarant un organisme de surveillance financière."),
     "confirm": _t("Confirm federally regulated financial institution status (otherwise consider AMF guidance for Quebec-regulated institutions).",
                   "Confirmer le statut d’institution financière fédérale (sinon, considérer les lignes directrices de l’AMF pour les institutions encadrées au Québec)."),
     "policies": ["EISP", "RISK", "TPRM", "IR", "BACKUP"]},
    {"code": "EU-NIS2", "kind": "law", "jurisdiction": "European Union",
     "name": _t("Directive (EU) 2022/2555 (NIS2) as transposed by member states", "Directive (UE) 2022/2555 (SRI 2) telle que transposée par les États membres"),
     "url": "https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
     "when": lambda p: p.has("ORG-05", "EU") and p.has("ORG-02", "energy_utilities", "healthcare", "it_services", "software_saas", "manufacturing_ot", "financial", "public_sector"),
     "observed": _t("EU operations in a sector that NIS2 may cover.", "Activités dans l’UE dans un secteur que SRI 2 peut viser."),
     "confirm": _t("Confirm sector, size thresholds and national transposition.", "Confirmer le secteur, les seuils de taille et la transposition nationale."),
     "policies": ["EISP", "IR", "TPRM", "RISK"]},
    {"code": "CONTRACT-CLIENT", "kind": "contract", "jurisdiction": "Contract",
     "name": _t("Client contractual security obligations", "Obligations contractuelles de sécurité envers les clients"),
     "url": "",
     "when": lambda p: p.value("REG-05") == "yes" or p.has("ORG-09", "client_assurance"),
     "observed": _t("Client contracts or client assurance were reported.", "Des contrats clients ou des exigences d’assurance client ont été indiqués."),
     "confirm": _t("Upload the contracts or security addenda so each requirement can be traced to a clause.",
                   "Téléversez les contrats ou annexes de sécurité afin de rattacher chaque exigence à une clause."),
     "policies": ["EISP", "TPRM", "IR"]},
    {"code": "FW-ISO27001", "kind": "framework", "jurisdiction": "Framework",
     "name": _t("ISO/IEC 27001:2022 (with Amd 1:2024) — adopted framework", "ISO/IEC 27001:2022 (avec Amd 1:2024) — référentiel adopté"),
     "url": "https://www.iso.org/standard/27001",
     "when": lambda p: p.has("GOV-04", "iso27001") or p.has("REG-04", "iso27001") or p.has("ORG-09", "certification"),
     "observed": _t("ISO/IEC 27001 adoption or certification was indicated.", "L’adoption ou la certification ISO/IEC 27001 a été indiquée."),
     "confirm": _t("Confirm formal adoption and ISMS scope. Mapping a policy to a control is not evidence of conformity.",
                   "Confirmer l’adoption formelle et la portée du SGSI. Associer une politique à une mesure n’est pas une preuve de conformité."),
     "policies": ["EISP"]},
    {"code": "FW-NISTCSF", "kind": "framework", "jurisdiction": "Framework",
     "name": _t("NIST Cybersecurity Framework 2.0 — adopted framework", "NIST Cybersecurity Framework 2.0 — référentiel adopté"),
     "url": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf",
     "when": lambda p: p.has("GOV-04", "nist_csf"),
     "observed": _t("NIST CSF 2.0 adoption was indicated.", "L’adoption du NIST CSF 2.0 a été indiquée."),
     "confirm": _t("Confirm current and target profiles. GV.PO-01 and GV.PO-02 concern establishing and updating policy.",
                   "Confirmer les profils actuel et cible. GV.PO-01 et GV.PO-02 portent sur l’établissement et la mise à jour des politiques."),
     "policies": ["EISP"]},
]

BY_CODE = {ob["code"]: ob for ob in OBLIGATIONS}
KIND_LABEL = {
    "law": _t("Legislation / regulation", "Législation / réglementation"),
    "guideline": _t("Regulatory guideline", "Ligne directrice réglementaire"),
    "contractual_standard": _t("Contractual industry standard", "Norme sectorielle contractuelle"),
    "contract": _t("Contract", "Contrat"),
    "framework": _t("Framework (only if adopted)", "Référentiel (seulement s’il est adopté)"),
}


def candidates(p: Profile, lang: str, decisions: dict[str, dict], crgo_results: dict | None = None) -> list[dict]:
    """Candidates for the reviewer. For instruments CRGO evaluates, the CRGO evaluator's state (from
    Compliance → Legal applicability) is attached as evidence; it never replaces the named reviewer."""
    from .crgo import CRGO_STATE, crgo_status
    out = []
    for ob in OBLIGATIONS:
        try:
            hit = bool(ob["when"](p))
        except Exception:
            hit = False
        dec = decisions.get(ob["code"])
        cs = crgo_status(ob["code"], crgo_results)
        crgo_hit = bool(cs and cs["state"] in ("Applicable", "PotentiallyApplicable"))
        if not hit and not dec and not crgo_hit:
            continue
        out.append({
            "code": ob["code"], "kind": ob["kind"], "kind_label": KIND_LABEL[ob["kind"]][lang],
            "jurisdiction": ob["jurisdiction"], "name": ob["name"][lang], "url": ob["url"], "url2": ob.get("url2", ""),
            "observed": ob["observed"][lang], "confirm": ob["confirm"][lang], "policies": ob["policies"],
            "triggered": hit or crgo_hit, "writer_rule": hit,
            "crgo": cs, "crgo_label": CRGO_STATE[cs["state"]][lang] if cs and cs.get("state") in CRGO_STATE else None,
            "suggested": "applies" if cs and cs.get("state") == "Applicable" else
                         "needs_legal_review" if cs and cs.get("state") == "PotentiallyApplicable" else None,
            "status": dec["status"] if dec else "candidate",
            "decision": dec,
            "verification": ("Not verified — reviewer confirmation required" if lang == "en"
                             else "Non vérifié — confirmation d’un réviseur requise") if not dec or dec["status"] != "applies" else "",
            "ruleset_version": RULESET_VERSION,
        })
    return out


def confirmed_codes(decisions: dict[str, dict]) -> set[str]:
    return {c for c, d in decisions.items() if d["status"] == "applies"}
