"""Read an edited Word draft back and compare it, clause by clause, with the version it was exported from.

Matching, in order of confidence:
  1. the hidden bookmark `_pb_<clause id>` that every exported clause paragraph carries;
  2. the clause number at the start of the paragraph (e.g. “6.1”), when the bookmark was lost;
  3. anything else in the policy body becomes a proposed *added* paragraph, placed after the preceding clause.
Nothing is applied automatically: the user accepts or rejects each change, and applying creates a new version.
"""
from __future__ import annotations

import difflib
import io
import re
from dataclasses import dataclass, field

import docx
from docx.oxml.ns import qn

from app.export.docx_render import BOOKMARK_PREFIX, bookmark_name
from app.ingestion.extract import ExtractionError, sniff

NUM_RE = re.compile(r"^\s*(\d+(?:\.\d+)+)\s+")
SECTION_RE = re.compile(r"^\s*(\d+)\.\s+\S")
APPENDIX_RE = re.compile(r"^\s*(Appendix|Annexe)\b", re.I)


class ReimportError(Exception):
    pass


@dataclass
class Para:
    text: str
    number: str | None
    bookmarks: list[str]
    section: str | None


@dataclass
class Parsed:
    identifier: str
    policy_id: str
    document_uuid: str
    version_no: int | None
    language: str | None
    paragraphs: list[Para] = field(default_factory=list)


def parse(data: bytes, filename: str) -> Parsed:
    try:
        if sniff(data, filename) != "docx":
            raise ReimportError("Only Word .docx files exported by this application can be re-imported.")
    except ExtractionError as e:
        raise ReimportError(str(e)) from e
    d = docx.Document(io.BytesIO(data))
    ident = (d.core_properties.identifier or "").strip()
    parts = ident.split("|")
    if len(parts) != 4 or not parts[1]:
        raise ReimportError("This Word file has no Policy Builder identifier. Export the draft from the application, edit it in Word, then re-import it.")
    m = re.match(r"v0\.(\d+)$", parts[2])
    out = Parsed(identifier=ident, policy_id=parts[0], document_uuid=parts[1], version_no=int(m.group(1)) if m else None,
                 language=parts[3] if parts[3] in ("en", "fr") else None)
    in_body, section = False, None
    for p in d.paragraphs:
        text = p.text.strip()
        style = (p.style.name or "") if p.style is not None else ""
        if style.startswith("Heading 1") or style.startswith("Titre 1"):
            if APPENDIX_RE.match(text):
                break
            sm = SECTION_RE.match(text)
            if sm:
                in_body, section = True, sm.group(1)
            continue
        if not in_body or style.startswith(("Heading", "Titre", "TOC", "Title")):
            continue
        marks = [b.get(qn("w:name")) for b in p._p.iter(qn("w:bookmarkStart"))]
        marks = [b for b in marks if b and b.startswith(BOOKMARK_PREFIX)]
        nm = NUM_RE.match(text)
        number = nm.group(1) if nm else None
        if nm:
            text = text[nm.end():].strip()
        if not text and not marks:
            continue
        out.paragraphs.append(Para(text=text, number=number, bookmarks=marks, section=section))
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


MODALS = [("must not", r"\bmust not\b|\bshall not\b|\bne doi(?:t|vent) pas\b"),
          ("must", r"\bmust\b|\bshall\b|\bdoi(?:t|vent)\b"),
          ("should", r"\bshould\b|\bdevrai(?:t|ent)\b"),
          ("may", r"\bmay\b|\bpeu(?:t|vent)\b")]


def modality(text: str) -> str:
    low = (text or "").lower()
    for name, pat in MODALS:
        if re.search(pat, low):
            return name
    return "info"


def word_diff(old: str, new: str) -> list[list[str]]:
    a, b = re.findall(r"\S+|\s+", old), re.findall(r"\S+|\s+", new)
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


