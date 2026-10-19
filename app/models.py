"""ORM entities. Every tenant-owned row carries workspace_id (the tenant) — see ADR-001 D4."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

SCHEMA_VERSION = 1


def _uuid() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


# ---------------------------------------------------------------- identity & tenancy
class Workspace(Base, Timestamped):
    __tablename__ = "workspace"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    retention_days: Mapped[int] = mapped_column(Integer, default=365)


class User(Base, Timestamped):
    __tablename__ = "user_account"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(300))
    ui_language: Mapped[str] = mapped_column(String(5), default="en")


class Membership(Base, Timestamped):
    __tablename__ = "membership"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user_account.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # admin | owner | author | reviewer | auditor


class SessionToken(Base):
    __tablename__ = "session_token"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user_account.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


# ---------------------------------------------------------------- project & interview
class Project(Base, Timestamped):
    __tablename__ = "project"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(300))
    org_display_name: Mapped[str] = mapped_column(String(300), default="")
    mode: Mapped[str] = mapped_column(String(20), default="express")  # express | standard
    purpose: Mapped[str] = mapped_column(String(30), default="new_framework")
    workflow_state: Mapped[str] = mapped_column(String(40), default="PROJECT_CREATED")
    doc_language: Mapped[str] = mapped_column(String(10), default="en")  # en | fr | both
    ai_on_sources: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(String(36))
    lock_version: Mapped[int] = mapped_column(Integer, default=1)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Answer(Base, Timestamped):
    __tablename__ = "answer"
    __table_args__ = (UniqueConstraint("project_id", "question_code"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    question_code: Mapped[str] = mapped_column(String(40))
    value: Mapped[object] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="answered")  # answered|unknown|not_applicable|decide_later
    source: Mapped[str] = mapped_column(String(20), default="user")  # user | document
    source_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)  # fact id when accepted from a document
    author_id: Mapped[str] = mapped_column(String(36))


# ---------------------------------------------------------------- evidence
class SourceDocument(Base, Timestamped):
    __tablename__ = "source_document"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))
    mime: Mapped[str] = mapped_column(String(120))
    size: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(40), default="other")
    confidentiality: Mapped[str] = mapped_column(String(20), default="confidential")
    title: Mapped[str] = mapped_column(String(300), default="")
    doc_date: Mapped[str] = mapped_column(String(40), default="")
    ingestion_state: Mapped[str] = mapped_column(String(20), default="received")  # received|extracted|failed
    error: Mapped[str] = mapped_column(Text, default="")
    blob_path: Mapped[str] = mapped_column(String(500))
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    uploaded_by: Mapped[str] = mapped_column(String(36))


class EvidenceSegment(Base):
    __tablename__ = "evidence_segment"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_document.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    locator: Mapped[str] = mapped_column(String(200))  # e.g. "p. 3", "§ 4.2 Access control", "Sheet1!A1:F20"
    text_enc: Mapped[bytes] = mapped_column()  # encrypted text
    injection_flag: Mapped[bool] = mapped_column(Boolean, default=False)


class OrganizationFact(Base, Timestamped):
    __tablename__ = "organization_fact"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_document.id", ondelete="CASCADE"), index=True)
    segment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    fact_type: Mapped[str] = mapped_column(String(60))  # question code or parameter key
    label: Mapped[str] = mapped_column(String(300))
    value: Mapped[object] = mapped_column(JSON)
    quote: Mapped[str] = mapped_column(Text)  # short excerpt shown to the user
    locator: Mapped[str] = mapped_column(String(200))
    confidence: Mapped[str] = mapped_column(String(10), default="medium")
    extractor: Mapped[str] = mapped_column(String(40), default="rules-v1")
    state: Mapped[str] = mapped_column(String(20), default="proposed")  # proposed|confirmed|rejected
    conflict_group: Mapped[str | None] = mapped_column(String(80), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class ApplicabilityDecision(Base, Timestamped):
    __tablename__ = "applicability_decision"
    __table_args__ = (UniqueConstraint("project_id", "obligation_code"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    obligation_code: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30))  # applies | not_applicable | needs_legal_review
    rationale: Mapped[str] = mapped_column(Text, default="")
    reviewer_name: Mapped[str] = mapped_column(String(200))
    decided_by: Mapped[str] = mapped_column(String(36))
    ruleset_version: Mapped[str] = mapped_column(String(20))


# ---------------------------------------------------------------- policies
class PolicyDocument(Base, Timestamped):
    __tablename__ = "policy_document"
    __table_args__ = (UniqueConstraint("project_id", "policy_code"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    policy_code: Mapped[str] = mapped_column(String(40))  # catalogue code e.g. POL-IAM
    policy_id: Mapped[str] = mapped_column(String(60))  # document number e.g. ACME-POL-IAM-001
    selected: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(30), default="NOT_STARTED")  # NOT_STARTED|DRAFT_GENERATED|...
    current_version: Mapped[int] = mapped_column(Integer, default=0)
    stale: Mapped[bool] = mapped_column(Boolean, default=False)
    stale_reason: Mapped[str] = mapped_column(Text, default="")


class PolicyVersion(Base):
    __tablename__ = "policy_version"
    __table_args__ = (UniqueConstraint("document_id", "version_no", "language"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("policy_document.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(5))
    body: Mapped[dict] = mapped_column(JSON)
    inputs_used: Mapped[list] = mapped_column(JSON, default=list)  # question codes / fact ids the draft depends on
    generator: Mapped[dict] = mapped_column(JSON, default=dict)  # provider, model, prompt_version, generated_at
    draft_status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    created_by: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class PolicyClause(Base):
    __tablename__ = "policy_clause"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("policy_version.id", ondelete="CASCADE"), index=True)
    clause_id: Mapped[str] = mapped_column(String(80), index=True)
    section_id: Mapped[str] = mapped_column(String(60))
    number: Mapped[str] = mapped_column(String(20))
    text: Mapped[str] = mapped_column(Text)
    modality: Mapped[str] = mapped_column(String(10))
    source_type: Mapped[str] = mapped_column(String(40))
    source_ids: Mapped[list] = mapped_column(JSON, default=list)
    framework_refs: Mapped[list] = mapped_column(JSON, default=list)
    review_status: Mapped[str] = mapped_column(String(40))
    edited: Mapped[bool] = mapped_column(Boolean, default=False)


class Issue(Base, Timestamped):
    __tablename__ = "issue"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    clause_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    kind: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(10))  # high | medium | low
    message: Mapped[str] = mapped_column(Text)
    message_fr: Mapped[str] = mapped_column(Text, default="")
    suggestion: Mapped[str] = mapped_column(Text, default="")
    suggestion_fr: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | acknowledged | resolved
    resolution: Mapped[str] = mapped_column(Text, default="")
    decided_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class ExportJob(Base):
    __tablename__ = "export_job"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # docx | zip
    filename: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64))
    files: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    __tablename__ = "audit_event"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(60))
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)  # never raw source text
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
