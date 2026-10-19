"""Re-import of a policy edited in Word: what changed, statement by statement — proposals only.

The Word file must be one exported from ISP management (its properties name the workspace, the policy and
the version). Statements and text paragraphs are matched by their hidden bookmark, then by their number when
an editor removed the bookmark. The result is a list of changes, each waiting for a person to accept or
reject it; CyberRiskGuardian applies the accepted ones to the working draft only — an approved or published
version is frozen and never changes.
© 2026 Marc-André Léger. CC BY-NC 4.0
"""
from __future__ import annotations

import difflib
import re

from .ooxml import NotAWordFile, bookmark, read
from .render import content_hash, paragraphs_of

NUM_RE = re.compile(r"^\s*(\d+(?:\.\d+)+[a-z]?)\s+")
SEC_RE = re.compile(r"^\s*(\d+)\.\s+\S")
APPX_RE = re.compile(r"^\s*(Appendix|Annexe)\b", re.I)
MODALS = [("mustnot", r"\bmust not\b|\bshall not\b|\bne (?:doi(?:t|vent)|peu(?:t|vent)) pas\b|\bil est interdit\b|\bsont interdit"),
          ("must", r"\bmust\b|\bshall\b|\bdoi(?:t|vent)\b|\bsont tenus\b"),
          ("should", r"\bshould\b|\bdevrai(?:t|ent)\b|\bil est recommandé\b"),
          ("may", r"\bmay\b|\bpeu(?:t|vent)\b")]


class ReimportError(Exception):
    pass


def modality(text: str) -> str | None:
    low = (text or "").lower()
    for name, pat in MODALS:
        if re.search(pat, low):
            return name
    return None


def word_diff(old: str, new: str) -> list[list[str]]:
    a, b = re.findall(r"\S+|\s+", old or ""), re.findall(r"\S+|\s+", new or "")
    ops = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            ops.append(["eq", "".join(a[i1:i2])])
        else:
            if i2 > i1:
                ops.append(["del", "".join(a[i1:i2])])
            if j2 > j1:
                ops.append(["ins", "".join(b[j1:j2])])
    return ops


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def _units(p: dict):
    """The export order of the policy: sections, their text paragraphs and statements, with numbers."""
    secs, sec = [], 0
    for key in ("purpose", "scope"):
        if (p.get(key) or "").strip():
            sec += 1
            secs.append({"no": str(sec), "key": key, "texts": [b["p"] for b in paragraphs_of(p[key]) if "p" in b], "stmts": []})
    stm = p.get("statements") or []
    clauses = p.get("clauses") or []
    for c in clauses:
        sec += 1
        secs.append({"no": str(sec), "key": c["id"], "texts": [b["p"] for b in paragraphs_of(c.get("text") or "") if "p" in b],
                     "stmts": [s for s in stm if s.get("clause") == c["id"]]})
    loose = [s for s in stm if not any(c["id"] == s.get("clause") for c in clauses)]
    if loose:
        sec += 1
        secs.append({"no": str(sec), "key": "", "texts": [], "stmts": loose})
    if (p.get("body") or "").strip():
        sec += 1
        secs.append({"no": str(sec), "key": "body", "texts": [b["p"] for b in paragraphs_of(p["body"]) if "p" in b], "stmts": []})
    return secs


