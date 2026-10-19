"""Rule-based candidate-fact extraction (offline, deterministic, explainable).

Each rule maps a pattern in a document segment to a *proposed* answer for a question or decision code.
Facts are never applied automatically: the user confirms or rejects each one (spec §5.9-4, §6.2).
"""
from __future__ import annotations

import re

LEVEL_WORDS = ["Public", "Internal", "Confidential", "Restricted", "Highly Confidential", "Secret", "Sensitive",
               "Protected A", "Protected B", "Protected C", "Interne", "Confidentiel", "Restreint", "Protégé A", "Protégé B",
               "Protégé C", "Très confidentiel", "Diffusion restreinte"]
LEVEL_RE = re.compile(r"\b(" + "|".join(sorted((re.escape(w) for w in LEVEL_WORDS), key=len, reverse=True)) + r")\b")

DAYS_MAP = {"7": "7", "14": "14", "30": "30"}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.;!?])\s+|\n+", text) if len(s.strip()) > 8]


def _fact(code, label, value, quote, conf="medium"):
    return {"fact_type": code, "label": label, "value": value, "quote": quote[:300], "confidence": conf}


def extract_rule_facts(text: str) -> list[dict]:
    facts: list[dict] = []
    for s in _sentences(text):
        low = s.lower()
        # ---- classification scheme
        if re.search(r"classif", low):
            levels = []
            for m in LEVEL_RE.finditer(s):
                w = m.group(1)
                if w not in levels:
                    levels.append(w)
            if len(levels) >= 3:
                facts.append(_fact("DATA-02B", "Classification levels", ", ".join(levels), s, "high"))
                facts.append(_fact("DATA-02", "A classification scheme exists", "formal", s, "medium"))
        # ---- MFA scope
        if re.search(r"multi-?factor|\bmfa\b|\b2fa\b|two-factor|multifacteur|\bamf\b", low) and \
                re.search(r"\bmust\b|\bshall\b|required|mandatory|\bdoit\b|obligatoire|exig", low):
            if re.search(r"all (users|accounts|staff|employees)|tous les (utilisateurs|comptes|employés)", low):
                val = "all"
            elif re.search(r"remote|vpn|email|cloud|à distance|courriel|infonuag", low):
                val = "remote_priv_cloud"
            elif re.search(r"privileged|admin|privilégi", low):
                val = "priv"
            else:
                val = None
            if val:
                facts.append(_fact("DEC-IAM-MFA-SCOPE", "MFA requirement stated in document", val, s, "medium"))
        # ---- password rotation (parameter tracked for contradictions)
        m = re.search(r"password[s]?.{0,60}?(?:changed|expire|rotat)\w*.{0,30}?(?:every|after)\s+(\d{1,3})\s+days", low) or \
            re.search(r"mots? de passe.{0,60}?(?:changé|expir|renouvel)\w*.{0,30}?(?:tous les|après)\s+(\d{1,3})\s+jours", low)
        if m:
            facts.append(_fact("PARAM-PWD-ROTATION", "Password rotation interval (days)", m.group(1), s, "high"))
        elif re.search(r"\b(no|not require\w*|without)\s+(?:(?:periodic|forced|scheduled|mandatory|regular)\s+){1,2}(?:password\s+)?(change|rotation|expir)|"
                       r"pas de (changement|renouvellement)( de mot de passe)? (périodique|forcé)", low):
            facts.append(_fact("PARAM-PWD-ROTATION", "Password rotation interval (days)", "none (risk-based)", s, "high"))
        # ---- review cycle
        m = re.search(r"review(?:ed)?\b.{0,40}?(annually|every (?:12|twelve|24|two years|36|three years)|each year|yearly)", low) or \
            re.search(r"révis\w*.{0,40}?(annuellement|chaque année|tous les (?:12|24|36) mois|tous les (?:deux|trois) ans)", low)
        if m and re.search(r"polic|politique", low):
            g = m.group(1)
            val = "24" if re.search(r"24|two years|deux ans", g) else "36" if re.search(r"36|three years|trois ans", g) else "12"
            facts.append(_fact("GOV-10", "Policy review cycle (months)", val, s, "medium"))
        # ---- vulnerability timeframes
        m = re.search(r"critical\s+vulnerabilit\w*.{0,80}?within\s+(\d{1,3})\s+days", low) or \
            re.search(r"vulnérabilités?\s+critiques?.{0,80}?(?:dans les|en|sous)\s+(\d{1,3})\s+jours", low)
        if m and m.group(1) in DAYS_MAP:
            facts.append(_fact("DEC-VULN-CRIT", "Remediation time for critical vulnerabilities", m.group(1), s, "high"))
        m = re.search(r"\bhigh\b(?:[- ]severity|[- ]risk)?\s+vulnerabilit\w*.{0,80}?within\s+(\d{1,3})\s+days", low)
        if m and m.group(1) in ("30", "60", "90"):
            facts.append(_fact("DEC-VULN-HIGH", "Remediation time for high vulnerabilities", m.group(1), s, "high"))
        # ---- leavers
        if re.search(r"(access|accounts?|accès|comptes?).{0,60}(disabled|revoked|removed|désactivé|révoqué|retiré)", low):
            if re.search(r"last (working )?day|same day|dernier jour|même jour", low):
                facts.append(_fact("DEC-IAM-LEAVER", "Deadline to disable leavers’ access", "same_day", s, "medium"))
            elif re.search(r"24 ?h|24 hours|24 heures", low):
                facts.append(_fact("DEC-IAM-LEAVER", "Deadline to disable leavers’ access", "24h", s, "medium"))
            elif re.search(r"72 ?h|72 hours|72 heures|three days|trois jours", low):
                facts.append(_fact("DEC-IAM-LEAVER", "Deadline to disable leavers’ access", "72h", s, "medium"))
        # ---- backups
        if re.search(r"back-?ups?|sauvegard", low):
            if re.search(r"\bdaily\b|every day|quotidien|chaque jour", low):
                facts.append(_fact("DEC-BKP-FREQ", "Backup frequency", "daily", s, "medium"))
            elif re.search(r"\bweekly\b|hebdomadaire", low):
                facts.append(_fact("DEC-BKP-FREQ", "Backup frequency", "weekly", s, "medium"))
            if re.search(r"restor\w*.{0,40}test|test\w*.{0,40}restor|restaur\w*.{0,40}test|test\w*.{0,40}restaur", low):
                val = "quarterly" if re.search(r"quarter|trimest", low) else "semiannual" if re.search(r"six months|semi-?annual|six mois|semestri", low) \
                    else "annual" if re.search(r"annual|yearly|annuel", low) else None
                if val:
                    facts.append(_fact("DEC-BKP-TEST", "Restoration test frequency", val, s, "medium"))
            if re.search(r"immutable|offline|air-?gap|immuable|hors ligne", low):
                facts.append(_fact("DEC-BKP-IMMUTABLE", "Offline or immutable backup copy", "yes", s, "medium"))
        # ---- exceptions duration
        m = re.search(r"exception\w*.{0,80}?(?:maximum|not exceed|up to|at most|valid for)\D{0,20}(3|6|12|three|six|twelve)\s+months", low) or \
            re.search(r"dérogation\w*.{0,80}?(?:maximum|au plus|n’excède pas|valide)\D{0,20}(3|6|12|trois|six|douze)\s+mois", low)
        if m:
            val = {"three": "3", "six": "6", "twelve": "12", "trois": "3", "douze": "12"}.get(m.group(1), m.group(1))
            facts.append(_fact("DEC-EXC-MAX", "Maximum exception duration (months)", val, s, "medium"))
        # ---- supplier notification
        m = re.search(r"(supplier|vendor|provider|contractor|fournisseur|prestataire).{0,120}?(?:notify|inform|aviser|informer).{0,60}?(24|48|72)\s*(?:h|hours|heures)", low)
        if m:
            facts.append(_fact("DEC-TP-NOTIFY", "Supplier incident notification deadline (hours)", m.group(2), s, "medium"))
        # ---- log retention
        m = re.search(r"logs?.{0,60}?(?:retained|kept|stored)\s+for\s+(?:at least\s+)?(\d+)\s+(days|months|year|years)", low) or \
            re.search(r"journaux.{0,60}?conserv\w+\s+(?:pendant|durant|au moins)?\s*(\d+)\s+(jours|mois|an|ans)", low)
        if m:
            n, unit = int(m.group(1)), m.group(2)
            days = n * (30 if unit.startswith("mo") else 365 if unit.startswith(("y", "an")) else 1)
            val = "90" if 80 <= days <= 100 else "365" if 330 <= days <= 400 else "730" if 700 <= days <= 760 else None
            if val:
                facts.append(_fact("DEC-LOG-RETENTION", "Security log retention", val, s, "medium"))
        # ---- approver of the policy
        m = re.search(r"approved by (the )?(board of directors|executive committee|chief executive officer|ceo|president)", low) or \
            re.search(r"approuvée? par (le |la )?(conseil d.administration|comité de direction|président|directeur général)", low)
        if m and re.search(r"polic|politique", low):
            facts.append(_fact("ORG-07B", "Approver of the enterprise policy", s[m.start(2):m.end(2)].strip().capitalize(), s, "medium"))
        # ---- BYOD
        if re.search(r"personal (devices?|phones?|computers?)|byod|appareils? personnels?|avap", low):
            if re.search(r"not (be )?(permitted|allowed)|prohibited|must not|interdit|ne doivent pas|n.est pas permis", low):
                facts.append(_fact("TECH-02B", "Personal devices (BYOD)", "no", s, "medium"))
            elif re.search(r"permitted|allowed|may (be )?used|may access|permis|autorisé|peuvent", low):
                facts.append(_fact("TECH-02B", "Personal devices (BYOD)", "yes", s, "low"))
        # ---- frameworks
        for pat, val in ((r"iso/?iec 27001|iso 27001", "iso27001"), (r"nist (csf|cybersecurity framework)", "nist_csf"),
                         (r"cis controls?|cis critical", "cis"), (r"soc ?2", "soc2"), (r"800-53", "nist_80053")):
            if re.search(pat, low) and re.search(r"adopt|align|follow|based on|certif|conform|aligné|fondé|adopté", low):
                facts.append(_fact("GOV-04", "Framework adopted or referenced", [val], s, "low"))
        # ---- privacy officer role
        if re.search(r"privacy officer|person in charge of the protection of personal information|chief privacy officer|"
                     r"responsable de la protection des renseignements personnels", low):
            facts.append(_fact("ORG-13", "Privacy officer role mentioned", ["privacy_officer"], s, "low"))
    # de-duplicate (same type + value + quote)
    seen, out = set(), []
    for f in facts:
        k = (f["fact_type"], str(f["value"]), f["quote"])
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


ALLOWED_AI_FACT_TYPES = ["DATA-02B", "DEC-IAM-MFA-SCOPE", "PARAM-PWD-ROTATION", "GOV-10", "DEC-VULN-CRIT", "DEC-VULN-HIGH",
                         "DEC-IAM-LEAVER", "DEC-BKP-FREQ", "DEC-BKP-TEST", "DEC-EXC-MAX", "DEC-TP-NOTIFY", "DEC-LOG-RETENTION",
                         "ORG-07B", "TECH-02B", "ORG-03", "ORG-14", "TECH-01"]
