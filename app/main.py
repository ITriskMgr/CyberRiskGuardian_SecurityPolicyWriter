"""FastAPI application: authenticated, tenant-scoped JSON API + static web client."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config, services as S
from app.catalogue.catalogue import CATALOGUE_VERSION
from app.catalogue.rulesets import RULESET_VERSION
from app.db import get_session, migrate
from app.drafting.library import LIBRARY_VERSION
from app.export import package
from app.ingestion.ocr import engine_info as ocr_engine_info
from app.models import (AuditEvent, Reimport, ExportJob, Issue, Membership, OrganizationFact, PolicyDocument, PolicyVersion, Project,
                        SourceDocument, User, Workspace, now)
from app.questionnaire.questions import QUESTIONNAIRE_VERSION
from app.security import (COOKIE, Ctx, audit, create_session, current_ctx, destroy_session, get_project, hash_password,
                          scoped_get, verify_password)

WEB = config.BASE_DIR / "web"


@asynccontextmanager
async def lifespan(_app):
    migrate()
    yield


app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION, lifespan=lifespan,
              description="AI-assisted information security policy development. All drafts require human review and approval.")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = ("default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; "
                                               "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
    if request.url.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    elif request.url.path == "/" or request.url.path.startswith("/static/"):
        resp.headers["Cache-Control"] = "no-cache"  # always revalidate, so an updated app is picked up
    return resp


@app.middleware("http")
async def csrf_guard(request: Request, call_next):
    """State-changing API calls must carry the custom header the web client sends (blocks cross-site form posts)."""
    if request.url.path.startswith("/api/") and request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if request.headers.get("x-requested-with") != "policybuilder":
            return JSONResponse({"detail": "Missing request header."}, status_code=403)
    return await call_next(request)


DB = Depends(get_session)
CTX = Depends(current_ctx)


def _lang(lang: str | None) -> str:
    return "fr" if lang == "fr" else "en"


# ------------------------------------------------------------------ meta & auth
@app.get("/api/health")
def health():
    return {"status": "ok", "version": config.APP_VERSION}


@app.get("/api/meta")
def meta():
    s = config.settings
    return {"app": config.APP_NAME, "version": config.APP_VERSION, "ai_provider": "anthropic" if s.ai_available else "mock",
            "ai_model": s.ai_model if s.ai_available else None, "questionnaire": QUESTIONNAIRE_VERSION,
            "catalogue": CATALOGUE_VERSION, "ruleset": RULESET_VERSION, "library": LIBRARY_VERSION,
            "max_upload_mb": s.max_upload_mb, "ocr": ocr_engine_info()}


class RegisterIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=10, max_length=200)
    display_name: str = Field(min_length=1, max_length=200)
    workspace_name: str = Field(min_length=1, max_length=200)


class LoginIn(BaseModel):
    email: str
    password: str


def _set_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(COOKIE, token, httponly=True, samesite="strict", secure=config.settings.secure_cookies,
                    max_age=config.settings.session_hours * 3600, path="/")


@app.post("/api/auth/register")
def register(body: RegisterIn, response: Response, db: Session = DB):
    email = body.email.strip().lower()
    if "@" not in email:
        raise HTTPException(422, "Invalid email.")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account already exists for this email.")
    ws = Workspace(name=body.workspace_name.strip())
    user = User(email=email, display_name=body.display_name.strip(), password_hash=hash_password(body.password))
    db.add_all([ws, user])
    db.flush()
    db.add(Membership(workspace_id=ws.id, user_id=user.id, role="admin"))
    audit(db, None, "auth.register", "user", user.id, workspace_id=ws.id)
    db.commit()
    _set_cookie(response, create_session(db, user.id, ws.id))
    return {"ok": True}


@app.post("/api/auth/login")
def login(body: LoginIn, response: Response, db: Session = DB):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    m = db.scalar(select(Membership).where(Membership.user_id == user.id).order_by(Membership.created_at))
    if not m:
        raise HTTPException(403, "No workspace access.")
    audit(db, None, "auth.login", "user", user.id, workspace_id=m.workspace_id)
    db.commit()
    _set_cookie(response, create_session(db, user.id, m.workspace_id))
    return {"ok": True}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response, db: Session = DB):
    destroy_session(db, request.cookies.get(COOKIE))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@app.get("/api/auth/me")
def me(ctx: Ctx = CTX, db: Session = DB):
    ws = db.get(Workspace, ctx.workspace_id)
    return {"email": ctx.user.email, "display_name": ctx.user.display_name, "role": ctx.role,
            "workspace": {"id": ws.id, "name": ws.name}, "ui_language": ctx.user.ui_language}


class LangIn(BaseModel):
    ui_language: str


@app.put("/api/auth/me/language")
def set_ui_lang(body: LangIn, ctx: Ctx = CTX, db: Session = DB):
    u = db.get(User, ctx.user.id)
    u.ui_language = _lang(body.ui_language)
    db.commit()
    return {"ok": True}


class MemberIn(BaseModel):
    email: str
    display_name: str
    password: str = Field(min_length=10)
    role: str


@app.get("/api/workspace/members")
def members(ctx: Ctx = CTX, db: Session = DB):
    rows = db.execute(select(Membership, User).join(User, User.id == Membership.user_id)
                      .where(Membership.workspace_id == ctx.workspace_id)).all()
    return [{"email": u.email, "display_name": u.display_name, "role": m.role} for m, u in rows]


@app.post("/api/workspace/members")
def add_member(body: MemberIn, ctx: Ctx = CTX, db: Session = DB):
    ctx.require("admin")
    if body.role not in ("admin", "owner", "author", "reviewer", "auditor"):
        raise HTTPException(422, "Invalid role.")
    email = body.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email, display_name=body.display_name.strip(), password_hash=hash_password(body.password))
        db.add(user)
        db.flush()
    elif db.scalar(select(Membership).where(Membership.user_id == user.id, Membership.workspace_id == ctx.workspace_id)):
        raise HTTPException(409, "Already a member.")
    db.add(Membership(workspace_id=ctx.workspace_id, user_id=user.id, role=body.role))
    audit(db, ctx, "member.add", "user", user.id, role=body.role)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ projects
class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    mode: str = "express"
    purpose: str = "new_framework"
    doc_language: str = "en"


class ProjectPatch(BaseModel):
    name: str | None = None
    mode: str | None = None
    doc_language: str | None = None
    ai_on_sources: bool | None = None


def _project_out(db: Session, p: Project, lang: str = "en") -> dict:
    prof = S.load_profile(db, p, lang)
    from app.questionnaire.engine import progress
    docs = db.scalars(select(PolicyDocument).where(PolicyDocument.project_id == p.id, PolicyDocument.selected.is_(True))).all()
    return {"id": p.id, "name": p.name, "org_display_name": p.org_display_name, "mode": p.mode, "purpose": p.purpose,
            "workflow_state": p.workflow_state, "doc_language": p.doc_language, "ai_on_sources": p.ai_on_sources,
            "lock_version": p.lock_version, "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "progress": progress(prof, p.mode), "selected": len(docs),
            "generated": sum(1 for d in docs if d.current_version > 0), "stale": sum(1 for d in docs if d.stale),
            "sources": len(db.scalars(select(SourceDocument.id).where(SourceDocument.project_id == p.id)).all())}


@app.get("/api/projects")
def list_projects(ctx: Ctx = CTX, db: Session = DB):
    rows = db.scalars(select(Project).where(Project.workspace_id == ctx.workspace_id, Project.deleted_at.is_(None))
                      .order_by(Project.updated_at.desc())).all()
    return [_project_out(db, p) for p in rows]


@app.post("/api/projects")
def create_project(body: ProjectIn, ctx: Ctx = CTX, db: Session = DB):
    ctx.require("author")
    if body.mode not in ("express", "standard") or body.doc_language not in ("en", "fr", "both") or \
            body.purpose not in ("new_framework", "single_policy", "improve", "update"):
        raise HTTPException(422, "Invalid project settings.")
    p = Project(workspace_id=ctx.workspace_id, name=body.name.strip(), mode=body.mode, purpose=body.purpose,
                doc_language=body.doc_language, created_by=ctx.user.id)
    db.add(p)
    db.flush()
    S.set_answer(db, ctx, p, "ORG-10", body.doc_language, "answered")
    p.workflow_state = "PROJECT_CREATED"
    audit(db, ctx, "project.create", "project", p.id, p.id)
    db.commit()
    return _project_out(db, p)


@app.get("/api/projects/{pid}")
def get_proj(pid: str, ctx: Ctx = CTX, db: Session = DB):
    return _project_out(db, get_project(db, ctx, pid))


@app.patch("/api/projects/{pid}")
def patch_project(pid: str, body: ProjectPatch, ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    ctx.require("author")
    if body.name is not None:
        p.name = body.name.strip()[:300] or p.name
    if body.mode in ("express", "standard"):
        p.mode = body.mode
    if body.doc_language in ("en", "fr", "both"):
        S.set_answer(db, ctx, p, "ORG-10", body.doc_language, "answered")
    if body.ai_on_sources is not None:
        ctx.require("owner")
        p.ai_on_sources = body.ai_on_sources
        audit(db, ctx, "project.ai_on_sources", "project", p.id, p.id, enabled=body.ai_on_sources)
    p.lock_version += 1
    db.commit()
    return _project_out(db, p)


@app.delete("/api/projects/{pid}")
def delete_project(pid: str, ctx: Ctx = CTX, db: Session = DB):
    """Hard delete: database rows (cascade), encrypted source files and exports (AT-13)."""
    p = get_project(db, ctx, pid)
    ctx.require("owner")
    import shutil
    for base in (config.settings.blob_dir, config.settings.export_dir):
        shutil.rmtree(base / p.workspace_id / p.id, ignore_errors=True)
    audit(db, ctx, "project.delete", "project", p.id, None, name=p.name)
    db.delete(p)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ interview
@app.get("/api/projects/{pid}/interview")
def get_interview(pid: str, lang: str = "en", ctx: Ctx = CTX, db: Session = DB):
    return S.interview(db, get_project(db, ctx, pid), _lang(lang))


class AnswerIn(BaseModel):
    value: Any = None
    status: str = "answered"


@app.put("/api/projects/{pid}/answers/{code}")
def put_answer(pid: str, code: str, body: AnswerIn, lang: str = "en", ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    ctx.require("author")
    S.set_answer(db, ctx, p, code, body.value, body.status)
    db.commit()
    from app.questionnaire.engine import progress
    return {"ok": True, "progress": progress(S.load_profile(db, p, _lang(lang)), p.mode)}


@app.get("/api/projects/{pid}/profile")
def get_profile(pid: str, lang: str = "en", ctx: Ctx = CTX, db: Session = DB):
    return S.profile_view(db, get_project(db, ctx, pid), _lang(lang))


# ------------------------------------------------------------------ documents & facts
@app.post("/api/projects/{pid}/sources")
async def upload(pid: str, file: UploadFile = File(...), category: str = Form("other"), ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    ctx.require("author")
    data = await file.read(config.settings.max_upload_mb * 1024 * 1024 + 1)
    doc = S.ingest(db, ctx, p, file.filename or "upload", data, category)
    db.commit()
    n = len(db.scalars(select(OrganizationFact.id).where(OrganizationFact.source_id == doc.id)).all())
    return {"id": doc.id, "filename": doc.filename, "warnings": doc.warnings, "facts": n}


@app.get("/api/projects/{pid}/sources")
def list_sources(pid: str, ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    rows = db.scalars(select(SourceDocument).where(SourceDocument.project_id == p.id).order_by(SourceDocument.created_at)).all()
    out = []
    for s in rows:
        facts = db.scalars(select(OrganizationFact).where(OrganizationFact.source_id == s.id)).all()
        out.append({"id": s.id, "filename": s.filename, "mime": s.mime, "size": s.size, "category": s.category,
                    "title": s.title, "doc_date": s.doc_date, "state": s.ingestion_state, "warnings": s.warnings,
                    "facts": len(facts), "pending": sum(1 for f in facts if f.state == "proposed"),
                    "ocr_pages": s.ocr_pages or [], "ocr_meta": s.ocr_meta or {},
                    "uploaded_at": s.created_at.isoformat()})
    return out


@app.get("/api/sources/{sid}/segments")
def source_segments(sid: str, ctx: Ctx = CTX, db: Session = DB):
    src = scoped_get(db, ctx, SourceDocument, sid)
    return {"filename": src.filename, "segments": S.segments_view(db, src)}


@app.post("/api/sources/{sid}/ocr")
def source_ocr(sid: str, ctx: Ctx = CTX, db: Session = DB):
    src = scoped_get(db, ctx, SourceDocument, sid)
    ctx.require("author")
    res = S.run_ocr(db, ctx, get_project(db, ctx, src.project_id), src)
    db.commit()
    return res


@app.delete("/api/sources/{sid}")
def delete_source(sid: str, ctx: Ctx = CTX, db: Session = DB):
    src = scoped_get(db, ctx, SourceDocument, sid)
    ctx.require("author")
    p = get_project(db, ctx, src.project_id)
    S.delete_source(db, ctx, p, src)
    db.commit()
    return {"ok": True}


@app.get("/api/projects/{pid}/facts")
def list_facts(pid: str, lang: str = "en", ctx: Ctx = CTX, db: Session = DB):
    return S.facts_view(db, get_project(db, ctx, pid), _lang(lang))


class FactDecision(BaseModel):
    action: str


@app.post("/api/facts/{fid}/decision")
def fact_decision(fid: str, body: FactDecision, ctx: Ctx = CTX, db: Session = DB):
    f = scoped_get(db, ctx, OrganizationFact, fid)
    ctx.require("author")
    S.decide_fact(db, ctx, get_project(db, ctx, f.project_id), f, body.action)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ applicability
@app.get("/api/projects/{pid}/applicability")
def get_applicability(pid: str, lang: str = "en", ctx: Ctx = CTX, db: Session = DB):
    return {"ruleset_version": RULESET_VERSION, "items": S.applicability(db, get_project(db, ctx, pid), _lang(lang))}


class ApplicabilityIn(BaseModel):
    status: str
    rationale: str = ""
    reviewer_name: str = ""


@app.post("/api/projects/{pid}/applicability/{code}")
def post_applicability(pid: str, code: str, body: ApplicabilityIn, ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    ctx.require("reviewer")
    S.decide_applicability(db, ctx, p, code, body.status, body.rationale, body.reviewer_name)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ catalogue, decisions, generation
@app.get("/api/projects/{pid}/catalogue")
def get_catalogue(pid: str, lang: str = "en", ctx: Ctx = CTX, db: Session = DB):
    return S.catalogue_view(db, get_project(db, ctx, pid), _lang(lang))


class SelectionIn(BaseModel):
    codes: list[str]


@app.put("/api/projects/{pid}/selection")
def put_selection(pid: str, body: SelectionIn, ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    ctx.require("author")
    S.save_selection(db, ctx, p, body.codes)
    db.commit()
    return {"ok": True}


@app.get("/api/projects/{pid}/decisions")
def get_decisions(pid: str, lang: str = "en", ctx: Ctx = CTX, db: Session = DB):
    return S.decisions_view(db, get_project(db, ctx, pid), _lang(lang))


class GenerateIn(BaseModel):
    codes: list[str] | None = None
    tailor_with_ai: bool = False


@app.post("/api/projects/{pid}/generate")
def generate(pid: str, body: GenerateIn, ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    ctx.require("author")
    res = S.generate(db, ctx, p, body.codes, body.tailor_with_ai)
    db.commit()
    return {"results": res}


@app.get("/api/projects/{pid}/policies")
def list_policies(pid: str, lang: str = "en", ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    from app.catalogue.catalogue import BY_CODE as CAT
    from app.drafting.composer import document_summary
    out = []
    for code in S.selected_codes(db, p):
        d = db.scalar(select(PolicyDocument).where(PolicyDocument.project_id == p.id, PolicyDocument.policy_code == code))
        v = S.current_body(db, d, _lang(lang)) if d.current_version else None
        out.append({"id": d.id, "code": code, "policy_id": d.policy_id, "title": CAT[code]["title"][_lang(lang)],
                    "template": CAT[code]["template"], "status": d.status, "version": d.current_version, "stale": d.stale,
                    "stale_reason": d.stale_reason, "summary": document_summary(v.body) if v else None,
                    "languages": sorted({x.language for x in db.scalars(select(PolicyVersion).where(
                        PolicyVersion.document_id == d.id, PolicyVersion.version_no == d.current_version)).all()})})
    return out


@app.get("/api/policies/{doc_id}")
def get_policy(doc_id: str, lang: str = "en", version: int | None = None, ctx: Ctx = CTX, db: Session = DB):
    d = scoped_get(db, ctx, PolicyDocument, doc_id)
    v = S.current_body(db, d, _lang(lang), version)
    if not v:
        raise HTTPException(404, "No draft yet.")
    return {"document_id": d.id, "version_no": v.version_no, "language": v.language, "body": v.body,
            "generator": v.generator, "stale": d.stale, "stale_reason": d.stale_reason}


@app.get("/api/policies/{doc_id}/versions")
def policy_versions(doc_id: str, ctx: Ctx = CTX, db: Session = DB):
    d = scoped_get(db, ctx, PolicyDocument, doc_id)
    rows = db.scalars(select(PolicyVersion).where(PolicyVersion.document_id == d.id).order_by(PolicyVersion.version_no.desc())).all()
    return [{"version_no": v.version_no, "language": v.language, "created_at": v.created_at.isoformat(),
             "generator": v.generator} for v in rows]


class ClauseEdit(BaseModel):
    text: str
    lang: str = "en"


@app.patch("/api/policies/{doc_id}/clauses/{clause_id}")
def patch_clause(doc_id: str, clause_id: str, body: ClauseEdit, ctx: Ctx = CTX, db: Session = DB):
    d = scoped_get(db, ctx, PolicyDocument, doc_id)
    ctx.require("author")
    p = get_project(db, ctx, d.project_id)
    v = S.edit_clause(db, ctx, p, d, clause_id, _lang(body.lang), body.text)
    db.commit()
    return {"version_no": v.version_no}


# ------------------------------------------------------------------ Word re-import
@app.post("/api/projects/{pid}/reimports")
async def upload_reimport(pid: str, file: UploadFile = File(...), ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    ctx.require("author")
    data = await file.read(config.settings.max_upload_mb * 1024 * 1024 + 1)
    ri = S.create_reimport(db, ctx, p, file.filename or "edited.docx", data)
    db.commit()
    return S.reimport_view(db, ri)


@app.get("/api/projects/{pid}/reimports")
def list_reimports(pid: str, ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    rows = db.scalars(select(Reimport).where(Reimport.project_id == p.id).order_by(Reimport.created_at.desc())).all()
    return [{k: v for k, v in S.reimport_view(db, r).items() if k != "changes"} | {"changes": len(r.changes)} for r in rows]


@app.get("/api/reimports/{rid}")
def get_reimport(rid: str, ctx: Ctx = CTX, db: Session = DB):
    return S.reimport_view(db, scoped_get(db, ctx, Reimport, rid))


class ReimportDecisions(BaseModel):
    decisions: dict[str, str]


@app.post("/api/reimports/{rid}/decisions")
def reimport_decisions(rid: str, body: ReimportDecisions, ctx: Ctx = CTX, db: Session = DB):
    ri = scoped_get(db, ctx, Reimport, rid)
    ctx.require("author")
    S.decide_reimport(db, ctx, ri, body.decisions)
    db.commit()
    return S.reimport_view(db, ri)


@app.post("/api/reimports/{rid}/apply")
def reimport_apply(rid: str, ctx: Ctx = CTX, db: Session = DB):
    ri = scoped_get(db, ctx, Reimport, rid)
    ctx.require("author")
    v = S.apply_reimport(db, ctx, get_project(db, ctx, ri.project_id), ri)
    db.commit()
    return {"version_no": v}


@app.post("/api/reimports/{rid}/discard")
def reimport_discard(rid: str, ctx: Ctx = CTX, db: Session = DB):
    ri = scoped_get(db, ctx, Reimport, rid)
    ctx.require("author")
    if ri.status == "pending":
        ri.status = "discarded"
        audit(db, ctx, "reimport.discard", "reimport", ri.id, ri.project_id)
        db.commit()
    return {"ok": True}


@app.get("/api/projects/{pid}/issues")
def list_issues(pid: str, lang: str = "en", ctx: Ctx = CTX, db: Session = DB):
    return S.issues_view(db, get_project(db, ctx, pid), _lang(lang))


class IssueIn(BaseModel):
    status: str
    resolution: str = ""


@app.post("/api/issues/{iid}")
def update_issue(iid: str, body: IssueIn, ctx: Ctx = CTX, db: Session = DB):
    i = scoped_get(db, ctx, Issue, iid)
    ctx.require("reviewer")
    if body.status not in ("open", "acknowledged", "resolved"):
        raise HTTPException(422, "Invalid status.")
    i.status, i.resolution, i.decided_by = body.status, body.resolution.strip()[:2000], ctx.user.id
    audit(db, ctx, "issue.update", "issue", i.id, i.project_id, status=body.status)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ exports
class ExportIn(BaseModel):
    kind: str
    document_id: str | None = None
    lang: str = "en"
    codes: list[str] | None = None


@app.post("/api/projects/{pid}/exports")
def create_export(pid: str, body: ExportIn, ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    ctx.require("author")
    if body.kind == "docx":
        d = scoped_get(db, ctx, PolicyDocument, body.document_id or "")
        if d.project_id != p.id:
            raise HTTPException(404, "Not found.")
        job = package.export_single(db, ctx, p, d, _lang(body.lang))
    elif body.kind == "zip":
        job = package.export_package(db, ctx, p, body.codes)
    else:
        raise HTTPException(422, "Unknown export kind.")
    db.commit()
    return {"id": job.id, "filename": job.filename, "sha256": job.sha256, "files": job.files,
            "download": f"/api/exports/{job.id}/download"}


@app.get("/api/projects/{pid}/exports")
def list_exports(pid: str, ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    rows = db.scalars(select(ExportJob).where(ExportJob.project_id == p.id).order_by(ExportJob.created_at.desc())).all()
    return [{"id": j.id, "kind": j.kind, "filename": j.filename, "sha256": j.sha256, "created_at": j.created_at.isoformat(),
             "files": len(j.files), "download": f"/api/exports/{j.id}/download"} for j in rows]


@app.get("/api/exports/{job_id}/download")
def download(job_id: str, ctx: Ctx = CTX, db: Session = DB):
    job = scoped_get(db, ctx, ExportJob, job_id)
    path = Path(job.path)
    if not path.exists():
        raise HTTPException(410, "Export file no longer available.")
    audit(db, ctx, "export.download", "export", job.id, job.project_id)
    db.commit()
    media = "application/zip" if job.kind == "zip" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(path, media_type=media, filename=job.filename)


@app.get("/api/projects/{pid}/audit")
def audit_log(pid: str, ctx: Ctx = CTX, db: Session = DB):
    p = get_project(db, ctx, pid)
    rows = db.scalars(select(AuditEvent).where(AuditEvent.project_id == p.id, AuditEvent.workspace_id == ctx.workspace_id)
                      .order_by(AuditEvent.at.desc()).limit(300)).all()
    users = {u.id: u.display_name for u in db.scalars(select(User)).all()}
    return [{"at": e.at.isoformat(), "actor": users.get(e.actor_id, "—"), "action": e.action, "entity": e.entity,
             "entity_id": e.entity_id, "details": e.details} for e in rows]


# ------------------------------------------------------------------ web client
@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


app.mount("/static", StaticFiles(directory=WEB), name="static")
