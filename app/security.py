"""Authentication, sessions, RBAC, tenant scoping, encryption at rest and audit logging."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.db import get_session
from app.models import AuditEvent, Membership, Project, SessionToken, User, now

COOKIE = "pb_session"
PBKDF2_ITER = 310_000

ROLE_RANK = {"auditor": 0, "reviewer": 1, "author": 2, "owner": 3, "admin": 4}


# ---------------------------------------------------------------- passwords
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITER)
    return f"pbkdf2_sha256${PBKDF2_ITER}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, it, salt_b64, dk_b64 = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt_b64), int(it))
        return hmac.compare_digest(dk, base64.b64decode(dk_b64))
    except Exception:
        return False


# ---------------------------------------------------------------- sessions
def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user_id: str, workspace_id: str) -> str:
    token = secrets.token_urlsafe(32)
    db.add(SessionToken(token_hash=_token_hash(token), user_id=user_id, workspace_id=workspace_id,
                        expires_at=now() + timedelta(hours=config.settings.session_hours)))
    db.commit()
    return token


def destroy_session(db: Session, token: str | None) -> None:
    if token:
        row = db.get(SessionToken, _token_hash(token))
        if row:
            db.delete(row)
            db.commit()


@dataclass
class Ctx:
    """The authenticated caller: user, tenant (workspace) and role."""
    user: User
    workspace_id: str
    role: str

    def require(self, minimum: str) -> None:
        if ROLE_RANK.get(self.role, -1) < ROLE_RANK[minimum]:
            raise HTTPException(403, "Your role does not allow this action.")


def current_ctx(request: Request, db: Session = Depends(get_session)) -> Ctx:
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, "Not signed in.")
    row = db.get(SessionToken, _token_hash(token))
    if not row:
        raise HTTPException(401, "Session expired.")
    exp = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=now().tzinfo)
    if exp < now():
        db.delete(row)
        db.commit()
        raise HTTPException(401, "Session expired.")
    user = db.get(User, row.user_id)
    m = db.scalar(select(Membership).where(Membership.user_id == row.user_id,
                                           Membership.workspace_id == row.workspace_id))
    if not user or not m:
        raise HTTPException(401, "No access to this workspace.")
    return Ctx(user=user, workspace_id=row.workspace_id, role=m.role)


def get_project(db: Session, ctx: Ctx, project_id: str) -> Project:
    """Tenant-scoped project lookup. Another tenant's project is indistinguishable from a missing one."""
    p = db.scalar(select(Project).where(Project.id == project_id, Project.workspace_id == ctx.workspace_id,
                                        Project.deleted_at.is_(None)))
    if not p:
        raise HTTPException(404, "Project not found.")
    return p


def scoped_get(db: Session, ctx: Ctx, model, obj_id: str):
    obj = db.get(model, obj_id)
    if not obj or getattr(obj, "workspace_id", None) != ctx.workspace_id:
        raise HTTPException(404, "Not found.")
    return obj


# ---------------------------------------------------------------- encryption at rest
_fernet: Fernet | None = None


def fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = config.settings.encryption_key
        if not key:
            key_file: Path = config.settings.data_dir / "pb-key"
            if not key_file.exists():
                key_file.write_bytes(Fernet.generate_key())
                os.chmod(key_file, 0o600)
            key = key_file.read_bytes().decode().strip()
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def reset_crypto() -> None:
    global _fernet
    _fernet = None


def encrypt(data: bytes) -> bytes:
    return fernet().encrypt(data)


def decrypt(token: bytes) -> bytes:
    return fernet().decrypt(token)


# ---------------------------------------------------------------- audit
def audit(db: Session, ctx: Ctx | None, action: str, entity: str, entity_id: str | None = None,
          project_id: str | None = None, workspace_id: str | None = None, **details) -> None:
    """Record a sensitive action. Never pass raw document text or secrets in details."""
    db.add(AuditEvent(workspace_id=workspace_id or (ctx.workspace_id if ctx else ""),
                      project_id=project_id, actor_id=ctx.user.id if ctx else None,
                      action=action, entity=entity, entity_id=entity_id, details=details))
