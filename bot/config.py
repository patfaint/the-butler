from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class BotConfig:
    discord_token: str
    guild_id: int | None
    welcome_channel_id: int
    verification_channel_id: int
    verify_log_channel_id: int
    general_channel_id: int
    roles_channel_id: int
    introductions_channel_id: int
    unverified_role_id: int
    verified_role_id: int
    domme_role_id: int
    submissive_role_id: int
    moderation_role_id: int
    database_path: Path


def load_config() -> BotConfig:
    load_dotenv()

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Missing required environment variable: DISCORD_TOKEN")

    return BotConfig(
        discord_token=token,
        guild_id=_optional_int("GUILD_ID"),
        welcome_channel_id=_required_int("WELCOME_CHANNEL_ID"),
        verification_channel_id=_required_int("VERIFICATION_CHANNEL_ID"),
        verify_log_channel_id=_required_int("VERIFY_LOG_CHANNEL_ID"),
        general_channel_id=_required_int("GENERAL_CHANNEL_ID"),
        roles_channel_id=_required_int("ROLES_CHANNEL_ID"),
        introductions_channel_id=_required_int("INTRODUCTIONS_CHANNEL_ID"),
        unverified_role_id=_required_int("UNVERIFIED_ROLE_ID"),
        verified_role_id=_required_int("VERIFIED_ROLE_ID"),
        domme_role_id=_required_int("DOMME_ROLE_ID"),
        submissive_role_id=_required_int("SUBMISSIVE_ROLE_ID"),
        moderation_role_id=_required_int("MODERATION_ROLE_ID"),
        database_path=Path(os.getenv("DATABASE_PATH", "data/the_butler.sqlite3")),
    )


def _optional_int(name: str) -> int | None:
    value = os.getenv(name)
    if not value:
        return None
    return _parse_int(name, value)


def _required_int(name: str) -> int:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return _parse_int(name, value)


def _parse_int(name: str, value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer") from exc
