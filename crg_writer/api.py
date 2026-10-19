"""The Writer as the CyberRiskGuardian helper serves it: one function per operation, JSON in, JSON out.

Stateless. Everything the person entered lives in their CyberRiskGuardian workspace (ws.isp.writer) and
is sent with each request to the helper on 127.0.0.1; nothing is stored here and nothing leaves the
computer. Binary files (Word documents, scanned PDFs) travel as base64.
© 2026 Marc-André Léger. CC BY-NC 4.0
"""
from __future__ import annotations

import base64
import re

from . import NAME, VERSION
from . import evidence, ocr as OCR, quality, reimport as RI, render
from .catalogue import BY_CODE as CAT, DECISIONS, DECISIONS_BY_POLICY, decision_applies, recommend
from .composer import Context, compose, document_summary, placeholders, PH_RE
from .crgo import CRGO_RELEASE, crg_refs, profile_proposal
from .engine import Profile, governance_observations, progress, sections_for, visible_questions
from .isp_map import to_isp
from .library import LIBRARY, LIBRARY_VERSION, referenced_decisions
from .questions import BY_CODE as QBY, QUESTIONNAIRE_VERSION
from .rulesets import RULESET_DATE, RULESET_VERSION, candidates

DEC_BY = {d["code"]: d for d in DECISIONS}
MAX_B64 = 90 * 1024 * 1024


class ApiError(Exception):
    def __init__(self, en, fr=None, status=400):
        super().__init__(en)
        self.en, self.fr, self.status = en, fr or en, status


def _lang(b):
    return "fr" if b.get("lang") == "fr" else "en"


def _profile(b, lang=None):
    ans = b.get("answers") or {}
    clean = {k: {"value": v.get("value"), "status": v.get("status", "answered")} for k, v in ans.items() if isinstance(v, dict)}
    return Profile(clean, lang or _lang(b))


def _qview(q, a, lang):
    return {"code": q["code"], "section": q.get("section", "decisions"), "type": q["type"], "required": q.get("required", False),
            "label": q["label"][lang], "help": q.get("help", {}).get(lang, ""), "why": q.get("why", {}).get(lang, ""),
            "options": [{"value": o["value"], "label": o[lang]} for o in q.get("options", [])],
            "suggested": q.get("suggested"), "legal": bool(q.get("legal_review") or q.get("legal")), "policy": q.get("policy"),
            "answer": a}


def _bytes(b, key="data"):
    s = b.get(key) or ""
    if len(s) > MAX_B64:
        raise ApiError("The file is too large.", "Le fichier est trop volumineux.", 413)
    try:
        return base64.b64decode(s.split(",", 1)[-1], validate=False)
    except Exception as e:                                                  # noqa: BLE001
        raise ApiError("The file could not be read.", "Le fichier n’a pas pu être lu.") from e


# ---------------------------------------------------------------- operations
def op_meta(b):
    return {"name": NAME, "version": VERSION, "library": LIBRARY_VERSION, "questionnaire": QUESTIONNAIRE_VERSION,
            "ruleset": RULESET_VERSION, "ruleset_date": RULESET_DATE, "crgo": CRGO_RELEASE, "documents": len(CAT),
            "clauses": sum(len(s["clauses"]) for v in LIBRARY.values() for s in v), "ocr": OCR.info()}


def op_interview(b):
    lang, mode = _lang(b), b.get("mode") or "express"
    p = _profile(b)
    qs = [_qview(q, p.answers.get(q["code"]), lang) for q in visible_questions(p, mode)]
    return {"sections": sections_for(p, mode, lang), "questions": qs, "progress": progress(p, mode),
            "observations": governance_observations(p, lang), "org_name": p.org_name, "prefix": p.doc_prefix}