def compare(base_body: dict, parsed: Parsed) -> tuple[list[dict], list[str]]:
    """Return (changes, warnings). Changes: modified, deleted, added — each pending a user decision."""
    clauses = [(s, c) for s in base_body["sections"] for c in s["clauses"]]
    by_bm = {bookmark_name(c["clause_id"]): c for _, c in clauses}
    by_num = {c["number"]: c for _, c in clauses}
    seen: set[str] = set()
    changes, warnings = [], []
    last_matched: str | None = None
    by_number_count = 0
    added_n = 0
    for para in parsed.paragraphs:
        clause = None
        for bm in para.bookmarks:
            if bm in by_bm and by_bm[bm]["clause_id"] not in seen:
                clause = by_bm[bm]
                break
        if clause is None and para.number and para.number in by_num and by_num[para.number]["clause_id"] not in seen:
            clause = by_num[para.number]
            by_number_count += 1
        if clause is None:
            if not para.text:
                continue
            added_n += 1
            changes.append({"key": f"add:{added_n}", "kind": "added", "clause_id": None, "after": last_matched,
                            "number": para.number, "old": "", "new": para.text, "match": "none", "decision": "pending",
                            "diff": [["ins", para.text]]})
            continue
        seen.add(clause["clause_id"])
        last_matched = clause["clause_id"]
        if clause.get("table"):
            continue  # tables are compared as a whole document element; not edited through re-import
        if _norm(para.text) != _norm(clause["text"]):
            changes.append({"key": f"mod:{clause['clause_id']}", "kind": "modified", "clause_id": clause["clause_id"],
                            "number": clause["number"], "old": clause["text"], "new": para.text,
                            "match": "bookmark" if any(b in by_bm for b in para.bookmarks) else "number",
                            "decision": "pending", "diff": word_diff(clause["text"], para.text),
                            "modality_from": modality(clause["text"]), "modality_to": modality(para.text)})
    for _, c in clauses:
        if c["clause_id"] not in seen and not c.get("table"):
            changes.append({"key": f"del:{c['clause_id']}", "kind": "deleted", "clause_id": c["clause_id"], "number": c["number"],
                            "old": c["text"], "new": "", "match": "missing", "decision": "pending", "diff": [["del", c["text"]]]})
    if by_number_count:
        warnings.append(f"{by_number_count} clause(s) were matched by their number because their hidden marker was removed; check them carefully.")
    return changes, warnings


def apply_changes(base_body: dict, changes: list[dict], code: str) -> tuple[dict, list[str]]:
    """Apply accepted changes to a copy of the body. Returns (new_body, changed clause ids)."""
    import copy
    from app.drafting.composer import placeholders
    body = copy.deepcopy(base_body)
    accepted = [c for c in changes if c["decision"] == "accept"]
    changed: list[str] = []
    index = {c["clause_id"]: (s, c) for s in body["sections"] for c in s["clauses"]}
    for ch in accepted:
        if ch["kind"] == "modified" and ch["clause_id"] in index:
            _, c = index[ch["clause_id"]]
            c["previous_text"], c["text"] = c["text"], ch["new"]
            c["edited"], c["review_status"] = True, "edited_by_user"
            c["placeholders"] = placeholders(ch["new"])
            if ch.get("modality_to") and ch.get("modality_to") != ch.get("modality_from") and ch["modality_to"] != "info":
                c["modality"] = ch["modality_to"]
            changed.append(c["clause_id"])
        elif ch["kind"] == "deleted" and ch["clause_id"] in index:
            s, c = index[ch["clause_id"]]
            s["clauses"] = [x for x in s["clauses"] if x["clause_id"] != ch["clause_id"]]
            changed.append(c["clause_id"])
    existing_u = [int(m.group(1)) for cid in index for m in [re.match(rf"{re.escape(code)}-U(\d+)$", cid)] if m]
    n = max(existing_u, default=0)
    for ch in accepted:
        if ch["kind"] != "added":
            continue
        n += 1
        new_id = f"{code}-U{n:02d}"
        clause = {"clause_id": new_id, "text": ch["new"], "modality": modality(ch["new"]), "source_type": "user_added", "source_ids": [],
                  "framework_refs": [], "review_status": "edited_by_user", "legal_review": False,
                  "placeholders": placeholders(ch["new"]), "edited": True}
        target = None
        if ch.get("after"):
            for s in body["sections"]:
                ids = [x["clause_id"] for x in s["clauses"]]
                if ch["after"] in ids:
                    s["clauses"].insert(ids.index(ch["after"]) + 1, clause)
                    target = s
                    break
        if target is None:
            body["sections"][0]["clauses"].append(clause)
        changed.append(new_id)
        ch["new_clause_id"] = new_id
    body["sections"] = [s for s in body["sections"] if s["clauses"]]
    for si, s in enumerate(body["sections"], 1):
        s["number"] = str(si)
        for ci, c in enumerate(s["clauses"], 1):
            c["number"] = f"{si}.{ci}"
    return body, changed
