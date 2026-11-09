"""Questionnaire engine: display conditions, progress, and the derived organization profile."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .questions import BY_CODE, QUESTIONS, SECTION_TITLES

ANSWERED = "answered"
NON_ANSWER_STATUSES = {"unknown", "not_applicable", "decide_later"}


@dataclass
class Profile:
    """Read-only view of a project's answers (code -> {value, status, source})."""
    answers: dict[str, dict] = field(default_factory=dict)
    lang: str = "en"

    def status(self, code: str) -> str | None:
        a = self.answers.get(code)
        return a["status"] if a else None

    def value(self, code: str, default=None):
        a = self.answers.get(code)
        if not a or a["status"] != ANSWERED or a["value"] in (None, "", []):
            return default
        return a["value"]

    def answered(self, code: str) -> bool:
        return self.value(code) is not None

    def has(self, code: str, *values) -> bool:
        v = self.value(code)
        if v is None:
            return False
        if isinstance(v, list):
            return any(x in v for x in values)
        return v in values

    def label(self, code: str, lang: str | None = None) -> str | None:
        """Human label for an answer (option labels for select/multi, raw text otherwise)."""
        lang = lang or self.lang
        v = self.value(code)
        if v is None:
            return None
        q = BY_CODE.get(code) or _decision_question(code)
        opts = {o["value"]: o[lang] for o in (q or {}).get("options", [])}
        if isinstance(v, list):
            return ", ".join(opts.get(x, str(x)) for x in v)
        return opts.get(v, str(v))

    # ---- derived facts used by catalogue and drafting
    @property
    def org_name(self) -> str:
        return (self.value("ORG-01B") or self.value("ORG-01") or "").strip()

    @property
    def size_rank(self) -> int:
        bands = ["1-10", "11-50", "51-250", "251-1000", "1001-5000", "5000+"]
        v = self.value("ORG-04")
        return bands.index(v) if v in bands else 2

    @property
    def small(self) -> bool:
        return self.size_rank <= 1

    @property
    def handles_pi(self) -> bool:
        return self.has("DATA-01", "employee", "customer_pi", "health", "students", "payment_card", "financial")

    @property
    def doc_prefix(self) -> str:
        p = self.value("DOC-06")
        if p:
            return re.sub(r"[^A-Za-z0-9]", "", p).upper()[:8] or "ORG"
        words = [w for w in re.split(r"[\s\-]+", self.org_name) if w and w[0].isalnum()]
        stop = {"inc", "inc.", "ltd", "ltée", "llc", "corp", "the", "de", "des", "la", "le", "du", "et", "and", "of"}
        kept = [w for w in words if w.lower().strip(".") not in stop]
        if len(kept) == 1:
            return re.sub(r"[^A-Za-z0-9]", "", kept[0]).upper()[:3] or "ORG"
        initials = "".join(w[0] for w in kept)
        return (re.sub(r"[^A-Za-z0-9]", "", initials).upper() or "ORG")[:6]


_decision_lookup = None


def _decision_question(code: str):
    global _decision_lookup
    if _decision_lookup is None:
        from .catalogue import DECISIONS
        _decision_lookup = {d["code"]: d for d in DECISIONS}
    return _decision_lookup.get(code)


def evaluate(cond: dict | None, profile: Profile) -> bool:
    if not cond:
        return True
    if "all" in cond:
        return all(evaluate(c, profile) for c in cond["all"])
    if "anyof" in cond:
        return any(evaluate(c, profile) for c in cond["anyof"])
    if "not" in cond:
        return not evaluate(cond["not"], profile)
    code = cond["q"]
    if "any" in cond:
        return profile.has(code, *cond["any"])
    if "eq" in cond:
        return profile.value(code) == cond["eq"]
    if "answered" in cond:
        return profile.answered(code) == cond["answered"]
    raise ValueError(f"Unknown condition: {cond}")


def visible_questions(profile: Profile, mode: str) -> list[dict]:
    modes = {"express"} if mode == "express" else {"express", "standard"}
    return [q for q in QUESTIONS if q["mode"] in modes and evaluate(q.get("condition"), profile)]