def compare(data: bytes, policy: dict, ws_id: str = "") -> dict:
    try:
        doc = read(data)
    except NotAWordFile as e:
        raise ReimportError(str(e)) from e
    ident = doc["core"].get("identifier", "")
    parts = ident.split("|")
    if len(parts) < 7 or parts[0] != "crg-isp":
        raise ReimportError("This Word file was not exported from ISP management. Export the policy with “Word (.docx)”, edit it in Word, then re-import it.")
    _, f_ws, f_pid, f_ver, f_lang, f_state, f_hash = parts[:7]
    if f_pid != policy.get("id"):
        raise ReimportError(f"This file belongs to policy {f_pid}, not to {policy.get('id')}.")
    if ws_id and f_ws and f_ws != ws_id:
        raise ReimportError("This file was exported from another workspace.")
    warnings = []
    if f_state == "frozen":
        warnings.append({"code": "frozen", "en": "The file is a copy of an approved version; the changes are compared with the current working draft.",
                         "fr": "Le fichier est une copie d’une version approuvée; les modifications sont comparées à l’ébauche de travail actuelle."})
    if f_ver != "v" + str(policy.get("version")):
        warnings.append({"code": "version", "en": f"The file was exported from {f_ver}; the working draft is now v{policy.get('version')}.",
                         "fr": f"Le fichier a été exporté de la {f_ver}; l’ébauche de travail est maintenant la v{policy.get('version')}."})
    if f_hash and f_hash != content_hash(policy)[:16]:
        warnings.append({"code": "changed", "en": "The draft changed in CyberRiskGuardian after this file was exported. Every difference below is shown against the current draft — check that you are not undoing someone else’s change.",
                         "fr": "L’ébauche a changé dans CyberRiskGuardian après l’exportation de ce fichier. Chaque différence ci-dessous est comparée à l’ébauche actuelle — vérifiez que vous n’annulez pas la modification de quelqu’un d’autre."})
    secs = _units(policy)
    by_mark, by_num = {}, {}
    for s in secs:
        for k, t in enumerate(s["texts"], 1):
            by_mark[bookmark("t", f"{s['key']}_{k}")] = ("text", s, k, t)
        for k, st in enumerate(s["stmts"], 1):
            u = ("stmt", s, k, st)
            by_mark[bookmark("s", st["id"])] = u
            by_num[f"{s['no']}.{k}"] = u
    sec_by_no = {s["no"]: s for s in secs}
    seen, changes, added = set(), [], 0
    in_body, cur_sec, last = False, None, None
    matched_by_number = 0
    for para in doc["paragraphs"]:
        text, style = para["text"].strip(), para["style"] or ""
        if style.startswith("Heading1") or style.lower().startswith(("heading1", "titre1")):
            if APPX_RE.match(text):
                break
            m = SEC_RE.match(text)
            if m:
                in_body, cur_sec, last = True, sec_by_no.get(m.group(1)), None
            continue
        if not in_body or style.startswith(("Heading", "Title", "TOC")):
            continue
        unit = next((by_mark[m] for m in para["marks"] if m in by_mark and m not in seen), None)
        nm = NUM_RE.match(text)
        num = nm.group(1) if nm else None
        if nm:
            text = text[nm.end():].strip()
        text = re.sub(r"\s*\((guideline — not binding|ligne directrice — non contraignante)\)\s*$", "", text)
        if unit is None and num and num in by_num:
            mk = bookmark("s", by_num[num][3]["id"])
            if mk not in seen:
                unit = by_num[num]
                matched_by_number += 1
        if unit is None:
            if not text:
                continue
            added += 1
            mod = modality(text)
            changes.append({"key": f"add:{added}", "kind": "added_statement" if mod else "added_text", "section": (cur_sec or {}).get("key", ""),
                            "after": last, "new": text, "old": "", "modality_to": mod, "diff": [["ins", text]], "decision": "pending"})
            continue
        kind, s, k, obj = unit
        mk = bookmark("s", obj["id"]) if kind == "stmt" else bookmark("t", f"{s['key']}_{k}")
        seen.add(mk)
        if kind == "stmt":
            last = obj["id"]
            if _norm(text) != _norm(obj.get("text")):
                mt = modality(text)
                changes.append({"key": "mod:" + obj["id"], "kind": "modified", "statement": obj["id"], "old": obj.get("text", ""), "new": text,
                                "modality_from": obj.get("modality"), "modality_to": mt if mt and mt != obj.get("modality") else None,
                                "match": "bookmark" if mk in para["marks"] else "number", "diff": word_diff(obj.get("text", ""), text), "decision": "pending"})
        else:
            last = last or f"text:{s['key']}"
            if _norm(text) != _norm(obj):
                changes.append({"key": f"txt:{s['key']}:{k}", "kind": "text", "section": s["key"], "index": k, "old": obj, "new": text,
                                "diff": word_diff(obj, text), "decision": "pending"})
    for s in secs:
        for k, t in enumerate(s["texts"], 1):
            if bookmark("t", f"{s['key']}_{k}") not in seen:
                changes.append({"key": f"txt:{s['key']}:{k}", "kind": "text", "section": s["key"], "index": k, "old": t, "new": "",
                                "diff": [["del", t]], "decision": "pending"})
        for st in s["stmts"]:
            if bookmark("s", st["id"]) not in seen:
                changes.append({"key": "del:" + st["id"], "kind": "deleted", "statement": st["id"], "old": st.get("text", ""), "new": "",
                                "diff": [["del", st.get("text", "")]], "decision": "pending"})
    if matched_by_number:
        warnings.append({"code": "number", "en": f"{matched_by_number} statement(s) were matched by their number because their hidden marker was removed; check them carefully.",
                         "fr": f"{matched_by_number} énoncé(s) ont été associés par leur numéro, car leur marqueur caché a été supprimé; vérifiez-les avec soin."})
    return {"identifier": ident, "policy": f_pid, "version": f_ver, "language": f_lang, "changes": changes, "warnings": warnings,
            "summary": {k: sum(1 for c in changes if c["kind"] == k) for k in ("modified", "deleted", "added_statement", "added_text", "text")}}
