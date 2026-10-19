"""Deterministic policy composer: profile + decisions + confirmed obligations -> structured policy body.

The composer never invents organizational facts. Every token is resolved from an answer or a decision,
or becomes a typed placeholder that is inventoried as an open decision (spec §9.2, §9.4).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .catalogue import BY_CODE as CAT, DECISIONS, LEVELS
from .rulesets import BY_CODE as OBL
from .library import LIBRARY, LIBRARY_VERSION
from .engine import Profile
from .questions import BY_CODE as QBY

COMPOSER_VERSION = "composer-1.0"
DEC_BY = {d["code"]: d for d in DECISIONS}

PH_RE = re.compile(r"\[(DECISION|DÉCISION|ROLE|RÔLE|VALUE|VALEUR|DATE|SOURCE|APPROVER|APPROBATEUR|TECHNICAL_DETAIL|DÉTAIL_TECHNIQUE)\s*:\s*([^\]]+)\]")
PH_TYPE = {"DÉCISION": "DECISION", "RÔLE": "ROLE", "VALEUR": "VALUE", "APPROBATEUR": "APPROVER", "DÉTAIL_TECHNIQUE": "TECHNICAL_DETAIL"}
PH_SEVERITY = {"DECISION": "high", "APPROVER": "high", "ROLE": "high", "VALUE": "medium", "TECHNICAL_DETAIL": "medium",
               "SOURCE": "medium", "DATE": "low"}
TOKEN_RE = re.compile(r"\{([A-Za-z_]+(?::[A-Z0-9\-]+)?)\}")

UNBOUNDED = ["as soon as possible", "regularly", "periodically", "appropriate security", "appropriate measures",
             "strong encryption", "adequate", "reasonable measures", "dès que possible", "régulièrement",
             "périodiquement", "sécurité appropriée", "mesures appropriées", "chiffrement fort", "adéquat"]

CROSS_REFS = {  # phrase -> policy code it refers to
    "artificial intelligence use policy": "AI", "politique d’utilisation de l’intelligence artificielle": "AI",
    "remote work and mobile device policy": "REMOTE", "politique de télétravail et d’appareils mobiles": "REMOTE",
    "third-party security policy": "TPRM", "politique de sécurité des tiers": "TPRM",
    "identity and access management policy": "IAM", "politique de gestion des identités et des accès": "IAM",
    "incident management policy": "IR", "politique de gestion des incidents": "IR",
    "acceptable use rules": "AUP", "règles d’utilisation acceptable": "AUP",
}

ROLE_WORDS_FR_M = ("conseil", "comité", "directeur", "président", "chef", "responsable", "gestionnaire", "vice",
                   "dirigeant", "premier", "bureau", "service", "secrétaire", "coordonnateur", "conseiller")
ROLE_WORDS_FR_F = ("direction", "présidence", "haute direction", "équipe", "fonction", "personne", "division", "vice-présidence")


def article(value: str, lang: str) -> str:
    """Add a definite article to a role or body name when it reads as a common noun."""
    v = value.strip()
    if not v or v.startswith("[") or "," in v:
        return v
    low = v.lower()
    if lang == "en":
        if low.startswith(("the ", "our ", "a ", "an ")):
            return v
        return "the " + v
    if low.startswith(("le ", "la ", "les ", "l’", "l'")):
        return v
    if low[0] in "aeéèêiîoôuh":
        return "l’" + v
    if low.startswith(ROLE_WORDS_FR_F):
        return "la " + v
    if low.startswith(ROLE_WORDS_FR_M):
        return "le " + v
    return v


def join_list(items: list[str], lang: str) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    conj = " and " if lang == "en" else " et "
    return ", ".join(items[:-1]) + conj + items[-1]


def T(lang, en, fr):
    return fr if lang == "fr" else en


@dataclass
class Context:
    profile: Profile
    lang: str
    selected: list[str]                      # catalogue codes selected for this project
    obligations: dict[str, dict]             # code -> decision dict {status,...}
    candidate_codes: set[str]                # obligations currently triggered as candidates
    version_no: int = 1
    assumptions: list[dict] = field(default_factory=list)
    inputs_used: set[str] = field(default_factory=set)

    @property
    def confirmed(self) -> set[str]:
        return {c for c, d in self.obligations.items() if d.get("status") == "applies"}


class Resolver:
    def __init__(self, ctx: Context):
        self.ctx, self.p, self.lang = ctx, ctx.profile, ctx.lang

    def t(self, en, fr):
        return T(self.lang, en, fr)

    # ---- named tokens
    def org(self):
        return self.p.org_name or self.t("[VALUE: organization name]", "[VALEUR : nom de l’organisation]")

    def sec(self):
        p = self.p
        if p.answered("ORG-13B"):
            return article(p.value("ORG-13B"), self.lang)
        if p.has("ORG-13", "ciso"):
            return self.t("the Chief Information Security Officer", "le chef de la sécurité de l’information")
        if p.has("ORG-13", "security_team"):
            return self.t("the head of information security", "le responsable de la sécurité de l’information")
        if p.has("ORG-13", "it_manager"):
            return self.t("the IT Manager", "le gestionnaire des TI")
        return self.t("[ROLE: person accountable for information security — CONFIRM]",
                      "[RÔLE : personne responsable de la sécurité de l’information — À CONFIRMER]")

    def owner(self):
        if self._code == "EISP" and self.p.answered("ORG-07"):
            return article(self.p.value("ORG-07"), self.lang)
        return self.sec()

    def approver(self):
        if self.p.answered("ORG-07B"):
            return article(self.p.value("ORG-07B"), self.lang)
        return self.t("[APPROVER: authority that approves the enterprise policy]",
                      "[APPROBATEUR : autorité qui approuve la politique d’entreprise]")

    def committee(self):
        v = self.p.value("DEC-EISP-COMMITTEE")
        if v == "yes":
            name = self.p.value("DEC-EISP-COMMITTEE-NAME")
            return article(name, self.lang) if name else self.t("the security governance committee", "le comité de gouvernance de la sécurité")
        if v == "no":
            return self.t("the executive team", "l’équipe de direction")
        return self.t("[DECISION: security governance committee or body]", "[DÉCISION : comité ou instance de gouvernance de la sécurité]")

    def topic_approver(self):
        v = self.p.value("DEC-EISP-COMMITTEE")
        if v in ("yes", "no"):
            return self.committee()
        return self.t("[DECISION: authority that approves topic-specific policies]", "[DÉCISION : autorité qui approuve les politiques thématiques]")

    def privacy(self):
        if self.p.answered("DATA-08"):
            return article(self.p.value("DATA-08"), self.lang)
        if self.p.has("ORG-13", "privacy_officer"):
            return self.t("the person in charge of the protection of personal information",
                          "la personne responsable de la protection des renseignements personnels")
        return self.t("[ROLE: person in charge of the protection of personal information]",
                      "[RÔLE : personne responsable de la protection des renseignements personnels]")

    def review(self):
        v = self.p.value("GOV-10")
        if v:
            return self.t(f"every {v} months", f"tous les {v} mois")
        return self.t("[DECISION: policy review cycle]", "[DÉCISION : cycle de révision des politiques]")

    def levels(self) -> list[str]:
        raw = self.p.value("DATA-02B")
        if raw:
            lv = [x.strip() for x in re.split(r"[,;/]|\s+>\s+", raw) if x.strip()]
            if len(lv) >= 2:
                return lv
        self.assume("CLASS-DEFAULT", self.t(
            "No classification scheme was provided; the recommended four-level scheme (Public, Internal, Confidential, Restricted) is used and must be confirmed.",
            "Aucun schéma de classification n’a été fourni; le schéma recommandé à quatre niveaux (Public, Interne, Confidentiel, Restreint) est utilisé et doit être confirmé."))
        return self.t("Public|Internal|Confidential|Restricted", "Public|Interne|Confidentiel|Restreint").split("|")

    def class_levels(self):
        return join_list(self.levels(), self.lang)

    def class_top(self):
        return self.levels()[-1]

    def parent_title(self):
        parent = CAT[self._code]["parent"] if self._code in CAT else "EISP"
        return CAT[parent or "EISP"]["title"][self.lang]

    def exc_ref(self):
        if "RISK" in self.ctx.selected:
            return self.t("the Cybersecurity Risk Management and Exceptions Policy",
                          "la Politique de gestion des risques de cybersécurité et des dérogations")
        return self.t("the exception process set out in the Enterprise Information Security Policy",
                      "le processus de dérogation prévu à la Politique de sécurité de l’information de l’entreprise")

    def risk_policy(self):
        if "RISK" in self.ctx.selected:
            return CAT["RISK"]["title"][self.lang]
        return self.t("[DECISION: document that sets detailed risk and exception rules]",
                      "[DÉCISION : document qui fixe les règles détaillées sur les risques et les dérogations]")

    def crown_jewels(self):
        v = self.p.value("ORG-14")
        return v.strip().rstrip(".") if v else self.t("[VALUE: critical services and assets]", "[VALEUR : services et actifs essentiels]")

    def tech_env(self):
        lbl = self.p.label("TECH-01", self.lang)
        return lbl if lbl else self.t("[VALUE: technology environments]", "[VALEUR : environnements technologiques]")

    def idp(self):
        return self.p.value("TECH-04B") or ""

    def pi_categories(self):
        pi = [c for c in (self.p.value("DATA-01") or []) if c in ("employee", "customer_pi", "health", "financial", "students", "payment_card", "research")]
        opts = {o["value"]: o[self.lang] for o in QBY["DATA-01"]["options"]}
        return join_list([opts[c].lower() if self.lang == "fr" else opts[c][0].lower() + opts[c][1:] for c in pi], self.lang) or \
            self.t("[VALUE: categories of personal information]", "[VALEUR : catégories de renseignements personnels]")

    def decision_value(self, code):
        lbl = self.p.label(code, self.lang)
        if lbl:
            return lbl[0].lower() + lbl[1:] if lbl[:1].isupper() and not lbl[:2].isupper() else lbl
        d = DEC_BY.get(code)
        what = d["label"][self.lang] if d else code
        return self.t(f"[DECISION: {what}]", f"[DÉCISION : {what}]")

    def assume(self, key, text):
        if not any(a["key"] == key for a in self.ctx.assumptions):
            self.ctx.assumptions.append({"key": key, "text": text})

    # ---- resolution
    _code = ""
    _token_inputs = {"org": ["ORG-01", "ORG-01B"], "sec": ["ORG-13", "ORG-13B"], "approver": ["ORG-07B"],
                     "committee": ["DEC-EISP-COMMITTEE", "DEC-EISP-COMMITTEE-NAME"], "privacy": ["DATA-08", "ORG-13"],
                     "review": ["GOV-10"], "class_levels": ["DATA-02B"], "class_top": ["DATA-02B"], "owner": ["ORG-07"],
                     "crown_jewels": ["ORG-14"], "tech_env": ["TECH-01"], "idp": ["TECH-04B"], "pi_categories": ["DATA-01"],
                     "topic_approver": ["DEC-EISP-COMMITTEE"]}

    def resolve(self, text: str, code: str) -> tuple[str, list[str]]:
        self._code = code
        used: list[str] = []

        def rep(m):
            tok = m.group(1)
            if tok.startswith("p:"):
                dcode = tok[2:]
                used.append(dcode)
                return self.decision_value(dcode)
            key = tok[0].lower() + tok[1:]
            fn = getattr(self, key, None)
            if fn is None:
                return m.group(0)
            used.extend(self._token_inputs.get(key, []))
            val = fn()
            if tok[0].isupper() and val:
                val = val[0].upper() + val[1:]
            return val

        out = TOKEN_RE.sub(rep, text)
        out = tidy(out, self.lang)
        return out, used


def tidy(s: str, lang: str) -> str:
    if lang == "fr":
        for a, b in ((" à le ", " au "), (" à les ", " aux "), (" de le ", " du "), (" de les ", " des "),
                     ("(à le ", "(au "), (" À le ", " Au ")):
            s = s.replace(a, b)
    else:
        s = s.replace(" the the ", " the ")
    s = re.sub(r"(\.\s+)(the|le|la|les|l’)\b", lambda m: m.group(1) + m.group(2)[0].upper() + m.group(2)[1:], s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s[:1].upper() + s[1:] if s else s


def _when_ok(when, p: Profile) -> bool:
    if when is None:
        return True
    if callable(when):
        return bool(when(p))
    from .engine import evaluate
    return evaluate(when, p)


def _gap_hit(gap, p: Profile) -> bool:
    code, values, _ = gap
    if callable(values):
        return bool(values(p))
    return p.has(code, *values)


def placeholders(text: str) -> list[dict]:
    return [{"type": PH_TYPE.get(m.group(1), m.group(1)), "text": m.group(2).strip(), "raw": m.group(0)} for m in PH_RE.finditer(text)]


def policy_number(prefix: str, code: str) -> str:
    c = CAT[code]
    kind = "EISP" if code == "EISP" else {3: "STD", 4: "PRC"}.get(c["level"], "POL")
    return f"{prefix}-{kind}-001" if code == "EISP" else f"{prefix}-{kind}-{c['abbr']}-001"


def compose(code: str, ctx: Context) -> dict:
    p, lang = ctx.profile, ctx.lang
    r = Resolver(ctx)
    cat = CAT[code]
    pid = policy_number(p.doc_prefix, code)
    sections_out, decisions, gaps, issues, refs = [], [], [], [], set()
    sec_no = 0
    for sec in LIBRARY[code]:
        if not _when_ok(sec.get("when"), p):
            continue
        clauses_out = []
        for cl in sec["clauses"]:
            if not _when_ok(cl.get("when"), p):
                continue
            cid = f"{code}-{cl['id']}"
            # -------- dynamic clauses
            if cl.get("dynamic"):
                dyn = _dynamic(cl["dynamic"], code, ctx, r)
                if dyn is None:
                    continue
                text, src, srcids, extra = dyn
                clauses_out.append({"clause_id": cid, "text": text, "modality": cl["modality"], "source_type": src,
                                    "source_ids": srcids, "framework_refs": list(cl.get("refs", [])),
                                    "review_status": "needs_owner_confirmation", "legal_review": src == "confirmed_obligation",
                                    "placeholders": placeholders(text), **extra})
                continue
            # -------- obligation-gated clauses
            if cl.get("obligation"):
                ob = cl["obligation"]
                if ob not in ctx.confirmed:
                    if ob in ctx.candidate_codes:
                        decisions.append({"id": f"OD-{cid}", "type": "SOURCE", "severity": "medium", "clause_id": cid,
                                          "text": T(lang, f"Clause withheld until applicability of “{OBL[ob]['name']['en']}” is decided by an authorized reviewer.",
                                                    f"Clause retenue jusqu’à ce qu’un réviseur autorisé statue sur l’applicabilité de « {OBL[ob]['name']['fr']} ».")})
                    continue
            # -------- text selection
            source_type, review, srcids = "framework_recommendation", "needs_owner_confirmation", []
            if cl.get("by"):
                dcode = cl["by"]
                val = p.value(dcode)
                variant = cl["variants"].get(val) if val is not None else None
                if variant is None:
                    variant = cl["variants"]["_none"]
                    source_type, review = "open_decision", "decision_required"
                else:
                    source_type = "organization_decision" if dcode.startswith("DEC-") else "company_fact"
                    review = "decision_recorded" if dcode.startswith("DEC-") else "user_confirmed"
                raw = variant[lang]
                srcids.append(dcode)
                ctx.inputs_used.add(dcode)
            else:
                raw = cl["text"][lang]
                if cl["src"] == "obligation":
                    source_type, review = "confirmed_obligation", "legal_review_required"
                    srcids.append(cl["obligation"])
            text, used = r.resolve(raw, code)
            for u in used:
                ctx.inputs_used.add(u)
            if cl["src"] in ("answer", "decision") and not cl.get("by"):
                ins = cl.get("inputs", [])
                srcids.extend(ins)
                ctx.inputs_used.update(ins)
                if all(p.answered(i) for i in ins) and ins:
                    source_type = "company_fact" if cl["src"] == "answer" else "organization_decision"
                    review = "user_confirmed" if cl["src"] == "answer" else "decision_recorded"
            extra = {}
            if cl.get("table"):
                tcols = cl["table"]["cols"][lang]
                trows = []
                for row in cl["table"]["rows"][lang]:
                    cells = []
                    for cell in row:
                        ctext, cused = r.resolve(cell, code)
                        ctx.inputs_used.update(cused)
                        cells.append(ctext)
                    trows.append(cells)
                extra = {"table": trows, "table_cols": tcols, "table_intro": text}
                text = text + " — " + " | ".join("; ".join(rw) for rw in trows)
            phs = placeholders(text)
            if phs and review in ("user_confirmed", "decision_recorded"):
                review = "needs_owner_confirmation"
            for ph in phs:
                decisions.append({"id": f"OD-{cid}-{len(decisions) + 1}", "type": ph["type"], "severity": PH_SEVERITY.get(ph["type"], "medium"),
                                  "clause_id": cid, "text": ph["text"]})
            if cl.get("gap") and _gap_hit(cl["gap"], p):
                enforce = p.value("GOV-09") == "enforceable"
                gaps.append({"clause_id": cid, "text": cl["gap"][2][lang], "question": cl["gap"][0],
                             "severity": "high" if enforce else "medium"})
            for ref in cl.get("refs", []):
                refs.add(ref)
            low = text.lower()
            for w in UNBOUNDED:
                if w in low:
                    issues.append({"kind": "ambiguous_wording", "severity": "low", "clause_id": cid,
                                   "message": T(lang, f"Unbounded wording “{w}” — link it to a standard or a defined parameter.",
                                                f"Formulation imprécise « {w} » — la rattacher à une norme ou à un paramètre défini.")})
            for phrase, target in CROSS_REFS.items():
                if phrase in low and target not in ctx.selected and target != code:
                    issues.append({"kind": "broken_cross_reference", "severity": "medium", "clause_id": cid,
                                   "message": T(lang, f"Refers to the {CAT[target]['title']['en']}, which is not selected in this package.",
                                                f"Renvoie à la {CAT[target]['title']['fr']}, qui n’est pas sélectionnée dans cet ensemble."),
                                   "suggestion": T(lang, "Select that policy, or edit the clause to refer to the document that covers the topic.",
                                                   "Sélectionnez cette politique ou modifiez la clause pour renvoyer au document qui couvre le sujet.")})
            clauses_out.append({"clause_id": cid, "text": text, "modality": cl["modality"], "source_type": source_type,
                                "source_ids": sorted(set(srcids)), "framework_refs": list(cl.get("refs", [])),
                                "review_status": review, "legal_review": bool(cl.get("legal")), "placeholders": phs, **extra})
        if not clauses_out:
            continue
        sec_no += 1
        for i, c in enumerate(clauses_out, 1):
            c["number"] = f"{sec_no}.{i}"
        sections_out.append({"section_id": sec["id"], "number": str(sec_no), "heading": sec["title"][lang], "clauses": clauses_out})

    parent = cat["parent"]
    body = {
        "schema": "pb-policy/1",
        "policy_code": code, "policy_id": pid, "title": cat["title"][lang], "language": lang,
        "policy_type": {1: "enterprise_policy", 2: "topic_policy", 3: "standard", 4: "procedure"}.get(cat["level"], "topic_policy"),
        "level": cat["level"], "level_label": LEVELS[cat["level"]][lang],
        "template": cat["template"],
        "parent_policy_id": policy_number(p.doc_prefix, parent) if parent else None,
        "parent_title": CAT[parent]["title"][lang] if parent else None,
        "organization": r.org(), "owner": r.owner(), "approver": r.approver() if code == "EISP" else r.topic_approver(),
        "classification": T(lang, "Internal", "Interne"), "status": "DRAFT", "version": f"0.{ctx.version_no}",
        "review_cycle": r.review(), "sections": sections_out, "open_decisions": decisions, "gaps": gaps,
        "issues": issues, "framework_refs": sorted(refs), "assumptions": list(ctx.assumptions),
        "children": [c["code"] for c in CAT.values() if c["parent"] == code and c["code"] in ctx.selected],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "library_version": LIBRARY_VERSION, "composer": COMPOSER_VERSION,
    }
    return body


def _dynamic(kind: str, code: str, ctx: Context, r: Resolver):
    lang = ctx.lang
    if kind == "obligations":
        conf = sorted(ctx.confirmed)
        if not conf:
            return (T(lang, "[SOURCE: Applicable laws, regulations and contracts — to be confirmed by an authorized reviewer.]",
                      "[SOURCE : Lois, règlements et contrats applicables — à confirmer par un réviseur autorisé.]"),
                    "open_decision", [], {})
        names = [OBL[c]["name"][lang] for c in conf if c in OBL]
        text = T(lang, "Confirmed as applicable: ", "Applicabilité confirmée : ") + "; ".join(names) + "."
        return text, "confirmed_obligation", conf, {"items": names}
    if kind == "policy_list":
        items = []
        for c in ctx.selected:
            if c == "EISP" or c not in CAT:
                continue
            items.append(f"{policy_number(ctx.profile.doc_prefix, c)} — {CAT[c]['title'][lang]}")
        if not items:
            return (T(lang, "[DECISION: Topic-specific policies to be developed under this policy.]",
                      "[DÉCISION : Politiques thématiques à élaborer en vertu de la présente politique.]"), "open_decision", [], {})
        text = T(lang, "The following topic-specific policies are issued under this policy: ",
                 "Les politiques thématiques suivantes sont adoptées en vertu de la présente politique : ") + "; ".join(items) + "."
        return text, "company_fact", ["SELECTION"], {"items": items}
    if kind == "class_table":
        levels = r.levels()
        desc_en = {0: "Information approved for public release; disclosure causes no harm.",
                   1: "Information for internal use; unauthorized disclosure would cause limited harm.",
                   2: "Sensitive information, including personal information and client information; unauthorized disclosure would cause significant harm.",
                   3: "Highly sensitive information whose compromise would cause severe harm (e.g., credentials and keys, health or financial data of individuals, critical trade secrets)."}
        desc_fr = {0: "Information dont la diffusion publique est approuvée; sa divulgation ne cause aucun préjudice.",
                   1: "Information à usage interne; sa divulgation non autorisée causerait un préjudice limité.",
                   2: "Information sensible, y compris les renseignements personnels et l’information des clients; sa divulgation non autorisée causerait un préjudice important.",
                   3: "Information très sensible dont la compromission causerait un préjudice grave (p. ex. authentifiants et clés, données de santé ou financières de personnes, secrets commerciaux essentiels)."}
        rows = []
        n = len(levels)
        for i, lv in enumerate(levels):
            idx = round(i * 3 / (n - 1)) if n > 1 else 0
            d = (desc_fr if lang == "fr" else desc_en)[idx]
            rows.append(f"{lv}: {d}")
        text = T(lang, "Level definitions — ", "Définition des niveaux — ") + " ".join(f"({i + 1}) {row}" for i, row in enumerate(rows))
        return text, "framework_recommendation", ["DATA-02B"], {
            "table": [[lv, rows[i].split(': ', 1)[1]] for i, lv in enumerate(levels)],
            "table_cols": T(lang, "Level|Definition", "Niveau|Définition").split("|"),
            "table_intro": T(lang, "Level definitions", "Définition des niveaux")}
    if kind == "handling_matrix":
        levels = r.levels()
        n = len(levels)
        M = {"en": [
            ["No label required", "Any approved system", "No restriction", "May be published", "Normal recycling"],
            ["Optional “Internal” label", "{org} systems and approved cloud services", "Internal channels; encrypted (TLS) over public networks", "To third parties under an agreement or with a business need", "Normal disposal; wipe devices"],
            ["“Confidential” label on documents and messages", "Approved locations only; encrypted on portable devices and removable media", "Encrypted; verify recipients; secure link with expiry for external sharing", "Only with the owner’s authorization and a confidentiality obligation", "Cross-cut shredding; sanitize or destroy media"],
            ["“" + levels[-1] + "” label on every page and message", "Systems approved by {sec} for this level; access logged", "End-to-end encryption; no personal email or messaging", "Only with the owner’s prior written approval, recorded", "Certified destruction with a record"]],
            "fr": [
            ["Aucune mention requise", "Tout système approuvé", "Aucune restriction", "Peut être publiée", "Recyclage normal"],
            ["Mention « Interne » facultative", "Systèmes de {org} et services infonuagiques approuvés", "Canaux internes; chiffrée (TLS) sur les réseaux publics", "À des tiers en vertu d’une entente ou d’un besoin d’affaires", "Élimination normale; effacement des appareils"],
            ["Mention « Confidentiel » sur les documents et messages", "Emplacements approuvés seulement; chiffrée sur appareils portables et supports amovibles", "Chiffrée; vérifier les destinataires; lien sécurisé avec échéance pour le partage externe", "Seulement avec l’autorisation du responsable et une obligation de confidentialité", "Déchiquetage en particules; assainissement ou destruction des supports"],
            ["Mention « " + levels[-1] + " » sur chaque page et message", "Systèmes approuvés par {sec} pour ce niveau; accès journalisé", "Chiffrement de bout en bout; aucune messagerie personnelle", "Seulement avec l’approbation écrite préalable du responsable, consignée", "Destruction certifiée avec preuve"]]}[lang]
        rows = []
        for i, lv in enumerate(levels):
            idx = round(i * 3 / (n - 1)) if n > 1 else 0
            cells = []
            for cell in M[idx]:
                t_, _u = r.resolve(cell, code)
                cells.append(t_)
            rows.append([lv] + cells)
        cols = T(lang, "Level|Labelling|Storage|Transmission|Sharing|Disposal",
                 "Niveau|Mention|Stockage|Transmission|Partage|Élimination").split("|")
        intro = T(lang, "Minimum handling rules by classification level", "Règles minimales de manipulation par niveau de classification")
        text = intro + " — " + " | ".join("; ".join(rw) for rw in rows)
        return text, "framework_recommendation", ["DATA-02B"], {"table": rows, "table_cols": cols, "table_intro": intro}
    return None


def document_summary(body: dict) -> dict:
    n_clauses = sum(len(s["clauses"]) for s in body["sections"])
    by_src: dict[str, int] = {}
    for s in body["sections"]:
        for c in s["clauses"]:
            by_src[c["source_type"]] = by_src.get(c["source_type"], 0) + 1
    return {"clauses": n_clauses, "by_source": by_src, "open_decisions": len(body["open_decisions"]),
            "high": sum(1 for d in body["open_decisions"] if d["severity"] == "high"), "gaps": len(body["gaps"]),
            "issues": len(body["issues"])}
