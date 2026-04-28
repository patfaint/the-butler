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
# Private module-level reads — do NOT use these directly outside this module.
# Use require_discord_token() and require_guild_id() instead, which validate
# that the values are set before the bot connects.
_DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN")
_guild_id_raw = os.getenv("GUILD_ID")
_GUILD_ID: int | None = int(_guild_id_raw) if _guild_id_raw else None


def require_discord_token() -> str:
    """Return the Discord token, validating it is set (call only at bot startup)."""
    return _require("DISCORD_TOKEN")


def require_guild_id() -> int:
    """Return the Discord guild ID, validating it is set (call only at bot startup)."""
    return int(_require("GUILD_ID"))


# ── External APIs ─────────────────────────────────────────────────────────────
TENOR_API_KEY: str = os.getenv("TENOR_API_KEY", "")

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///./butler.db"
)
