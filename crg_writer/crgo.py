"""The CyberRiskGuardian Ontology (CRGO) as the Writer sees it.

Three things live here, and nothing in them computes risk or decides applicability:

1. Control identifiers. Library clauses cite frameworks by identifier ("ISO 27002:2022 5.15",
   "NIST CSF 2.0 PR.AA"); CyberRiskGuardian stores the same controls in CRGO form ("ISO22:5.15",
   "CSF2:PR.AA"). ``crg_ref`` converts one to the other, so a drafted statement lands in ISP management
   already mapped to the controls that CRGO links to risk scenarios.
2. Legal instruments. CRGO 0.10.0 evaluates seven instruments (P-39.1, A-2.1, R-22.1, PIPEDA, OSFI B-13,
   GDPR, C-1.1). Where a Writer candidate is one of them, the CRGO evaluator's state is shown as evidence
   and the Writer's own rule only explains the interview answers behind it. Candidates CRGO does not
   cover (sector rules, contracts, frameworks) stay Writer candidates. Either way, a clause that depends
   on a law is drafted only after a NAMED reviewer records that it applies.
3. The applicability profile. Interview answers that translate directly into CRGO's organisation
   profile terms are offered as a proposal; the person applies it on the Compliance screen's terms.
   Unknown stays unknown: a value never becomes "absent" because the interview did not mention it.

© 2026 Marc-André Léger. CC BY-NC 4.0
"""
from __future__ import annotations

import re

from .engine import Profile

CRGO_RELEASE = "v0.10.0"

# Writer candidate code -> CRGO legal instrument id (crgo-legal)
INSTRUMENT = {"QC-P39.1": "P-39.1", "QC-A2.1": "A-2.1", "CA-PIPEDA": "PIPEDA", "EU-GDPR": "GDPR", "CA-OSFI-B13": "OSFI-B-13"}
CRGO_STATE = {
    "Applicable": {"en": "applicable (CRGO evaluator)", "fr": "applicable (évaluateur CRGO)"},
    "NotApplicable": {"en": "not applicable (CRGO evaluator)", "fr": "non applicable (évaluateur CRGO)"},
    "PotentiallyApplicable": {"en": "potentially applicable — qualified review required (CRGO evaluator)",
                              "fr": "potentiellement applicable — examen par une personne qualifiée requis (évaluateur CRGO)"},
    "Unknown": {"en": "unknown — evidence gap, organizational input required (CRGO evaluator)",
                "fr": "inconnu — lacune de preuve, information de l’organisation requise (évaluateur CRGO)"},
}

_REF = [
    (re.compile(r"^ISO 27002:2022 (\d+\.\d+)$"), "ISO22:{0}"),
    (re.compile(r"^ISO 27001:2022 (\d+(?:\.\d+)?)$"), "ISO27001:{0}"),
    (re.compile(r"^NIST CSF 2\.0 ([A-Z]{2}\.[A-Z]{2}(?:-\d{2})?)$"), "CSF2:{0}"),
    (re.compile(r"^CIS v8\.1 (\d+(?:\.\d+)?)$"), "CIS81:{0}"),
    (re.compile(r"^NIST SP 800-63B$"), "SP800-63B"),
]


def crg_ref(ref: str) -> str:
    """'ISO 27002:2022 5.15' -> 'ISO22:5.15'; unknown forms are returned unchanged."""
    for rx, fmt in _REF:
        m = rx.match(ref.strip())
        if m:
            return fmt.format(*m.groups())
    return ref


def crg_refs(refs) -> list[str]:
    out: list[str] = []
    for r in refs or []:
        x = crg_ref(r)
        if x not in out:
            out.append(x)
    return out


# ---------------------------------------------------------------- applicability profile proposal
_JUR = {"QC": "JurQuebec", "ON": "JurCanadaOtherProvince", "BC": "JurCanadaSimilarProvince", "AB": "JurCanadaSimilarProvince",
        "CA_OTHER": "JurCanadaOtherProvince", "EU": "JurEU", "US": "JurOtherCountry", "UK": "JurOtherCountry", "OTHER": "JurOtherCountry"}
_CANADA = {"QC", "ON", "BC", "AB", "CA_OTHER"}
_ORG = {"private": "OrgEnterprise", "public_listed": "OrgEnterprise", "nonprofit": "OrgEnterprise", "public_sector": "OrgPublicBody"}
_DATA = {"employee": "DataIdentityContact", "customer_pi": "DataIdentityContact", "students": "DataIdentityContact",
         "health": "DataHealth", "financial": "DataFinancial", "payment_card": "DataFinancial"}


def profile_proposal(p: Profile) -> dict:
    """CRGO organisation-profile values implied by interview answers, each with the answer behind it.
    Only additions are proposed; nothing is ever marked complete (that is the person's call)."""
    out: dict[str, list[dict]] = {"orgTypes": [], "establishedIn": [], "offersServicesIn": []}

    def add(key, value, because):
        if value and not any(x["value"] == value for x in out[key]):
            out[key].append({"value": value, "because": because})

    for j in p.value("ORG-05") or []:
        add("establishedIn", _JUR.get(j), "ORG-05")
        if j in _CANADA:
            add("establishedIn", "JurCanada", "ORG-05")
    for j in p.value("ORG-05B") or []:
        add("offersServicesIn", _JUR.get(j), "ORG-05B")
        if j in _CANADA:
            add("offersServicesIn", "JurCanada", "ORG-05B")
    add("orgTypes", _ORG.get(p.value("ORG-06")), "ORG-06")
    if p.value("ORG-06") == "healthcare" or p.value("ORG-02") == "healthcare":
        out.setdefault("note", []).append({"value": "OrgHealthBody", "because": "ORG-06",
                                            "text": {"en": "Health sector: whether the organization is a health body within the meaning of the law needs a qualified person.",
                                                     "fr": "Secteur de la santé : savoir si l’organisation est un organisme de santé au sens de la loi exige une personne qualifiée."}})
    cats = []
    for c in p.value("DATA-01") or []:
        v = _DATA.get(c)
        if v and v not in cats:
            cats.append(v)
    if cats:
        out["activity"] = [{"name": {"en": "Activities stated in the policy interview", "fr": "Activités déclarées à l’entrevue sur les politiques"},
                            "dataCategories": cats, "dataSubjectsIn": [x["value"] for x in out["offersServicesIn"]], "because": "DATA-01"}]
    return out


def crgo_status(code: str, crgo_results: dict | None) -> dict | None:
    """The CRGO evaluator's state for a Writer candidate, when CRGO covers it."""
    inst = INSTRUMENT.get(code)
    if not inst:
        return None
    res = (crgo_results or {}).get("results", {}).get(inst) if crgo_results else None
    return {"instrument": inst, "state": (res or {}).get("state"), "date": (crgo_results or {}).get("date"),
            "source": (crgo_results or {}).get("source"), "release": (crgo_results or {}).get("release"),
            "undetermined": (res or {}).get("undetermined", []), "met": (res or {}).get("met", [])}
