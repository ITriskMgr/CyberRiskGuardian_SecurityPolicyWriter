"""Export jobs: single .docx and ZIP package with index, open decisions, traceability and roadmap reports."""
from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
import zipfile
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.catalogue.catalogue import BY_CODE as CAT
from app.export import docx_render as R
from app.models import ExportJob, PolicyDocument, Project
from app.questionnaire.engine import governance_observations
from app.security import Ctx, audit
from app import services as S

FOLDER = {0: "01_Governance", 1: "01_Governance", 2: "02_Policies", 3: "03_Standards", 4: "04_Procedures"}


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w\- ]", "", s).strip().replace(" ", "_")
    return s[:80] or "document"


def _filename(body: dict) -> str:
    return f"{body['policy_id']}_{_slug(body['title'])}_v{body['version']}_{body['language'].upper()}_DRAFT.docx"


def _job(db: Session, ctx: Ctx, project: Project, kind: str, filename: str, data: bytes, files: list[str]) -> ExportJob:
    folder = config.settings.export_dir / project.workspace_id / project.id
    folder.mkdir(parents=True, exist_ok=True)
    job = ExportJob(workspace_id=project.workspace_id, project_id=project.id, kind=kind, filename=filename, path="",
                    sha256=hashlib.sha256(data).hexdigest(), files=files, created_by=ctx.user.id)
    db.add(job)
    db.flush()
    path = folder / f"{job.id}.{'zip' if kind == 'zip' else 'docx'}"
    path.write_bytes(data)
    job.path = str(path)
    audit(db, ctx, f"export.{kind}", "export", job.id, project.id, filename=filename, sha256=job.sha256, files=len(files))
    return job


def export_single(db: Session, ctx: Ctx, project: Project, doc: PolicyDocument, lang: str) -> ExportJob:
    v = S.current_body(db, doc, lang)
    if not v or v.language != lang:
        raise HTTPException(404, "No draft in this language. Generate it first.")
    data = R.render_policy(v.body, {"document_uuid": doc.id, "model": v.generator.get("model")})
    name = _filename(v.body)
    return _job(db, ctx, project, "docx", name, data, [name])


def export_package(db: Session, ctx: Ctx, project: Project, codes: list[str] | None) -> ExportJob:
    selected = S.selected_codes(db, project)
    codes = [c for c in (codes or selected) if c in selected]
    docs = {d.policy_code: d for d in db.scalars(select(PolicyDocument).where(PolicyDocument.project_id == project.id)).all()}
    codes = [c for c in codes if docs.get(c) and docs[c].current_version > 0]
    if not codes:
        raise HTTPException(409, "No generated drafts to export.")
    langs = S.languages_for(project)
    buf = io.BytesIO()
    files: list[str] = []
    org = project.org_display_name or project.name
    root = _slug(org) + "_Policy_Package_DRAFT"
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for lang in langs:
            sub = f"/{lang.upper()}" if len(langs) > 1 else ""
            bodies = []
            for code in codes:
                d = docs[code]
                v = S.current_body(db, d, lang)
                if not v:
                    continue
                bodies.append(v.body)
                path = f"{root}{sub}/{FOLDER[CAT[code]['level']]}/{_filename(v.body)}"
                z.writestr(path, R.render_policy(v.body, {"document_uuid": d.id, "model": v.generator.get("model")}))
                files.append(path)
            # reports
            rep = f"{root}{sub}/05_Registers_Reports"
            idx_rows = [[b["policy_id"], b["title"], b["level_label"], b.get("parent_policy_id") or "—", b["owner"], b["version"],
                         "DRAFT"] for b in bodies]
            rep_names = [f"{rep}/0{i}_{_slug(R.R[lang][k])}.docx" for i, k in enumerate(("index", "decisions", "trace", "roadmap"))]
            z.writestr(rep_names[0], R.render_index(org, lang, idx_rows))
            p = S.load_profile(db, project, lang)
            facts = []
            for g in S.profile_view(db, project, lang)["groups"]:
                for it in g["items"]:
                    if it["status"] == "answered":
                        facts.append([it["label"], it["value"], R.R[lang]["src_doc"] if it["source"] == "document" else R.R[lang]["src_user"]])
            obl = [[c["name"], R.R[lang]["status_map"].get(c["status"], c["status"]),
                    (f"{c['decision']['reviewer_name']}: {c['decision']['rationale']}" if c.get("decision") else c["confirm"])]
                   for c in S.applicability(db, project, lang)]
            z.writestr(rep_names[1],
                       R.render_decisions(org, lang, bodies, facts, obl, governance_observations(p, lang)))
            z.writestr(rep_names[2], R.render_trace(org, lang, bodies))
            z.writestr(rep_names[3], R.render_roadmap(org, lang, bodies))
            files += rep_names
            # CSVs
            s = io.StringIO()
            w = csv.writer(s)
            w.writerow(["document_id", "title", "type", "parent", "owner", "version", "status"])
            w.writerows(idx_rows)
            z.writestr(f"{rep}/policy_index.csv", "﻿" + s.getvalue())
            s = io.StringIO()
            w = csv.writer(s)
            w.writerow(["document_id", "clause_id", "number", "modality", "source_type", "source_ids", "framework_refs",
                        "review_status", "legal_review", "text"])
            for b in bodies:
                for sec in b["sections"]:
                    for c in sec["clauses"]:
                        w.writerow([b["policy_id"], c["clause_id"], c["number"], c["modality"], c["source_type"],
                                    ";".join(c["source_ids"]), ";".join(c["framework_refs"]), c["review_status"],
                                    "yes" if c.get("legal_review") else "no", c["text"]])
            z.writestr(f"{rep}/traceability.csv", "﻿" + s.getvalue())
            files += [f"{rep}/policy_index.csv", f"{rep}/traceability.csv"]
        z.writestr(f"{root}/README.txt", (
            f"{org} — information security policy package (DRAFT)\n"
            f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} by {config.APP_NAME} {config.APP_VERSION}.\n\n"
            "These documents are drafts. They are not in force until reviewed and approved by the organization's authorized persons.\n"
            "Open the Word files and update the table of contents (F9). Highlighted [BRACKETS] are decisions to complete.\n"
            "05_Registers_Reports lists open decisions, assumptions, legal candidates, traceability and implementation gaps.\n"))
    data = buf.getvalue()
    return _job(db, ctx, project, "zip", f"{root}.zip", data, files)
