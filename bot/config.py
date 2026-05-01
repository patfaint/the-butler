from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from bot import channels


@dataclass(frozen=True)
class BotConfig:
    discord_token: str
    guild_id: int
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
    leaderboard_channel_id: int
    database_path: Path


def load_config() -> BotConfig:
    load_dotenv()

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Missing required environment variable: DISCORD_TOKEN")

    return BotConfig(
        discord_token=token,
        guild_id=channels.GUILD_ID,
        welcome_channel_id=channels.WELCOME_CHANNEL_ID,
        verification_channel_id=channels.VERIFICATION_CHANNEL_ID,
        verify_log_channel_id=channels.VERIFY_LOG_CHANNEL_ID,
        general_channel_id=channels.GENERAL_CHANNEL_ID,
        roles_channel_id=channels.ROLES_CHANNEL_ID,
        introductions_channel_id=channels.INTRODUCTIONS_CHANNEL_ID,
        unverified_role_id=channels.UNVERIFIED_ROLE_ID,
        verified_role_id=channels.VERIFIED_ROLE_ID,
        domme_role_id=channels.DOMME_ROLE_ID,
        submissive_role_id=channels.SUBMISSIVE_ROLE_ID,
        moderation_role_id=channels.MODERATION_ROLE_ID,
        leaderboard_channel_id=channels.LEADERBOARD_CHANNEL_ID,
        database_path=Path(os.getenv("DATABASE_PATH", "data/the_butler.sqlite3")),
    )
