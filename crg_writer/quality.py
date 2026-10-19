"""Quality checks over a set of Writer drafts, in English and French (deterministic, explainable).

Findings are about the drafts and the package — open decisions that block approval, clauses that need
legal review, documents whose parent is missing, owners named inconsistently, documents that disagree,
implementation gaps, structure templates. They are advice to the author; approval stays in ISP management.
© 2026 Marc-André Léger. CC BY-NC 4.0
"""
from __future__ import annotations

import json

from .catalogue import BY_CODE as CAT


def check(bodies: dict, selected: list[str], facts: list[dict] | None = None, refs: dict | None = None) -> list[dict]:
    """bodies: {code: {lang: body}} for the drafts just produced; refs: {code: ISP record id} for messages."""
    out: list[dict] = []
    refs = refs or {}

    def add(kind, sev, en, fr, code=None, clause=None, sug_en="", sug_fr=""):
        key = f"{kind}|{code or ''}|{clause or ''}|{en[:80]}"
        if any(x["key"] == key for x in out):
            return
        out.append({"key": key, "kind": kind, "severity": sev, "code": code, "clause": clause, "en": en, "fr": fr,
                    "suggestion": {"en": sug_en, "fr": sug_fr}})

    blocking, legal, owners = [], [], set()
    for code, by_lang in bodies.items():
        b = by_lang.get("en") or next(iter(by_lang.values()))
        bf = by_lang.get("fr") or b
        name = refs.get(code) or b["policy_id"]
        frx = {(x["kind"], x.get("clause_id")): x for x in bf["issues"]}
        for f in b["issues"]:
            g = frx.get((f["kind"], f.get("clause_id")), f)
            add(f["kind"], f["severity"], f"{name} {f.get('clause_id') or ''}: {f['message']}", f"{name} {g.get('clause_id') or ''} : {g['message']}",
                code, f.get("clause_id"), f.get("suggestion", ""), g.get("suggestion", ""))
        high = sum(1 for x in b["open_decisions"] if x["severity"] == "high")
        if high:
            blocking.append(f"{name} ({high})")
        if any(c.get("legal_review") for s in b["sections"] for c in s["clauses"]):
            legal.append(name)
        fg = {x["clause_id"]: x["text"] for x in bf.get("gaps", [])}
        for g in b.get("gaps", []):
            add("implementation_gap", g["severity"], f"{name} {g['clause_id']}: {g['text']} The requirement needs implementation work before it can be enforced.",
                f"{name} {g['clause_id']} : {fg.get(g['clause_id'], g['text'])} L’exigence nécessite des travaux de mise en œuvre avant de pouvoir être appliquée.", code, g["clause_id"])
        if b["template"] == "structure":
            add("structure_template", "medium", f"{name}: structure template — the owner still has to write the mandatory requirements.",
                f"{name} : gabarit de structure — le responsable doit encore rédiger les exigences obligatoires.", code)
        if not b["owner"].startswith("["):
            owners.add(b["owner"])
    if blocking:
        add("unresolved_placeholders", "high",
            "High-severity open decisions remain (the draft can still be reviewed; approval should wait): " + ", ".join(blocking) + ".",
            "Des décisions ouvertes de gravité élevée subsistent (l’ébauche peut être révisée; l’approbation devrait attendre) : " + ", ".join(blocking) + ".",
            sug_en="Answer the Decisions step, or complete the highlighted placeholders in the drafts.",
            sug_fr="Répondez à l’étape Décisions ou complétez les espaces réservés surlignés dans les ébauches.")
    if legal:
        add("legal_review", "medium", "Clauses flagged for legal review (privacy, monitoring, retention, sanctions or notification) in: " + ", ".join(legal) + ".",
            "Clauses à soumettre à une révision juridique (vie privée, surveillance, conservation, sanctions ou notification) dans : " + ", ".join(legal) + ".")
    orphans = [c for c in selected if CAT.get(c, {}).get("parent") and CAT[c]["parent"] not in selected]
    if orphans:
        add("missing_parent", "medium",
            "These documents refer to a parent document that is not selected: " + ", ".join(f"{c} → {CAT[CAT[c]['parent']]['title']['en']}" for c in orphans) + ".",
            "Ces documents renvoient à un document parent qui n’est pas sélectionné : " + ", ".join(f"{c} → {CAT[CAT[c]['parent']]['title']['fr']}" for c in orphans) + ".",
            sug_en="Select the parent documents, or replace the references with the document that plays that role.",
            sug_fr="Sélectionnez les documents parents ou remplacez les renvois par le document qui joue ce rôle.")
    if len({o.lower() for o in owners}) > 2:
        add("role_inconsistency", "low", f"Different owner names are used across documents: {', '.join(sorted(owners))}.",
            f"Des noms de responsables différents sont utilisés dans les documents : {', '.join(sorted(owners))}.")
    groups: dict[str, set] = {}
    for f in facts or []:
        if f.get("conflict_group") and f.get("state", "proposed") == "proposed":
            groups.setdefault(f["conflict_group"], set()).add(json.dumps(f["value"], ensure_ascii=False))
    for grp, vals in sorted(groups.items()):
        code = grp.replace("CONFLICT-", "")
        add("evidence_conflict", "high", f"Documents disagree on {code}: {', '.join(sorted(vals))}. Neither value is used until you decide in Documents & facts.",
            f"Des documents se contredisent sur {code} : {', '.join(sorted(vals))}. Aucune valeur n’est utilisée avant votre décision à l’étape Documents et faits.")
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(out, key=lambda x: order.get(x["severity"], 3))