def progress(profile: Profile, mode: str) -> dict:
    qs = visible_questions(profile, mode)
    done = [q for q in qs if profile.status(q["code"]) is not None]
    required = [q for q in qs if q.get("required")]
    req_done = [q for q in required if profile.status(q["code"]) is not None]
    return {"total": len(qs), "done": len(done), "required": len(required), "required_done": len(req_done),
            "minimum_complete": len(req_done) == len(required)}


def sections_for(profile: Profile, mode: str, lang: str) -> list[dict]:
    """Group visible questions into steps of at most 8 questions (spec §11: 4–8 per step)."""
    out: list[dict] = []
    for sec_key, title in SECTION_TITLES.items():
        qs = [q for q in visible_questions(profile, mode) if q["section"] == sec_key]
        for i in range(0, len(qs), 8):
            chunk = qs[i:i + 8]
            n = len(out) + 1
            suffix = f" ({i // 8 + 1})" if len(qs) > 8 else ""
            out.append({"key": f"{sec_key}-{i // 8}", "section": sec_key, "step": n,
                        "title": title[lang] + suffix, "questions": [q["code"] for q in chunk]})
    return out


def governance_observations(profile: Profile, lang: str) -> list[dict]:
    """Governance patterns from *Introduction to Cybersecurity Governance for Business Technology Management* (v2.51), Chapter 21 (People, organizational design and accountability) detectable from answers.
    These are observations to discuss, never facts written into a policy."""
    t = (lambda en, fr: fr if lang == "fr" else en)
    obs = []
    if profile.value("GOV-01B") == "it":
        obs.append({"code": "GP-IT-OWNS-RISK", "severity": "medium",
                    "text": t("Cyber risk is accepted by IT or security rather than by business owners. Policies will assign risk acceptance to business owners — confirm this decision.",
                              "Le risque cyber est accepté par les TI ou la sécurité plutôt que par les responsables d’affaires. Les politiques attribueront l’acceptation du risque aux responsables d’affaires — confirmez cette décision.")})
    if profile.value("GOV-01B") == "unclear":
        obs.append({"code": "GP-UNCLEAR-RISK", "severity": "high",
                    "text": t("Nobody is clearly accountable for accepting cyber risk. An unmanaged risk is an implicit decision; name the risk-acceptance authority.",
                              "Personne n’est clairement responsable d’accepter le risque cyber. Un risque non géré est une décision implicite; désignez l’autorité d’acceptation.")})
    roles = profile.value("ORG-13") or []
    if profile.answered("ORG-13") and not any(r in roles for r in ("ciso", "security_team", "it_manager", "msp")):
        obs.append({"code": "GP-NO-SECURITY-ROLE", "severity": "high",
                    "text": t("No role currently leads information security. Policies will use a placeholder role until one is designated.",
                              "Aucun rôle ne dirige actuellement la sécurité de l’information. Les politiques utiliseront un rôle à confirmer jusqu’à sa désignation.")})
    if profile.handles_pi and profile.has("ORG-05", "QC") and not profile.has("ORG-13", "privacy_officer") and profile.answered("ORG-13"):
        obs.append({"code": "GP-NO-PRIVACY-OFFICER", "severity": "medium",
                    "text": t("Personal information is held and the organization operates in Quebec, but no privacy officer was listed. Confirm who holds this role with counsel.",
                              "Des renseignements personnels sont détenus et l’organisation exerce au Québec, mais aucun responsable de la protection des renseignements personnels n’a été indiqué. Confirmez qui occupe ce rôle avec un conseiller juridique.")})
    if profile.value("ORG-12") in ("documented", "managed") and profile.value("ORG-08") == "scratch":
        obs.append({"code": "GP-MATURITY-CONFLICT", "severity": "low",
                    "text": t("Maturity was described as documented or managed, yet the project starts from scratch. Check which statement is accurate.",
                              "La maturité a été décrite comme documentée ou gérée, mais le projet part de zéro. Vérifiez quel énoncé est exact.")})
    if profile.has("ORG-13", "ciso") and profile.value("GOV-01B") == "it":
        obs.append({"code": "GP-CISO-SCAPEGOAT", "severity": "low",
                    "text": t("Check that the security lead has authority and budget matching the accountability given.",
                              "Vérifiez que le responsable de la sécurité dispose d’une autorité et d’un budget à la hauteur de la responsabilité confiée.")})
    return obs