def op_answer(b):
    """Validate and normalize one answer: {code, value, status}."""
    code, status, value = b.get("code"), b.get("status") or "answered", b.get("value")
    q = QBY.get(code) or DEC_BY.get(code)
    if not q:
        raise ApiError("Unknown question.", "Question inconnue.", 404)
    if status in ("unknown", "not_applicable", "decide_later"):
        return {"code": code, "value": None, "status": status}
    if status != "answered":
        raise ApiError("Invalid status.", "Statut non valide.")
    t, allowed = q["type"], {o["value"] for o in q.get("options", [])}
    if t == "select":
        if value not in allowed:
            raise ApiError("Choose one of the options.", "Choisissez une des options.")
    elif t == "multi":
        if not isinstance(value, list) or not value or any(v not in allowed for v in value):
            raise ApiError("Select one or more options.", "Sélectionnez une ou plusieurs options.")
        if "none" in value and len(value) > 1:
            value = [v for v in value if v != "none"]
    else:
        if not isinstance(value, str) or not value.strip():
            raise ApiError("Empty answer: choose Unknown or Decide later instead.", "Réponse vide : choisissez plutôt Inconnu ou À décider plus tard.")
        value = value.strip()
        if len(value) > (2000 if t == "textarea" else 300):
            raise ApiError("The answer is too long.", "La réponse est trop longue.")
    return {"code": code, "value": value, "status": "answered"}


def _library_refs(code):
    refs = []
    for s in LIBRARY.get(code, []):
        for c in s["clauses"]:
            for r in crg_refs(c.get("refs", [])):
                if r not in refs:
                    refs.append(r)
    return refs


def op_catalogue(b):
    lang = _lang(b)
    items = recommend(_profile(b), lang)
    for x in items:
        x["refs"] = _library_refs(x["code"])
    return {"items": items, "small_org": _profile(b).small}


def op_legal(b):
    lang = _lang(b)
    p = _profile(b)
    return {"candidates": candidates(p, lang, b.get("applicability") or {}, b.get("crgo")), "proposal": profile_proposal(p),
            "ruleset": RULESET_VERSION, "ruleset_date": RULESET_DATE, "crgo": CRGO_RELEASE}


def op_decisions(b):
    lang = _lang(b)
    p = _profile(b)
    selected = [c for c in CAT if c in set(b.get("selection") or [])]
    out, shown = [], set()
    for code in selected:
        own = [d for d in DECISIONS_BY_POLICY.get(code, []) if decision_applies(d, p)]
        borrowed = [DEC_BY[c] for c in referenced_decisions(code) if c in DEC_BY and DEC_BY[c] not in own
                    and DEC_BY[c]["policy"] not in selected and decision_applies(DEC_BY[c], p)]
        items = [_qview(d, p.answers.get(d["code"]), lang) for d in own + borrowed if d["code"] not in shown]
        shown.update(i["code"] for i in items)
        if items:
            out.append({"policy": code, "title": CAT[code]["title"][lang], "questions": items})
    return {"groups": out}


def op_compose(b):
    selected = [c for c in CAT if c in set(b.get("selection") or [])]
    if not selected:
        raise ApiError("Select documents in the Library step first.", "Sélectionnez d’abord des documents à l’étape Bibliothèque.", 409)
    targets = [c for c in (b.get("codes") or selected) if c in selected]
    langs = [x for x in (b.get("languages") or ["en"]) if x in ("en", "fr")] or ["en"]
    obligations = {k: v for k, v in (b.get("applicability") or {}).items() if isinstance(v, dict)}
    versions = b.get("versions") or {}
    docs, bodies, used = [], {}, {}
    for code in targets:
        inputs = set()
        for lang in langs:
            p = _profile(b, lang)
            cand = {c["code"] for c in candidates(p, lang, obligations, b.get("crgo")) if c["triggered"]}
            cx = Context(p, lang, selected, obligations, cand, version_no=int(versions.get(code, 1) or 1))
            body = compose(code, cx)
            bodies.setdefault(code, {})[lang] = body
            inputs |= cx.inputs_used
            isp = to_isp(body)
            gov10 = p.value("GOV-10")
            isp["reviewMonths"] = int(gov10) if gov10 and str(gov10).isdigit() else 12
            docs.append({"code": code, "lang": lang, "isp": isp, "summary": document_summary(body)})
        used[code] = sorted(inputs)
    issues = quality.check(bodies, selected, b.get("facts"), b.get("refs"))
    return {"documents": docs, "issues": issues, "inputs": used, "library": LIBRARY_VERSION}


def op_facts(b):
    return evidence.extract(b.get("docs") or [], b.get("org"), b.get("crown"), _lang(b))


