"""Runtime configuration, read from environment variables (and an optional .env file)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

APP_NAME = "CyberRiskGuardian Policy Builder"
APP_VERSION = "0.1.0-beta"
BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / ".env")


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("PB_DATA_DIR", BASE_DIR / "data")))
    database_url: str = field(default_factory=lambda: os.environ.get("PB_DATABASE_URL", ""))
    host: str = field(default_factory=lambda: os.environ.get("PB_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.environ.get("PB_PORT", "8120")))
    ai_provider: str = field(default_factory=lambda: os.environ.get("PB_AI_PROVIDER", "mock"))  # mock | anthropic
    ai_model: str = field(default_factory=lambda: os.environ.get("PB_AI_MODEL", "claude-sonnet-5-5"))
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    ai_max_tokens: int = field(default_factory=lambda: int(os.environ.get("PB_AI_MAX_TOKENS", "4000")))
    ai_timeout_s: float = field(default_factory=lambda: float(os.environ.get("PB_AI_TIMEOUT", "90")))
    max_upload_mb: int = field(default_factory=lambda: int(os.environ.get("PB_MAX_UPLOAD_MB", "20")))
    session_hours: int = field(default_factory=lambda: int(os.environ.get("PB_SESSION_HOURS", "12")))
    encryption_key: str = field(default_factory=lambda: os.environ.get("PB_ENCRYPTION_KEY", ""))
    secure_cookies: bool = field(default_factory=lambda: os.environ.get("PB_SECURE_COOKIES", "0") == "1")

    def __post_init__(self) -> None:
        self.data_dir = Path(self.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.database_url:
            self.database_url = f"sqlite:///{self.data_dir / 'policybuilder.db'}"

    @property
    def blob_dir(self) -> Path:
        p = self.data_dir / "blobs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def export_dir(self) -> Path:
        p = self.data_dir / "exports"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def ai_available(self) -> bool:
        return self.ai_provider == "anthropic" and bool(self.anthropic_api_key)


settings = Settings()


def reset_settings(**overrides) -> Settings:
    """Used by tests: rebuild settings with overrides."""
    global settings
    for k, v in overrides.items():
        os.environ[k] = str(v)
    settings = Settings()
    return settings
