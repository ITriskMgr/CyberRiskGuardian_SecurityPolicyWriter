"""Application services: interview, evidence, applicability, selection, generation and quality checks.
All functions take an already tenant-checked Project."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import config
from app.catalogue.catalogue import BY_CODE as CAT, DECISIONS, DECISIONS_BY_POLICY, decision_applies, recommend
from app.catalogue.rulesets import RULESET_VERSION, candidates
from app.drafting import ai
from app.drafting.composer import Context, compose, document_summary, placeholders
from app.ingestion.extract import ExtractionError, extract, sanitize_filename
from app.ingestion.facts import ALLOWED_AI_FACT_TYPES, extract_rule_facts
from app.models import (Answer, ApplicabilityDecision, EvidenceSegment, Issue, OrganizationFact, PolicyClause,
                        PolicyDocument, PolicyVersion, Project, SourceDocument)
from app.questionnaire.engine import Profile, governance_observations, progress, sections_for, visible_questions
from app.questionnaire.questions import BY_CODE as QBY, QUESTIONNAIRE_VERSION, SECTION_TITLES
from app.security import Ctx, audit, decrypt, encrypt

WORKFLOW = ["PROJECT_CREATED", "DISCOVERY_IN_PROGRESS", "EVIDENCE_REVIEW", "APPLICABILITY_REVIEW", "LIBRARY_CONFIRMED",
            "OUTLINE_REVIEW", "DRAFT_GENERATED"]
DEC_BY = {d["code"]: d for d in DECISIONS}
STATUSES = {"answered", "unknown", "not_applicable", "decide_later"}


def advance(project: Project, state: str) -> None:
    if WORKFLOW.index(state) > WORKFLOW.index(project.workflow_state if project.workflow_state in WORKFLOW else "PROJECT_CREATED"):
        project.workflow_state = state


# ------------------------------------------------------------------ profile
def load_profile(db: Session, project: Project, lang: str = "en") -> Profile:
    rows = db.scalars(select(Answer).where(Answer.project_id == project.id)).all()
    return Profile({a.question_code: {"value": a.value, "status": a.status, "source": a.source} for a in rows}, lang)


def question_def(code: str) -> dict | None:
    return QBY.get(code) or DEC_BY.get(code)


def validate_value(q: dict, value):
    t = q["type"]
    allowed = {o["value"] for o in q.get("options", [])}
    if t == "select":
        if value not in allowed:
            raise HTTPException(422, "Value is not one of the allowed options.")
    elif t == "multi":
        if not isinstance(value, list) or not value or any(v not in allowed for v in value):
            raise HTTPException(422, "Select one or more allowed options.")
        if "none" in value and len(value) > 1:
            value = [v for v in value if v != "none"]
    elif t in ("text", "textarea", "date"):
        if not isinstance(value, str):
            raise HTTPException(422, "Text expected.")
        value = value.strip()
        if not value:
            raise HTTPException(422, "Empty answer: choose Unknown or Decide later instead.")
        if len(value) > (2000 if t == "textarea" else 300):
            raise HTTPException(422, "Answer is too long.")
    return value


def set_answer(db: Session, ctx: Ctx, project: Project, code: str, value, status: str,
               source: str = "user", source_ref: str | None = None) -> Answer:
    q = question_def(code)
    if not q:
        raise HTTPException(404, "Unknown question.")
    if status not in STATUSES:
        raise HTTPException(422, "Invalid answer status.")
    if status == "answered":
        value = validate_value(q, value)
    else:
        value = None
        if q.get("required") and status == "not_applicable":
            raise HTTPException(422, "This question cannot be marked not applicable.")
    a = db.scalar(select(Answer).where(Answer.project_id == project.id, Answer.question_code == code))
    before = a.value if a else None
    before_status = a.status if a else None
    if not a:
        a = Answer(workspace_id=project.workspace_id, project_id=project.id, question_code=code, author_id=ctx.user.id)
        db.add(a)
    a.value, a.status, a.source, a.source_ref, a.author_id = value, status, source, source_ref, ctx.user.id
    if code == "ORG-01B" or (code == "ORG-01" and not project.org_display_name):
        project.org_display_name = value or project.org_display_name
    if code == "ORG-10" and value in ("en", "fr", "both"):
        project.doc_language = value
    changed = (before != value) or (before_status != status)
    if changed:
        _mark_stale(db, project, code)
        audit(db, ctx, "answer.set", "answer", code, project.id, status=status, source=source)
    advance(project, "DISCOVERY_IN_PROGRESS")
    project.lock_version += 1
    return a


def _mark_stale(db: Session, project: Project, code: str) -> None:
    docs = db.scalars(select(PolicyDocument).where(PolicyDocument.project_id == project.id, PolicyDocument.current_version > 0)).all()
    for d in docs:
        v = db.scalar(select(PolicyVersion).where(PolicyVersion.document_id == d.id, PolicyVersion.version_no == d.current_version))
        if v and (code in (v.inputs_used or []) or code in ("ORG-01", "ORG-01B", "ORG-13", "ORG-13B", "DEC-EISP-COMMITTEE")):
            d.stale = True
            reason = f"Answer {code} changed after version {d.current_version}."
            d.stale_reason = reason if not d.stale_reason else (d.stale_reason + " " + reason)[-1000:]


def interview(db: Session, project: Project, lang: str) -> dict:
    p = load_profile(db, project, lang)
    qs = []
    for q in visible_questions(p, project.mode):
        a = p.answers.get(q["code"])
        qs.append(_qview(q, a, lang))
    return {"sections": sections_for(p, project.mode, lang), "questions": qs, "progress": progress(p, project.mode),
            "observations": governance_observations(p, lang), "questionnaire_version": QUESTIONNAIRE_VERSION}


def _qview(q: dict, a: dict | None, lang: str) -> dict:
    return {"code": q["code"], "section": q["section"], "type": q["type"], "required": q.get("required", False),
            "label": q["label"][lang], "help": q["help"][lang], "why": q["why"][lang],
            "options": [{"value": o["value"], "label": o[lang]} for o in q.get("options", [])],
            "suggested": q.get("suggested"), "legal_review": q.get("legal_review", False),
            "answer": a}


# ------------------------------------------------------------------ evidence
CATEGORIES = ["existing_policy", "risk_assessment", "audit_report", "contract", "org_chart", "inventory", "privacy",
              "strategy", "other"]


def ingest(db: Session, ctx: Ctx, project: Project, filename: str, data: bytes, category: str) -> SourceDocument:
    s = config.settings
    if len(data) > s.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {s.max_upload_mb} MB.")
    if not data:
        raise HTTPException(422, "Empty file.")
    name = sanitize_filename(filename)
    sha = hashlib.sha256(data).hexdigest()
    dup = db.scalar(select(SourceDocument).where(SourceDocument.project_id == project.id, SourceDocument.sha256 == sha))
    if dup:
        raise HTTPException(409, f"This file was already uploaded as “{dup.filename}”.")
    try:
        ex = extract(data, name)
    except ExtractionError as e:
        audit(db, ctx, "source.rejected", "source", None, project.id, reason=str(e), filename=name)
        db.commit()
        raise HTTPException(422, str(e))
    folder = s.blob_dir / project.workspace_id / project.id
    folder.mkdir(parents=True, exist_ok=True)
    doc = SourceDocument(workspace_id=project.workspace_id, project_id=project.id, filename=name, sha256=sha,
                         mime=ex.mime, size=len(data), category=category if category in CATEGORIES else "other",
                         title=ex.title[:300], doc_date=ex.doc_date, ingestion_state="extracted", blob_path="",
                         warnings=ex.warnings, uploaded_by=ctx.user.id)
    db.add(doc)
    db.flush()
    path = folder / f"{doc.id}.bin"
    path.write_bytes(encrypt(data))
    doc.blob_path = str(path)
    allow_ai = project.ai_on_sources and config.settings.ai_available
    ai_meta = None
    for i, seg in enumerate(ex.segments):
        es = EvidenceSegment(workspace_id=project.workspace_id, project_id=project.id, source_id=doc.id, ordinal=i,
                             locator=seg.locator[:200], text_enc=encrypt(seg.text.encode()), injection_flag=seg.injection)
        db.add(es)
        db.flush()
        facts = extract_rule_facts(seg.text)
        if allow_ai and not seg.injection:
            try:
                ai_facts, ai_meta = ai.extract_facts_ai(seg.text, ALLOWED_AI_FACT_TYPES)
                for f in ai_facts:
                    f["label"] = f["fact_type"]
                    f["extractor"] = "ai"
                facts += ai_facts
            except ai.AIError:
                doc.warnings = list(doc.warnings) + ["AI extraction failed for one passage; rule-based extraction was kept."]
        for f in facts:
            db.add(OrganizationFact(workspace_id=project.workspace_id, project_id=project.id, source_id=doc.id,
                                    segment_id=es.id, fact_type=f["fact_type"], label=f["label"], value=f["value"],
                                    quote=f["quote"], locator=seg.locator[:200], confidence=f["confidence"],
                                    extractor=f.get("extractor", "rules-v1")))
    db.flush()
    recompute_conflicts(db, project)
    advance(project, "EVIDENCE_REVIEW")
    audit(db, ctx, "source.uploaded", "source", doc.id, project.id, filename=name, sha256=sha, size=len(data),
          segments=len(ex.segments), injection_flags=sum(1 for x in ex.segments if x.injection),
          ai_extraction=bool(allow_ai), ai_meta=ai_meta)
    return doc


def recompute_conflicts(db: Session, project: Project) -> None:
    facts = db.scalars(select(OrganizationFact).where(OrganizationFact.project_id == project.id,
                                                      OrganizationFact.state != "rejected")).all()
    by_type: dict[str, list[OrganizationFact]] = {}
    for f in facts:
        by_type.setdefault(f.fact_type, []).append(f)
    for t, group in by_type.items():
        values = {json.dumps(f.value, sort_keys=True) for f in group}
        multi_ok = t in ("GOV-04", "ORG-13")
        conflict = len(values) > 1 and not multi_ok
        for f in group:
            f.conflict_group = f"CONFLICT-{t}" if conflict else None


def facts_view(db: Session, project: Project, lang: str) -> list[dict]:
    p = load_profile(db, project, lang)
    srcs = {s.id: s for s in db.scalars(select(SourceDocument).where(SourceDocument.project_id == project.id)).all()}
    out = []
    for f in db.scalars(select(OrganizationFact).where(OrganizationFact.project_id == project.id)
                        .order_by(OrganizationFact.fact_type, OrganizationFact.created_at)).all():
        q = question_def(f.fact_type)
        cur = p.answers.get(f.fact_type)
        val_label = _value_label(q, f.value, lang)
        cur_label = _value_label(q, cur["value"], lang) if cur and cur["status"] == "answered" else None
        differs = cur_label is not None and cur["value"] != f.value and not (isinstance(cur["value"], list) and isinstance(f.value, list) and set(f.value) <= set(cur["value"]))
        src = srcs.get(f.source_id)
        out.append({"id": f.id, "fact_type": f.fact_type, "question": q["label"][lang] if q else f.label,
                    "value": f.value, "value_label": val_label, "quote": f.quote, "locator": f.locator,
                    "source": src.filename if src else "", "source_date": src.doc_date if src else "", "source_id": f.source_id,
                    "confidence": f.confidence, "extractor": f.extractor, "state": f.state,
                    "conflict_group": f.conflict_group, "current_answer": cur_label, "differs_from_answer": differs,
                    "applies_to_answer": q is not None})
    return out


def _value_label(q, value, lang):
    if value is None:
        return None
    if not q:
        return str(value)
    opts = {o["value"]: o[lang] for o in q.get("options", [])}
    if isinstance(value, list):
        return ", ".join(opts.get(v, str(v)) for v in value)
    return opts.get(value, str(value))


def decide_fact(db: Session, ctx: Ctx, project: Project, fact: OrganizationFact, action: str) -> None:
    if action not in ("confirm", "reject"):
        raise HTTPException(422, "Action must be confirm or reject.")
    fact.state = "confirmed" if action == "confirm" else "rejected"
    fact.decided_by = ctx.user.id
    if action == "confirm":
        q = question_def(fact.fact_type)
        if q:
            value = fact.value
            if q["type"] == "multi":
                cur = db.scalar(select(Answer).where(Answer.project_id == project.id, Answer.question_code == fact.fact_type))
                base = cur.value if cur and cur.status == "answered" and isinstance(cur.value, list) else []
                value = sorted(set(base) | set(value if isinstance(value, list) else [value]))
            set_answer(db, ctx, project, fact.fact_type, value, "answered", source="document", source_ref=fact.id)
        # a user choice resolves the conflict: other proposals with a different value are set aside
        if fact.conflict_group:
            for other in db.scalars(select(OrganizationFact).where(OrganizationFact.project_id == project.id,
                                                                    OrganizationFact.conflict_group == fact.conflict_group,
                                                                    OrganizationFact.id != fact.id)).all():
                if other.value != fact.value and other.state == "proposed":
                    other.state = "rejected"
                    other.decided_by = ctx.user.id
    recompute_conflicts(db, project)
    audit(db, ctx, f"fact.{action}", "fact", fact.id, project.id, fact_type=fact.fact_type)


def delete_source(db: Session, ctx: Ctx, project: Project, src: SourceDocument) -> None:
    from pathlib import Path
    Path(src.blob_path).unlink(missing_ok=True)
    db.execute(delete(OrganizationFact).where(OrganizationFact.source_id == src.id))
    db.execute(delete(EvidenceSegment).where(EvidenceSegment.source_id == src.id))
    audit(db, ctx, "source.deleted", "source", src.id, project.id, filename=src.filename, sha256=src.sha256)
    db.delete(src)
    db.flush()
    recompute_conflicts(db, project)


def segments_view(db: Session, src: SourceDocument) -> list[dict]:
    rows = db.scalars(select(EvidenceSegment).where(EvidenceSegment.source_id == src.id).order_by(EvidenceSegment.ordinal)).all()
    return [{"locator": r.locator, "text": decrypt(r.text_enc).decode(), "injection": r.injection_flag} for r in rows]


# ------------------------------------------------------------------ applicability
def applicability_decisions(db: Session, project: Project) -> dict[str, dict]:
    out = {}
    for d in db.scalars(select(ApplicabilityDecision).where(ApplicabilityDecision.project_id == project.id)).all():
        out[d.obligation_code] = {"status": d.status, "rationale": d.rationale, "reviewer_name": d.reviewer_name,
                                  "decided_at": d.updated_at.isoformat() if d.updated_at else None,
                                  "ruleset_version": d.ruleset_version}
    return out


def applicability(db: Session, project: Project, lang: str) -> list[dict]:
    p = load_profile(db, project, lang)
    return candidates(p, lang, applicability_decisions(db, project))


def decide_applicability(db: Session, ctx: Ctx, project: Project, code: str, status: str, rationale: str, reviewer: str):
    from app.catalogue.rulesets import BY_CODE as OBL
    if code not in OBL:
        raise HTTPException(404, "Unknown obligation.")
    if status not in ("applies", "not_applicable", "needs_legal_review", "candidate"):
        raise HTTPException(422, "Invalid status.")
    if status != "candidate" and (not reviewer.strip() or not rationale.strip()):
        raise HTTPException(422, "A reviewer name and a rationale are required.")
    row = db.scalar(select(ApplicabilityDecision).where(ApplicabilityDecision.project_id == project.id,
                                                        ApplicabilityDecision.obligation_code == code))
    if status == "candidate":
        if row:
            db.delete(row)
    else:
        if not row:
            row = ApplicabilityDecision(workspace_id=project.workspace_id, project_id=project.id, obligation_code=code,
                                        status=status, reviewer_name=reviewer.strip()[:200], decided_by=ctx.user.id,
                                        ruleset_version=RULESET_VERSION)
            db.add(row)
        row.status, row.rationale, row.reviewer_name = status, rationale.strip()[:2000], reviewer.strip()[:200]
        row.decided_by, row.ruleset_version = ctx.user.id, RULESET_VERSION
    for d in db.scalars(select(PolicyDocument).where(PolicyDocument.project_id == project.id, PolicyDocument.current_version > 0)).all():
        if d.policy_code in OBL[code]["policies"] or d.policy_code == "EISP":
            d.stale, d.stale_reason = True, f"Applicability of {code} changed."
    advance(project, "APPLICABILITY_REVIEW")
    audit(db, ctx, "applicability.decide", "obligation", code, project.id, status=status, reviewer=reviewer.strip()[:200])


# ------------------------------------------------------------------ catalogue and selection
def catalogue_view(db: Session, project: Project, lang: str) -> dict:
    p = load_profile(db, project, lang)
    recs = recommend(p, lang)
    docs = {d.policy_code: d for d in db.scalars(select(PolicyDocument).where(PolicyDocument.project_id == project.id)).all()}
    initialized = bool(docs)
    for r in recs:
        d = docs.get(r["code"])
        if initialized:
            r["selected"] = bool(d and d.selected)
        else:
            r["selected"] = r["recommended"] and p.value("ORG-15") != "custom"
        r["status"] = d.status if d else "NOT_STARTED"
    return {"items": recs, "saved": initialized, "small_org": p.small}


def save_selection(db: Session, ctx: Ctx, project: Project, codes: list[str]) -> None:
    from app.drafting.composer import policy_number
    unknown = [c for c in codes if c not in CAT]
    if unknown:
        raise HTTPException(422, f"Unknown policy codes: {unknown}")
    if not codes:
        raise HTTPException(422, "Select at least one document.")
    p = load_profile(db, project)
    docs = {d.policy_code: d for d in db.scalars(select(PolicyDocument).where(PolicyDocument.project_id == project.id)).all()}
    for code in CAT:
        d = docs.get(code)
        if code in codes and not d:
            db.add(PolicyDocument(workspace_id=project.workspace_id, project_id=project.id, policy_code=code,
                                  policy_id=policy_number(p.doc_prefix, code), selected=True))
        elif d:
            d.selected = code in codes
    advance(project, "LIBRARY_CONFIRMED")
    audit(db, ctx, "selection.save", "project", project.id, project.id, codes=codes)


def selected_codes(db: Session, project: Project) -> list[str]:
    order = list(CAT)
    rows = db.scalars(select(PolicyDocument).where(PolicyDocument.project_id == project.id, PolicyDocument.selected.is_(True))).all()
    return sorted([d.policy_code for d in rows], key=order.index)


def decisions_view(db: Session, project: Project, lang: str) -> list[dict]:
    p = load_profile(db, project, lang)
    out = []
    for code in selected_codes(db, project):
        items = [_qview(d, p.answers.get(d["code"]), lang) for d in DECISIONS_BY_POLICY.get(code, []) if decision_applies(d, p)]
        if items:
            out.append({"policy": code, "title": CAT[code]["title"][lang], "questions": items})
    return out


# ------------------------------------------------------------------ generation
def languages_for(project: Project) -> list[str]:
    return ["en", "fr"] if project.doc_language == "both" else [project.doc_language if project.doc_language in ("en", "fr") else "en"]


def profile_summary(p: Profile) -> str:
    keys = ["ORG-01", "ORG-01B", "ORG-02", "ORG-02B", "ORG-03", "ORG-04", "ORG-05", "ORG-06", "ORG-14", "TECH-01", "TECH-02"]
    parts = [f"{k}: {p.label(k, 'en')}" for k in keys if p.label(k, "en")]
    return "; ".join(parts)[:3000]


def generate(db: Session, ctx: Ctx, project: Project, codes: list[str] | None, tailor: bool) -> list[dict]:
    selected = selected_codes(db, project)
    if not selected:
        raise HTTPException(409, "Select documents in the policy library first.")
    targets = [c for c in (codes or selected) if c in selected]
    if not targets:
        raise HTTPException(422, "None of the requested documents is selected.")
    obligations = applicability_decisions(db, project)
    langs = languages_for(project)
    docs = {d.policy_code: d for d in db.scalars(select(PolicyDocument).where(PolicyDocument.project_id == project.id)).all()}
    results = []
    for code in targets:
        doc = docs[code]
        new_no = doc.current_version + 1
        inputs: set[str] = set()
        bodies = {}
        for lang in langs:
            p = load_profile(db, project, lang)
            cand = {c["code"] for c in candidates(p, lang, obligations) if c["triggered"]}
            cx = Context(p, lang, selected, obligations, cand, version_no=new_no)
            body = compose(code, cx)
            body["policy_id"] = doc.policy_id
            gen = {"provider": "deterministic", "model": None, "prompt_version": None, "composer": body["composer"],
                   "library_version": body["library_version"], "generated_at": body["generated_at"]}
            if tailor:
                gen = _tailor(body, p, lang, gen)
            bodies[lang] = (body, gen)
            inputs |= cx.inputs_used
        for lang, (body, gen) in bodies.items():
            v = PolicyVersion(workspace_id=project.workspace_id, project_id=project.id, document_id=doc.id,
                              version_no=new_no, language=lang, body=body, inputs_used=sorted(inputs), generator=gen,
                              created_by=ctx.user.id)
            db.add(v)
            db.flush()
            _store_clauses(db, v, body)
        doc.current_version, doc.status, doc.stale, doc.stale_reason = new_no, "DRAFT_GENERATED", False, ""
        results.append({"code": code, "version": new_no, "languages": langs,
                        "summary": document_summary(bodies[langs[0]][0])})
        audit(db, ctx, "policy.generate", "policy", doc.id, project.id, code=code, version=new_no, languages=langs,
              generator=bodies[langs[0]][1])
    db.flush()
    run_quality(db, project)
    advance(project, "DRAFT_GENERATED")
    return results


def _tailor(body: dict, p: Profile, lang: str, gen: dict) -> dict:
    summary = profile_summary(p)
    accepted_n, rejected_all, meta = 0, [], None
    for sec in body["sections"]:
        try:
            accepted, rejected, meta = ai.tailor_section(sec, summary, lang)
        except ai.AIError as e:
            rejected_all.append({"section": sec["section_id"], "reason": str(e)})
            continue
        amap = {a["clause_id"]: a["text"] for a in accepted}
        for c in sec["clauses"]:
            if c["clause_id"] in amap:
                c["original_text"] = c["text"]
                c["text"] = amap[c["clause_id"]]
                c["ai_tailored"] = True
                c["placeholders"] = placeholders(c["text"])
                accepted_n += 1
        rejected_all += rejected
    for r in rejected_all:
        body["issues"].append({"kind": "ai_output_rejected", "severity": "low", "clause_id": r.get("clause_id"),
                               "message": (f"Reformulation par l’IA rejetée ({r['reason']}); le texte déterministe a été conservé." if lang == "fr"
                                           else f"AI rewording rejected ({r['reason']}); the deterministic text was kept.")})
    gen = dict(gen)
    if meta:
        gen.update({"provider": meta["provider"], "model": meta["model"], "prompt_version": meta["prompt_version"],
                    "ai_generated_at": meta["generated_at"]})
    gen["ai_tailored_clauses"] = accepted_n
    return gen


def _store_clauses(db: Session, v: PolicyVersion, body: dict) -> None:
    for s in body["sections"]:
        for c in s["clauses"]:
            db.add(PolicyClause(workspace_id=v.workspace_id, version_id=v.id, clause_id=c["clause_id"], section_id=s["section_id"],
                                number=c["number"], text=c["text"], modality=c["modality"], source_type=c["source_type"],
                                source_ids=c["source_ids"], framework_refs=c["framework_refs"], review_status=c["review_status"],
                                edited=bool(c.get("edited"))))


def current_body(db: Session, doc: PolicyDocument, lang: str, version: int | None = None) -> PolicyVersion | None:
    vno = version or doc.current_version
    v = db.scalar(select(PolicyVersion).where(PolicyVersion.document_id == doc.id, PolicyVersion.version_no == vno,
                                              PolicyVersion.language == lang))
    if not v:
        v = db.scalar(select(PolicyVersion).where(PolicyVersion.document_id == doc.id, PolicyVersion.version_no == vno))
    return v


def edit_clause(db: Session, ctx: Ctx, project: Project, doc: PolicyDocument, clause_id: str, lang: str, text: str) -> PolicyVersion:
    """A manual edit creates a new version; earlier versions stay intact (AT-16)."""
    text = (text or "").strip()
    if not text or len(text) > 5000:
        raise HTTPException(422, "Clause text must be 1–5000 characters.")
    old = current_body(db, doc, lang)
    if not old or old.language != lang:
        raise HTTPException(404, "No draft in this language.")
    body = json.loads(json.dumps(old.body))
    found = False
    for s in body["sections"]:
        for c in s["clauses"]:
            if c["clause_id"] == clause_id:
                c["previous_text"] = c["text"]
                c["text"], c["edited"], c["review_status"] = text, True, "edited_by_user"
                c["placeholders"] = placeholders(text)
                found = True
    if not found:
        raise HTTPException(404, "Clause not found.")
    # rebuild placeholder inventory for the edited clause
    body["open_decisions"] = [d for d in body["open_decisions"] if d.get("clause_id") != clause_id]
    for ph in placeholders(text):
        body["open_decisions"].append({"id": f"OD-{clause_id}-e", "type": ph["type"], "severity": "high" if ph["type"] in ("DECISION", "ROLE", "APPROVER") else "medium",
                                       "clause_id": clause_id, "text": ph["text"]})
    new_no = doc.current_version + 1
    body["version"] = f"0.{new_no}"
    body["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    others = db.scalars(select(PolicyVersion).where(PolicyVersion.document_id == doc.id, PolicyVersion.version_no == doc.current_version)).all()
    for o in others:  # carry other languages forward unchanged so every version is complete
        b = body if o.language == lang else dict(o.body, version=f"0.{new_no}")
        nv = PolicyVersion(workspace_id=o.workspace_id, project_id=o.project_id, document_id=doc.id, version_no=new_no,
                           language=o.language, body=b, inputs_used=o.inputs_used,
                           generator=dict(o.generator, edited_by=ctx.user.id), created_by=ctx.user.id)
        db.add(nv)
        db.flush()
        _store_clauses(db, nv, b)
        if o.language != lang:
            db.add(Issue(workspace_id=project.workspace_id, project_id=project.id, document_id=doc.id, version_id=nv.id,
                         clause_id=clause_id, kind="translation_review", severity="medium",
                         message=f"Clause {clause_id} was edited in {lang.upper()}; review the {o.language.upper()} version for equivalence.",
                         message_fr=f"La clause {clause_id} a été modifiée en {lang.upper()}; vérifiez l’équivalence de la version {o.language.upper()}."))
    doc.current_version = new_no
    audit(db, ctx, "clause.edit", "clause", clause_id, project.id, document=doc.policy_code, version=new_no, language=lang)
    db.flush()
    run_quality(db, project)
    return current_body(db, doc, lang)


# ------------------------------------------------------------------ quality checks
def run_quality(db: Session, project: Project) -> list[Issue]:
    """Deterministic per-document and cross-document checks, recorded in English and French.
    Replaces open machine findings; findings a reviewer acknowledged or resolved are not raised again."""
    db.execute(delete(Issue).where(Issue.project_id == project.id, Issue.status == "open",
                                   Issue.kind != "translation_review"))
    selected = selected_codes(db, project)
    docs = {d.policy_code: d for d in db.scalars(select(PolicyDocument).where(PolicyDocument.project_id == project.id)).all()}
    issues: list[Issue] = []

    def add(kind, sev, en, fr, doc=None, version=None, clause=None, sugg_en="", sugg_fr=""):
        if db.scalar(select(Issue).where(Issue.project_id == project.id, Issue.kind == kind, Issue.message == en,
                                         Issue.status != "open")):
            return
        i = Issue(workspace_id=project.workspace_id, project_id=project.id, document_id=doc.id if doc else None,
                  version_id=version.id if version else None, clause_id=clause, kind=kind, severity=sev, message=en,
                  message_fr=fr, suggestion=sugg_en, suggestion_fr=sugg_fr)
        db.add(i)
        issues.append(i)

    blocking, legal, owners = [], [], set()
    for code in selected:
        d = docs.get(code)
        if not d or d.current_version == 0:
            continue
        v_en, v_fr = current_body(db, d, "en"), current_body(db, d, "fr")
        v = v_en or v_fr
        b_en = v_en.body if v_en and v_en.language == "en" else None
        b_fr = v_fr.body if v_fr and v_fr.language == "fr" else None
        b = b_en or b_fr
        fr_issues = {(x["kind"], x.get("clause_id")): x for x in (b_fr or b)["issues"]}
        for f in b["issues"]:
            g = fr_issues.get((f["kind"], f.get("clause_id")), f)
            add(f["kind"], f["severity"], f"{d.policy_id} {f.get('clause_id') or ''}: {f['message']}",
                f"{d.policy_id} {g.get('clause_id') or ''} : {g['message']}", d, v, f.get("clause_id"),
                f.get("suggestion", ""), g.get("suggestion", ""))
        high = sum(1 for x in b["open_decisions"] if x["severity"] == "high")
        if high:
            blocking.append(f"{d.policy_id} ({high})")
        if any(c["legal_review"] for s in b["sections"] for c in s["clauses"]):
            legal.append(d.policy_id)
        fr_gaps = {x["clause_id"]: x["text"] for x in (b_fr or b).get("gaps", [])}
        for g in b.get("gaps", []):
            add("implementation_gap", g["severity"],
                f"{d.policy_id} {g['clause_id']}: {g['text']} The requirement needs implementation work before it can be enforced.",
                f"{d.policy_id} {g['clause_id']} : {fr_gaps.get(g['clause_id'], g['text'])} L’exigence nécessite des travaux de mise en œuvre avant de pouvoir être appliquée.",
                d, v, g["clause_id"])
        if d.stale:
            add("stale_draft", "medium", f"{d.policy_id}: answers changed since this draft — regenerate it.",
                f"{d.policy_id} : des réponses ont changé depuis cette ébauche — régénérez-la.", d, v)
        if b["template"] == "structure":
            add("structure_template", "medium", f"{d.policy_id}: structure template — the owner still has to write the mandatory requirements.",
                f"{d.policy_id} : gabarit de structure — le responsable doit encore rédiger les exigences obligatoires.", d, v)
        if not b["owner"].startswith("["):
            owners.add(b["owner"])
    if blocking:
        add("unresolved_placeholders", "high",
            "High-severity open decisions block “ready for approval” status (draft export remains possible): " + ", ".join(blocking) + ".",
            "Des décisions ouvertes de gravité élevée empêchent le statut « prêt pour approbation » (l’exportation de l’ébauche reste possible) : " + ", ".join(blocking) + ".",
            sugg_en="Answer the Decisions step, or complete the highlighted placeholders in the drafts.",
            sugg_fr="Répondez à l’étape Décisions ou complétez les espaces réservés surlignés dans les ébauches.")
    if legal:
        add("legal_review", "medium",
            "Clauses flagged for legal review (privacy, monitoring, retention, sanctions or notification) in: " + ", ".join(legal) + ".",
            "Clauses à soumettre à une révision juridique (vie privée, surveillance, conservation, sanctions ou notification) dans : " + ", ".join(legal) + ".")
    if "EISP" not in selected and selected:
        add("missing_parent", "medium", "Topic policies refer to the Enterprise Information Security Policy, which is not selected.",
            "Les politiques thématiques renvoient à la Politique de sécurité de l’information de l’entreprise, qui n’est pas sélectionnée.",
            sugg_en="Select it, or replace the references with the document that plays that role.",
            sugg_fr="Sélectionnez-la ou remplacez les renvois par le document qui joue ce rôle.")
    if len({o.lower() for o in owners}) > 2:
        add("role_inconsistency", "low", f"Different owner names are used across documents: {', '.join(sorted(owners))}.",
            f"Des noms de responsables différents sont utilisés dans les documents : {', '.join(sorted(owners))}.")
    conflicts = db.scalars(select(OrganizationFact).where(OrganizationFact.project_id == project.id,
                                                          OrganizationFact.conflict_group.is_not(None),
                                                          OrganizationFact.state == "proposed")).all()
    for grp in sorted({f.conflict_group for f in conflicts}):
        vals = ", ".join(sorted({json.dumps(f.value, ensure_ascii=False) for f in conflicts if f.conflict_group == grp}))
        code = grp.replace("CONFLICT-", "")
        add("evidence_conflict", "high", f"Uploaded documents disagree on {code}: {vals}. Neither value is used until you decide in Documents.",
            f"Des documents téléversés se contredisent sur {code} : {vals}. Aucune valeur n’est utilisée avant votre décision à l’étape Documents.")
    db.flush()
    return issues


def issues_view(db: Session, project: Project, lang: str = "en") -> list[dict]:
    docs = {d.id: d for d in db.scalars(select(PolicyDocument).where(PolicyDocument.project_id == project.id)).all()}
    order = {"high": 0, "medium": 1, "low": 2}
    rows = db.scalars(select(Issue).where(Issue.project_id == project.id)).all()
    fr = lang == "fr"
    out = [{"id": i.id, "kind": i.kind, "severity": i.severity,
            "message": (i.message_fr or i.message) if fr else i.message,
            "suggestion": (i.suggestion_fr or i.suggestion) if fr else i.suggestion,
            "status": i.status, "resolution": i.resolution, "clause_id": i.clause_id,
            "policy": docs[i.document_id].policy_code if i.document_id in docs else None} for i in rows]
    return sorted(out, key=lambda x: (x["status"] != "open", order.get(x["severity"], 3)))


def profile_view(db: Session, project: Project, lang: str) -> dict:
    p = load_profile(db, project, lang)
    groups = []
    for sec, title in SECTION_TITLES.items():
        items = []
        for q in visible_questions(p, project.mode) if sec != "decisions" else []:
            if q["section"] != sec:
                continue
            a = p.answers.get(q["code"])
            items.append({"code": q["code"], "label": q["label"][lang], "status": a["status"] if a else None,
                          "value": p.label(q["code"], lang), "source": a.get("source") if a else None})
        if sec == "decisions":
            for d in DECISIONS:
                a = p.answers.get(d["code"])
                if a:
                    items.append({"code": d["code"], "label": d["label"][lang], "status": a["status"],
                                  "value": p.label(d["code"], lang), "source": a.get("source")})
        if items:
            groups.append({"section": sec, "title": title[lang], "items": items})
    return {"groups": groups, "observations": governance_observations(p, lang), "progress": progress(p, project.mode),
            "doc_prefix": p.doc_prefix, "org_name": p.org_name}