def op_ground(b):
    """Keep only AI-proposed facts whose quote is verbatim in the text that was sent and whose type is allowed."""
    allowed = set(b.get("allowed") or [])
    text = b.get("text") or ""
    out = []
    for f in (b.get("facts") or [])[:60]:
        if not isinstance(f, dict) or f.get("fact_type") not in allowed:
            continue
        q = str(f.get("quote", ""))[:300]
        if not q or q not in text:
            continue
        out.append({"fact_type": f["fact_type"], "value": f.get("value"), "quote": q,
                    "confidence": f.get("confidence") if f.get("confidence") in ("high", "medium", "low") else "low"})
    return {"facts": out}


NUM_RE = re.compile(r"\d+")
MODALS = {"en": [r"\bmust not\b", r"\bmust\b", r"\bshould\b", r"\bmay\b"],
          "fr": [r"\bne doi(?:t|vent) pas\b", r"\bdoi(?:t|vent)\b", r"\bdevrai(?:t|ent)\b", r"\bpeu(?:t|vent)\b"]}


def validate_rewording(original: str, new: str, context: str, lang: str):
    if not new or not new.strip():
        return "empty"
    if sorted(m.group(0) for m in PH_RE.finditer(original)) != sorted(m.group(0) for m in PH_RE.finditer(new)):
        return "placeholders changed"
    extra = set(NUM_RE.findall(new)) - (set(NUM_RE.findall(original)) | set(NUM_RE.findall(context)))
    if extra:
        return "new numbers introduced: " + ", ".join(sorted(extra))
    if not 0.5 <= len(new) / max(len(original), 1) <= 1.8:
        return "length changed too much"
    for pat in MODALS.get(lang, []):
        if bool(re.search(pat, original, re.I)) != bool(re.search(pat, new, re.I)):
            return "normative strength changed"
    return None


def op_validate_rewording(b):
    """{items:[{id, text}], proposed:{id: text}, context, lang} → accepted and rejected rewordings."""
    lang, ctx = _lang(b), b.get("context") or ""
    items = {i["id"]: i["text"] for i in b.get("items") or []}
    acc, rej = [], []
    for k, new in (b.get("proposed") or {}).items():
        if k not in items:
            rej.append({"id": str(k)[:80], "reason": "unexpected id"})
            continue
        why = validate_rewording(items[k], str(new), ctx, lang)
        if why:
            rej.append({"id": k, "reason": why})
        elif new.strip() != items[k].strip():
            acc.append({"id": k, "old": items[k], "new": new.strip(), "diff": RI.word_diff(items[k], new.strip())})
    for k in items:
        if k not in (b.get("proposed") or {}):
            rej.append({"id": k, "reason": "missing from the answer"})
    return {"accepted": acc, "rejected": rej}


def op_docx(b):
    data = render.render(b.get("doc") or {})
    return {"name": b.get("name") or "policy.docx", "data": base64.b64encode(data).decode(), "bytes": len(data)}


def op_reimport(b):
    try:
        return RI.compare(_bytes(b), b.get("policy") or {}, b.get("ws") or "")
    except RI.ReimportError as e:
        raise ApiError(str(e), str(e), 422) from e


def op_ocr(b):
    try:
        return OCR.ocr(_bytes(b), b.get("name") or "", b.get("pages"))
    except OCR.OCRUnavailable as e:
        raise ApiError(str(e), str(e), 501) from e


def op_placeholders(b):
    return {"placeholders": placeholders(b.get("text") or "")}


OPS = {"meta": op_meta, "interview": op_interview, "answer": op_answer, "catalogue": op_catalogue, "legal": op_legal,
       "decisions": op_decisions, "compose": op_compose, "facts": op_facts, "ground": op_ground,
       "validate_rewording": op_validate_rewording, "docx": op_docx, "reimport": op_reimport, "ocr": op_ocr,
       "placeholders": op_placeholders}


def handle(op: str, body: dict) -> tuple[int, dict]:
    fn = OPS.get(op)
    if not fn:
        return 404, {"error": "Unknown Writer operation.", "error_fr": "Opération inconnue du rédacteur."}
    try:
        return 200, fn(body or {})
    except ApiError as e:
        return e.status, {"error": e.en, "error_fr": e.fr}
    except Exception as e:                                                  # noqa: BLE001
        return 500, {"error": f"The Writer could not complete {op}: {type(e).__name__}: {e}", "error_fr": f"Le rédacteur n’a pas pu terminer {op} : {type(e).__name__} : {e}"}
