"""From a Writer draft to an ISP management policy — the hand-over from writing to managing.

A Writer body (sections of clauses) becomes the structure ISP management uses and CRGO describes:
  • the Purpose and Scope sections, when purely descriptive, become the policy's purpose and scope;
  • every other section becomes a clause (heading + descriptive text, tables kept as Markdown tables);
  • every normative clause (must, must not, should, may) becomes a policy statement with its modality, the
    clause it sits in, its CRGO control identifiers, and the Writer clause id it came from (``wid``).
The ``wid`` is what keeps statement identifiers stable when a draft is regenerated, and what lets the
person keep an edit made in ISP management instead of the regenerated text.
© 2026 Marc-André Léger. CC BY-NC 4.0
"""
from __future__ import annotations

from .catalogue import BY_CODE as CAT
from .crgo import crg_refs

MOD = {"must": "must", "must not": "mustnot", "should": "should", "may": "may"}
TYPE = {1: "policy", 2: "policy", 3: "standard", 4: "procedure"}
DOMAIN = {
    "governance": ("Governance", "Gouvernance"), "people": ("People", "Personnes"), "identity": ("Identity and access", "Identités et accès"),
    "information": ("Information", "Information"), "resilience": ("Resilience", "Résilience"), "suppliers": ("Third parties", "Tiers"),
    "operations": ("Operations", "Exploitation"), "development": ("Applications", "Applications"), "specialized": ("Specialized environments", "Environnements spécialisés"),
}


def _md_table(cols, rows):
    esc = lambda s: str(s or "").replace("|", "/").replace("\n", " ")          # noqa: E731
    return "\n".join(["| " + " | ".join(esc(c) for c in cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows])


def to_isp(body: dict) -> dict:
    lang = body["language"]
    purpose, scope, clauses, statements = [], [], [], []
    for sec in body["sections"]:
        normative = [c for c in sec["clauses"] if c["modality"] in MOD and not c.get("table")]
        texts = []
        for c in sec["clauses"]:
            if c.get("table"):
                texts.append((c.get("table_intro") or "").rstrip(" —") + "\n" + _md_table(c.get("table_cols") or [], c["table"]))
            elif c["modality"] not in MOD:
                texts.append(c["text"])
        if sec["section_id"] == "SEC-PURPOSE" and not normative:
            purpose += texts
            continue
        if sec["section_id"] == "SEC-SCOPE" and not normative:
            scope += texts
            continue
        clauses.append({"wsec": sec["section_id"], "heading": sec["heading"], "text": "\n".join(texts)})
        for c in normative:
            statements.append({"wid": c["clause_id"], "wsec": sec["section_id"], "text": c["text"], "modality": MOD[c["modality"]],
                               "refs": crg_refs(c.get("framework_refs")), "guideline": False,
                               "src": c["source_type"], "ids": c.get("source_ids", []), "review": c["review_status"], "legal": bool(c.get("legal_review"))})
    cat = CAT[body["policy_code"]]
    dom = DOMAIN.get(cat.get("domain"), (cat.get("domain", ""), cat.get("domain", "")))
    return {
        "code": body["policy_code"], "language": lang, "reference": body["policy_id"], "title": body["title"],
        "type": TYPE.get(body["level"], "policy"), "domain": dom[1] if lang == "fr" else dom[0], "level": body["level"], "level_label": body["level_label"],
        "purpose": "\n".join(purpose), "scope": "\n".join(scope), "clauses": clauses, "statements": statements,
        "owner": "" if body["owner"].startswith("[") else body["owner"], "approver": "" if body["approver"].startswith("[") else body["approver"],
        "owner_text": body["owner"], "approver_text": body["approver"],
        "parent": body.get("parent_policy_id"), "parent_code": cat.get("parent"), "parent_title": body.get("parent_title"),
        "template": body["template"], "review_cycle": body["review_cycle"],
        "meta": {"open_decisions": body["open_decisions"], "gaps": [{**g, "where": g["clause_id"]} for g in body["gaps"]], "assumptions": body["assumptions"],
                 "issues": body["issues"], "framework_refs": body["framework_refs"], "generated_at": body["generated_at"],
                 "library_version": body["library_version"], "composer": body["composer"], "children": body["children"], "template": body["template"]},
    }
