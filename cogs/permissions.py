"""Permissions system — reusable checks and decorators for all cogs."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from database.db import AsyncSessionLocal
from database.models import GuildConfig

T = TypeVar("T")

# ── Butler error messages ─────────────────────────────────────────────────────

_MSG_DOMME_ONLY = "I'm afraid that command is reserved for the Dommes, darling. 🎩"
_MSG_SUB_ONLY = "That command is for the subs only, I'm afraid. 🎩"
_MSG_ADMIN_ONLY = "You don't have the authority for that, I'm afraid. 🎩"
_MSG_VERIFIED_ONLY = (
    "You'll need to complete the verification process first, darling. 🎩"
)
_MSG_COOLDOWN = "Please slow down. The Butler operates at his own pace. 🎩"


# ── Guild config helper ───────────────────────────────────────────────────────

async def _get_guild_config(guild_id: int) -> GuildConfig | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(GuildConfig).where(GuildConfig.guild_id == guild_id)
        )
        return result.scalar_one_or_none()


# ── Role helpers ──────────────────────────────────────────────────────────────

def _member_has_role(member: discord.Member, role_id: int | None) -> bool:
    if role_id is None:
        return False
    return any(r.id == role_id for r in member.roles)


async def _member_is_domme(member: discord.Member) -> bool:
    config = await _get_guild_config(member.guild.id)
    if config is None:
        return False
    return _member_has_role(member, config.domme_role_id)


async def _member_is_sub(member: discord.Member) -> bool:
    config = await _get_guild_config(member.guild.id)
    if config is None:
        return False
    return _member_has_role(member, config.sub_role_id)


async def _member_is_admin(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    config = await _get_guild_config(member.guild.id)
    if config is None:
        return False
    return _member_has_role(member, config.admin_role_id)


# ── App-command check decorators ──────────────────────────────────────────────

def _ephemeral_error(message: str) -> app_commands.CheckFailure:
    """Wrap a denial message in a CheckFailure so the error handler can send it."""
    error = app_commands.CheckFailure(message)
    return error


def is_domme() -> Callable[..., Any]:
    """Slash-command check: the invoking member must have the configured Domme role."""

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise _ephemeral_error(_MSG_DOMME_ONLY)
        if await _member_is_domme(interaction.user):
            return True
        raise _ephemeral_error(_MSG_DOMME_ONLY)

    return app_commands.check(predicate)


def is_sub() -> Callable[..., Any]:
    """Slash-command check: the invoking member must have the configured Sub role."""

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise _ephemeral_error(_MSG_SUB_ONLY)
        if await _member_is_sub(interaction.user):
            return True
        raise _ephemeral_error(_MSG_SUB_ONLY)

    return app_commands.check(predicate)


def is_admin() -> Callable[..., Any]:
    """Slash-command check: the invoking member must be an admin."""

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise _ephemeral_error(_MSG_ADMIN_ONLY)
        if await _member_is_admin(interaction.user):
            return True
        raise _ephemeral_error(_MSG_ADMIN_ONLY)

    return app_commands.check(predicate)


def is_domme_or_admin() -> Callable[..., Any]:
    """Slash-command check: the invoking member is a domme OR an admin."""

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise _ephemeral_error(_MSG_DOMME_ONLY)
        member = interaction.user
        if await _member_is_domme(member) or await _member_is_admin(member):
            return True
        raise _ephemeral_error(_MSG_DOMME_ONLY)

    return app_commands.check(predicate)


def is_verified() -> Callable[..., Any]:
    """Slash-command check: the invoking member has completed the verification quiz."""
    from database.models import SubProfile  # avoid circular import at module level

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise _ephemeral_error(_MSG_VERIFIED_ONLY)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SubProfile).where(
                    SubProfile.discord_id == interaction.user.id,
                    SubProfile.guild_id == interaction.guild_id,
                )
            )
            profile = result.scalar_one_or_none()
        if profile and profile.is_verified:
            return True
        raise _ephemeral_error(_MSG_VERIFIED_ONLY)

    return app_commands.check(predicate)


# ── In-memory rate limiter ────────────────────────────────────────────────────

# user_id → list of timestamps of recent invocations
_rate_limit_buckets: dict[str, list[float]] = defaultdict(list)


def cooldown(seconds: float, max_uses: int = 1) -> Callable[..., Any]:
    """Rate-limit a slash command to *max_uses* uses per *seconds* window per user."""

    async def predicate(interaction: discord.Interaction) -> bool:
        bucket_key = f"{interaction.command.name if interaction.command else 'unknown'}:{interaction.user.id}"
        now = time.monotonic()
        window_start = now - seconds
        timestamps = _rate_limit_buckets[bucket_key]
        # Prune old timestamps
        _rate_limit_buckets[bucket_key] = [t for t in timestamps if t > window_start]
        if len(_rate_limit_buckets[bucket_key]) >= max_uses:
            raise _ephemeral_error(_MSG_COOLDOWN)
        _rate_limit_buckets[bucket_key].append(now)
        return True

    return app_commands.check(predicate)


# ── Global error handler helper ───────────────────────────────────────────────

async def handle_check_failure(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    """Send the permission denial message ephemerally to the user.

    Wire this up in each cog's ``cog_app_command_error`` method.
    """
    if isinstance(error, app_commands.CheckFailure):
        message = str(error) if str(error) else _MSG_ADMIN_ONLY
        embed = discord.Embed(description=f"🎩 {message}", colour=0xFF69B4)
        embed.set_footer(text="The Butler — At your service. 🎩")
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        raise error
