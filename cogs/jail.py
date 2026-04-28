"""Jail cog — jail and release members with role management and auto-release."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks
from sqlalchemy import select

from cogs.permissions import handle_check_failure, is_domme_or_admin
from database.db import AsyncSessionLocal
from database.models import GuildConfig, JailRecord
from utils.embeds import base_embed, error_embed, success_embed

log = logging.getLogger("butler.jail")


def _parse_duration(text: str) -> timedelta | None:
    """Parse a duration string like '1h', '30m', '2d', '1h30m' into a timedelta."""
    pattern = re.compile(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?$", re.IGNORECASE)
    match = pattern.match(text.strip())
    if not match or not any(match.groups()):
        return None
    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    total = timedelta(days=days, hours=hours, minutes=minutes)
    if total.total_seconds() <= 0:
        return None
    return total


class JailCog(commands.Cog, name="Jail"):
    """Jails and releases members."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._check_releases.start()

    def cog_unload(self) -> None:
        self._check_releases.cancel()

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    # ── /jail ─────────────────────────────────────────────────────────────────

    @app_commands.command(
        name="jail",
        description="Send a member to jail. (Domme/Admin only)",
    )
    @is_domme_or_admin()
    async def jail_command(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        duration: str,
        reason: str = "No reason provided.",
    ) -> None:
        """Assign the jail role, strip other roles, and log the sentence."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        delta = _parse_duration(duration)
        if delta is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid duration format. Use combinations of d/h/m — e.g. `1h`, `30m`, `2d`, `1h30m`. 🎩"
                ),
                ephemeral=True,
            )
            return

        async with AsyncSessionLocal() as session:
            cfg_result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == interaction.guild.id)
            )
            config = cfg_result.scalar_one_or_none()

        if config is None or config.jail_role_id is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "The jail role has not been configured. An admin must run `/setjailrole` first. 🎩"
                ),
                ephemeral=True,
            )
            return

        jail_role = interaction.guild.get_role(config.jail_role_id)
        if jail_role is None:
            await interaction.response.send_message(
                embed=error_embed("The configured jail role no longer exists. 🎩"),
                ephemeral=True,
            )
            return

        # Already jailed?
        if jail_role in user.roles:
            await interaction.response.send_message(
                embed=error_embed(f"{user.mention} is already in jail, darling. 🎩"),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Save current roles (excluding @everyone and the jail role itself)
        saved_role_ids = [
            r.id for r in user.roles
            if r.id != interaction.guild.default_role.id and r.id != jail_role.id
        ]

        # Strip all assignable roles and add jail role
        try:
            roles_to_remove = [r for r in user.roles if r != interaction.guild.default_role and r != jail_role]
            await user.remove_roles(*roles_to_remove, reason=f"Jailed by {interaction.user}")
            await user.add_roles(jail_role, reason=f"Jailed by {interaction.user}: {reason}")
        except discord.Forbidden:
            await interaction.followup.send(
                embed=error_embed("I don't have permission to manage that member's roles. 🎩"),
                ephemeral=True,
            )
            return

        release_at = datetime.now(timezone.utc) + delta

        async with AsyncSessionLocal() as session:
            record = JailRecord(
                guild_id=interaction.guild.id,
                user_id=user.id,
                jailed_by=interaction.user.id,
                reason=reason,
                release_at=release_at,
                released=False,
            )
            record.saved_roles = saved_role_ids
            session.add(record)
            await session.commit()

        # DM the jailed user
        try:
            await user.send(
                embed=base_embed(
                    "🔒 You Have Been Jailed",
                    (
                        f"**Reason:** {reason}\n"
                        f"**Release:** <t:{int(release_at.timestamp())}:R>\n\n"
                        "Reflect on your behaviour. 🎩"
                    ),
                )
            )
        except discord.Forbidden:
            pass

        duration_text = duration.strip()
        await interaction.followup.send(
            embed=success_embed(
                f"{user.mention} has been sent to jail for **{duration_text}**.\n"
                f"**Reason:** {reason}\n"
                f"**Release:** <t:{int(release_at.timestamp())}:R> 🎩"
            ),
            ephemeral=True,
        )

    # ── /release ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="release",
        description="Release a member from jail early. (Domme/Admin only)",
    )
    @is_domme_or_admin()
    async def release_command(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ) -> None:
        """Remove the jail role and restore the member's saved roles."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        released = await self._release_member(interaction.guild, user.id)

        if not released:
            await interaction.followup.send(
                embed=error_embed(f"{user.mention} is not currently in jail. 🎩"),
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            embed=success_embed(f"{user.mention} has been released from jail. 🎩"),
            ephemeral=True,
        )

    # ── Auto-release loop ─────────────────────────────────────────────────────

    @tasks.loop(minutes=1)
    async def _check_releases(self) -> None:
        """Automatically release members whose jail sentences have expired."""
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(JailRecord).where(
                    JailRecord.released.is_(False),
                    JailRecord.release_at <= now,
                )
            )
            due_records = result.scalars().all()

        for record in due_records:
            guild = self.bot.get_guild(record.guild_id)
            if guild is None:
                continue
            await self._release_member(guild, record.user_id, record_id=record.id)

    @_check_releases.before_loop
    async def _before_check(self) -> None:
        await self.bot.wait_until_ready()

    # ── Helper ────────────────────────────────────────────────────────────────

    async def _release_member(
        self,
        guild: discord.Guild,
        user_id: int,
        *,
        record_id: int | None = None,
    ) -> bool:
        """Release a member from jail. Returns True if a record was found and processed."""
        async with AsyncSessionLocal() as session:
            query = (
                select(GuildConfig).where(GuildConfig.guild_id == guild.id)
            )
            cfg_result = await session.execute(query)
            config = cfg_result.scalar_one_or_none()

            query2 = select(JailRecord).where(
                JailRecord.guild_id == guild.id,
                JailRecord.user_id == user_id,
                JailRecord.released.is_(False),
            )
            if record_id is not None:
                query2 = query2.where(JailRecord.id == record_id)
            else:
                query2 = query2.order_by(JailRecord.jailed_at.desc()).limit(1)

            rec_result = await session.execute(query2)
            record = rec_result.scalar_one_or_none()

            if record is None:
                return False

            record.released = True
            saved_roles = record.saved_roles
            await session.commit()

        member = guild.get_member(user_id)
        if member is None:
            return True  # Recorded as released even if member left

        # Remove jail role
        if config and config.jail_role_id:
            jail_role = guild.get_role(config.jail_role_id)
            if jail_role and jail_role in member.roles:
                try:
                    await member.remove_roles(jail_role, reason="Jail sentence served.")
                except discord.Forbidden:
                    log.warning("Could not remove jail role from %s.", user_id)

        # Restore saved roles
        roles_to_restore = [
            guild.get_role(rid) for rid in saved_roles
        ]
        valid_roles = [r for r in roles_to_restore if r is not None]
        if valid_roles:
            try:
                await member.add_roles(*valid_roles, reason="Released from jail.")
            except discord.Forbidden:
                log.warning("Could not restore roles for %s.", user_id)

        # DM the released member
        try:
            await member.send(
                embed=base_embed(
                    "🔓 You Have Been Released",
                    "Your sentence has been served. Behave yourself. 🎩",
                )
            )
        except discord.Forbidden:
            pass

        return True


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JailCog(bot))

