"""Shared database helper utilities used across cogs."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import GuildConfig


async def get_or_create_guild_config(session: AsyncSession, guild_id: int) -> GuildConfig:
    """Return the GuildConfig for *guild_id*, creating one if it doesn't exist.

    The caller is responsible for committing the session to persist any new row.
    """
    result = await session.execute(
        select(GuildConfig).where(GuildConfig.guild_id == guild_id)
    )
    config = result.scalar_one_or_none()
    if config is None:
        config = GuildConfig(guild_id=guild_id)
        session.add(config)
    return config
