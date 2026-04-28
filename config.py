"""Configuration loader — reads all secrets from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Return an env var or raise a clear error if it is missing."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{key}' is not set. "
            "Check your .env file or AWS environment configuration."
        )
    return value


# ── Discord ───────────────────────────────────────────────────────────────────
DISCORD_TOKEN: str = _require("DISCORD_TOKEN")
GUILD_ID: int = int(_require("GUILD_ID"))

# ── External APIs ─────────────────────────────────────────────────────────────
TENOR_API_KEY: str = os.getenv("TENOR_API_KEY", "")

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///./butler.db"
)
