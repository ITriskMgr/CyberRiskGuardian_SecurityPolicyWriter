"""Word rendering of an ISP policy (any policy of ISP management, drafted by the Writer or not).

The document is rebuilt from the policy record every time: the record in CyberRiskGuardian is the source
of truth, the .docx is a derived, editable copy. Every statement and every paragraph of clause text carries
a hidden bookmark with its identifier, and the document properties carry the workspace, the policy, the
version and a hash of the content exported — that is what re-import uses to put edits back in place.
© 2026 Marc-André Léger. CC BY-NC 4.0
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date

from .ooxml import GREY, RED, Doc, Run, bookmark, runs_with_placeholders, PH_RE

L = {
    "en": {"draft": "DRAFT — NOT APPROVED", "frozen": "APPROVED VERSION — FROZEN", "doc_control": "Document control", "rec": "ISP record",
           "ref": "Document number", "version": "Version", "status": "Status", "classification": "Classification", "internal": "Internal",
           "owner": "Policy owner", "approver": "Approval authority", "author": "Author", "family": "Policy family", "parent": "Parent document",
           "review": "Review cycle", "months": "{0} months", "effective": "Effective date", "next": "Next review date", "hash": "SHA-256 of the approved content",
           "set": "Set on approval and publication", "lang": "Language", "lang_name": "English", "generated": "Produced with", "on": "Exported on",
           "rev": "Revision history", "rev_cols": ["Date", "Version", "Status", "By", "Change"], "appr": "Approval", "appr_cols": ["Role", "Name", "Signature", "Date"],
           "contents": "Contents", "toc": "Right-click and choose “Update Field” (or press F9) to build the table of contents.",
           "purpose": "Purpose", "scope": "Scope", "other": "Other policy statements", "details": "Details",
           "guideline": "guideline — not binding", "app_a": "Appendix A — Open decisions", "app_a_none": "No placeholder remains in this version.",
           "od_cols": ["#", "Where", "Type", "Decision or information needed"], "app_b": "Appendix B — Statements and traceability",
           "tr_cols": ["Statement", "Modality", "Basis", "Controls (CRGO)", "Review"], "app_c": "Appendix C — Assumptions and implementation gaps",
           "assumptions": "Assumptions", "gaps": "Requirements that need implementation work", "page": "Page", "of": "of",
           "structure": "Structure template: the owner still has to write the mandatory requirements of the sections below.",
           "disclaimer": "Draft produced with decision-support software (CyberRiskGuardian Security Policy Writer). It is not legal advice and is not in force until approved and published in ISP management by the authorized persons. Control references indicate the topics addressed; a mapping, a statement or an acknowledgement is never evidence of compliance.",
           "type": {"policy": "Policy", "standard": "Standard", "procedure": "Procedure", "guideline": "Guideline"},
           "state": {"draft": "Draft — not approved; not in force", "review": "In review — not approved; not in force", "approved": "Approved — not published yet",
                     "published": "Published — in force", "retired": "Retired", "superseded": "Superseded"},
           "mod": {"must": "Must", "mustnot": "Must not", "should": "Should", "may": "May"},
           "basis": {"framework_recommendation": "Good practice — owner to confirm", "company_fact": "Company answer", "organization_decision": "Organization decision",
                     "open_decision": "Open decision", "confirmed_obligation": "Confirmed obligation", "manual": "Written in ISP management", "user_added": "Added in Word"},
           "rv": {"needs_owner_confirmation": "Owner confirmation needed", "user_confirmed": "Confirmed", "decision_recorded": "Decision recorded",
                  "decision_required": "Decision required", "legal_review_required": "Legal review required", "edited": "Edited — review"},
           "ph": {}},
    "fr": {"draft": "ÉBAUCHE — NON APPROUVÉE", "frozen": "VERSION APPROUVÉE — FIGÉE", "doc_control": "Contrôle du document", "rec": "Dossier GPSI",
           "ref": "Numéro du document", "version": "Version", "status": "Statut", "classification": "Classification", "internal": "Interne",
           "owner": "Responsable de la politique", "approver": "Autorité d’approbation", "author": "Auteur", "family": "Famille de politiques", "parent": "Document parent",
           "review": "Cycle de révision", "months": "{0} mois", "effective": "Date d’entrée en vigueur", "next": "Prochaine révision", "hash": "SHA-256 du contenu approuvé",
           "set": "Fixée à l’approbation et à la publication", "lang": "Langue", "lang_name": "Français", "generated": "Produit avec", "on": "Exporté le",
           "rev": "Historique des révisions", "rev_cols": ["Date", "Version", "Statut", "Par", "Modification"], "appr": "Approbation", "appr_cols": ["Rôle", "Nom", "Signature", "Date"],
           "contents": "Table des matières", "toc": "Cliquez avec le bouton droit et choisissez « Mettre à jour les champs » (ou F9) pour générer la table des matières.",
           "purpose": "Objet", "scope": "Portée", "other": "Autres énoncés de politique", "details": "Précisions",
           "guideline": "ligne directrice — non contraignante", "app_a": "Annexe A — Décisions ouvertes", "app_a_none": "Aucun espace réservé ne subsiste dans cette version.",
           "od_cols": ["#", "Emplacement", "Type", "Décision ou information requise"], "app_b": "Annexe B — Énoncés et traçabilité",
           "tr_cols": ["Énoncé", "Modalité", "Fondement", "Mesures (CRGO)", "Révision"], "app_c": "Annexe C — Hypothèses et écarts de mise en œuvre",
           "assumptions": "Hypothèses", "gaps": "Exigences nécessitant des travaux de mise en œuvre", "page": "Page", "of": "de",
           "structure": "Gabarit de structure : le responsable doit encore rédiger les exigences obligatoires des sections ci-dessous.",
           "disclaimer": "Ébauche produite avec un logiciel d’aide à la décision (CyberRiskGuardian Security Policy Writer). Elle ne constitue pas un avis juridique et n’est pas en vigueur tant qu’elle n’a pas été approuvée et publiée dans la gestion des PSI par les personnes autorisées. Les renvois aux mesures indiquent les sujets traités; une correspondance, un énoncé ou une attestation ne prouve jamais la conformité.",
           "type": {"policy": "Politique", "standard": "Norme", "procedure": "Procédure", "guideline": "Ligne directrice"},
           "state": {"draft": "Ébauche — non approuvée; non en vigueur", "review": "En révision — non approuvée; non en vigueur", "approved": "Approuvée — pas encore publiée",
                     "published": "Publiée — en vigueur", "retired": "Retirée", "superseded": "Remplacée"},
           "mod": {"must": "Doit", "mustnot": "Ne doit pas", "should": "Devrait", "may": "Peut"},
           "basis": {"framework_recommendation": "Bonne pratique — à confirmer", "company_fact": "Réponse de l’organisation", "organization_decision": "Décision de l’organisation",
                     "open_decision": "Décision ouverte", "confirmed_obligation": "Obligation confirmée", "manual": "Rédigé dans la gestion des PSI", "user_added": "Ajouté dans Word"},
           "rv": {"needs_owner_confirmation": "Confirmation du responsable requise", "user_confirmed": "Confirmé", "decision_recorded": "Décision consignée",
                  "decision_required": "Décision requise", "legal_review_required": "Révision juridique requise", "edited": "Modifié — à réviser"},
           "ph": {"DECISION": "DÉCISION", "ROLE": "RÔLE", "VALUE": "VALEUR", "APPROVER": "APPROBATEUR", "TECHNICAL_DETAIL": "DÉTAIL TECHNIQUE"}},
}
PH_TYPE = re.compile(r"\[(DECISION|DÉCISION|ROLE|RÔLE|VALUE|VALEUR|DATE|SOURCE|APPROVER|APPROBATEUR|TECHNICAL_DETAIL|DÉTAIL_TECHNIQUE)\s*:\s*([^\]]+)\]")
NORM = {"DÉCISION": "DECISION", "RÔLE": "ROLE", "VALEUR": "VALUE", "APPROBATEUR": "APPROVER", "DÉTAIL_TECHNIQUE": "TECHNICAL_DETAIL"}


def content_hash(policy: dict) -> str:
    """Hash of what re-import compares against: purpose, scope, clause texts and statements."""
    c = {"purpose": policy.get("purpose", ""), "scope": policy.get("scope", ""),
         "clauses": [[x.get("id"), x.get("heading", ""), x.get("text", "")] for x in policy.get("clauses", [])],
         "statements": [[s.get("id"), s.get("text", ""), s.get("modality", ""), s.get("clause", "")] for s in policy.get("statements", [])]}
    return hashlib.sha256(json.dumps(c, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def paragraphs_of(text: str) -> list[dict]:
    """Clause text → blocks: {'p': text} paragraphs, {'table': (cols, rows)} for Markdown pipe tables."""
    out, rows = [], []

    def flush_table():
        if rows:
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            cells = [r for r in cells if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
            if cells:
                out.append({"table": (cells[0], cells[1:])})
            rows.clear()
    for line in (text or "").split("\n"):
        if line.strip().startswith("|"):
            rows.append(line)
            continue
        flush_table()
        if line.strip():
            out.append({"p": line.strip()})
    flush_table()
    return out


def _cap(s):
    return s[:1].upper() + s[1:] if s else s


def render(doc: dict) -> bytes:
    lang = "fr" if doc.get("lang") == "fr" else "en"
    lab = L[lang]
    p = doc["policy"]
    w = doc.get("writer") or {}
    frozen = doc.get("frozen")
    org = doc.get("org") or ""
    ref = p.get("reference") or p.get("id")
    D = Doc(lang)
    D.title(p.get("title") or "")
    typ = lab["type"].get(p.get("type") or "policy", p.get("type"))
    D.para([Run(f"{org}  ·  {ref}  ·  {typ}", size=11, color=GREY)])
    if frozen:
        D.banner(f"{lab['frozen']} — v{frozen.get('version')}", fill="E7F4EA", color="1E6B34")
    else:
        D.banner(lab["draft"])
    D.heading(lab["doc_control"], 2)
    rows = [(lab["ref"], ref), (lab["rec"], p.get("id")), (lab["version"], p.get("version")),
            (lab["status"], lab["state"].get(p.get("status"), p.get("status"))), (lab["classification"], lab["internal"]),
            (lab["owner"], _cap(p.get("owner") or ("[RÔLE : responsable de la politique]" if lang == "fr" else "[ROLE: policy owner]"))),
            (lab["approver"], _cap(p.get("approver") or ("[APPROBATEUR : autorité d’approbation]" if lang == "fr" else "[APPROVER: approval authority]")))]
    if doc.get("family"):
        rows.append((lab["family"], doc["family"]))
    if doc.get("parent"):
        rows.append((lab["parent"], doc["parent"]))
    rows += [(lab["review"], lab["months"].replace("{0}", str(p.get("reviewMonths") or 12))),
             (lab["effective"], (frozen or {}).get("effective") or p.get("effective") or lab["set"]),
             (lab["next"], (frozen or {}).get("nextReview") or p.get("nextReview") or lab["set"])]
    if frozen and frozen.get("hash"):
        rows.append((lab["hash"], frozen["hash"]))
    rows += [(lab["lang"], lab["lang_name"]), (lab["generated"], doc.get("generator") or "CyberRiskGuardian"), (lab["on"], date.today().isoformat())]
    D.kv(rows)
    hist = p.get("history") or []
    if hist:
        D.heading(lab["rev"], 2)
        D.table(lab["rev_cols"], [[h.get("date", ""), h.get("version", ""), h.get("status", ""), h.get("by", ""), h.get("what", "")] for h in hist[-12:]],
                [2.3, 1.6, 2.2, 3.0, 7.4], font_pt=8.5)
    D.heading(lab["appr"], 2)
    D.table(lab["appr_cols"], [[lab["approver"], _cap(p.get("approver") or ""), "", (frozen or {}).get("approved", "")], [lab["owner"], _cap(p.get("owner") or ""), "", ""]],
            [4.2, 5.6, 4.0, 2.7])
    D.para([Run(lab["disclaimer"], i=True, size=8.5, color=GREY)])
    D.page_break()
    D.heading(lab["contents"], 2)
    D.toc(lab["toc"])
    D.para("")
    if w.get("template") == "structure":
        D.para([Run(lab["structure"], b=True, color=RED)])

    sec = 0
    ph_rows = []

    def note_ph(where, text):
        for m in PH_TYPE.finditer(text or ""):
            t = NORM.get(m.group(1), m.group(1))
            ph_rows.append([len(ph_rows) + 1, where, lab["ph"].get(t, t), m.group(2).strip()])

    def blocks(text, key, number_prefix):
        for k, b in enumerate(paragraphs_of(text), 1):
            if "table" in b:
                cols, trs = b["table"]
                n = max(len(cols), 1)
                first = 3.6 if n > 2 else 4.5
                widths = [first] + [(16.5 - first) / (n - 1)] * (n - 1) if n > 1 else [16.5]
                D.table(cols, [r + [""] * (n - len(r)) for r in trs], widths, font_pt=8.5 if n > 3 else 9)
                continue
            D.para(runs_with_placeholders(b["p"]), marks=[bookmark("t", f"{key}_{k}")])
            note_ph(number_prefix, b["p"])

    for key, head in (("purpose", lab["purpose"]), ("scope", lab["scope"])):
        if (p.get(key) or "").strip():
            sec += 1
            D.heading(f"{sec}. {head}", 1)
            blocks(p[key], key, f"{sec}")
    clauses = p.get("clauses") or []
    stm = p.get("statements") or []
    srcs = w.get("sources") or {}
    tr_rows = []

    def statement(s, num):
        tag = f"  ({lab['guideline']})" if s.get("guideline") else ""
        D.para([Run(num + "\t", b=True, color="0B4F6C")] + runs_with_placeholders(s.get("text", "")) + ([Run(tag, i=True, size=8.5, color=GREY)] if tag else []),
               indent=1.2, hanging=1.2, tab=1.2, marks=[bookmark("s", s["id"])])
        note_ph(f"{num} ({s['id']})", s.get("text", ""))
        info = srcs.get(s["id"]) or {}
        basis = lab["basis"].get(info.get("src") or "manual", info.get("src") or "")
        rv = lab["rv"].get(info.get("review") or "", info.get("review") or "")
        if info.get("legal"):
            rv += " · " + lab["rv"]["legal_review_required"]
        tr_rows.append([f"{num} · {s['id']}", lab["mod"].get(s.get("modality"), s.get("modality")), basis, ", ".join(s.get("refs") or []) or "—", rv or "—"])

    for c in clauses:
        sec += 1
        D.heading(f"{sec}. {c.get('heading') or c['id']}", 1)
        blocks(c.get("text") or "", c["id"], str(sec))
        for k, s in enumerate([s for s in stm if s.get("clause") == c["id"]], 1):
            statement(s, f"{sec}.{k}")
    loose = [s for s in stm if not any(c["id"] == s.get("clause") for c in clauses)]
    if loose:
        sec += 1
        D.heading(f"{sec}. {lab['other']}", 1)
        for k, s in enumerate(loose, 1):
            statement(s, f"{sec}.{k}")
    if (p.get("body") or "").strip():
        sec += 1
        D.heading(f"{sec}. {lab['details']}", 1)
        blocks(p["body"], "body", str(sec))

    D.page_break()
    D.heading(lab["app_a"], 1)
    if ph_rows:
        D.table(lab["od_cols"], ph_rows, [0.9, 3.6, 2.6, 9.4], font_pt=8.5)
    else:
        D.para(lab["app_a_none"])
    D.heading(lab["app_b"], 1)
    if tr_rows:
        D.table(lab["tr_cols"], tr_rows, [3.3, 1.9, 3.6, 4.2, 3.5], font_pt=8)
    if w.get("assumptions") or w.get("gaps"):
        D.heading(lab["app_c"], 1)
        if w.get("assumptions"):
            D.heading(lab["assumptions"], 2)
            for a in w["assumptions"]:
                D.bullet(a.get("text", ""))
        if w.get("gaps"):
            D.heading(lab["gaps"], 2)
            for g in w["gaps"]:
                D.bullet(f"{g.get('where') or g.get('clause_id', '')}: {g.get('text', '')}")
    ident = "|".join(["crg-isp", doc.get("ws") or "", p.get("id") or "", "v" + str(p.get("version") or ""), lang,
                      "frozen" if frozen else "draft", content_hash(p)[:16]])
    core = {"title": p.get("title"), "subject": ref, "identifier": ident, "version": p.get("version"),
            "category": ("Information security policy — " + ("approved version" if frozen else "DRAFT")) if lang == "en"
            else ("Politique de sécurité de l’information — " + ("version approuvée" if frozen else "ÉBAUCHE")),
            "keywords": f"isp={p.get('id')}; writer={w.get('code', '')}; library={w.get('library_version', '')}",
            "author": "CyberRiskGuardian", "comments": lab["disclaimer"][:250]}
    return D.build(core, f"{org} — {ref}", lab["frozen"] if frozen else lab["draft"],
                   f"{lab['classification']}: {lab['internal']} · {lab['version']} {p.get('version')}", lab["page"], lab["of"])
