"""VIP cog — expiring VIP roles with APScheduler-based expiry."""

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
from database.models import GuildConfig, VIPRole
from utils.embeds import base_embed, error_embed, success_embed

log = logging.getLogger("butler.vip")


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


class VIPCog(commands.Cog, name="VIP"):
    """Manages time-limited VIP roles."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._check_vip_expiry.start()

    def cog_unload(self) -> None:
        self._check_vip_expiry.cancel()

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    # ── /givevip ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="givevip",
        description="Grant a member a time-limited VIP role. (Domme/Admin only)",
    )
    @is_domme_or_admin()
    async def givevip_command(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: str,
    ) -> None:
        """Assign the VIP role to a member for a specified duration."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        delta = _parse_duration(duration)
        if delta is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid duration. Use combinations of d/h/m — e.g. `7d`, `1h`, `30m`. 🎩"
                ),
                ephemeral=True,
            )
            return

        async with AsyncSessionLocal() as session:
            cfg_result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == interaction.guild.id)
            )
            config = cfg_result.scalar_one_or_none()

        if config is None or config.vip_role_id is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "The VIP role has not been configured. An admin must set `vip_role_id` first. 🎩"
                ),
                ephemeral=True,
            )
            return

        vip_role = interaction.guild.get_role(config.vip_role_id)
        if vip_role is None:
            await interaction.response.send_message(
                embed=error_embed("The configured VIP role no longer exists. 🎩"),
                ephemeral=True,
            )
            return

        expires_at = datetime.now(timezone.utc) + delta

        try:
            await member.add_roles(vip_role, reason=f"VIP granted by {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed("I don't have permission to assign that role. 🎩"),
                ephemeral=True,
            )
            return

        async with AsyncSessionLocal() as session:
            vip_record = VIPRole(
                guild_id=interaction.guild.id,
                user_id=member.id,
                role_id=vip_role.id,
                expires_at=expires_at,
            )
            session.add(vip_record)
            await session.commit()

        try:
            await member.send(
                embed=base_embed(
                    "⭐ VIP Status Granted",
                    (
                        f"You have been granted the **{vip_role.name}** role.\n"
                        f"**Expires:** <t:{int(expires_at.timestamp())}:R> 🎩"
                    ),
                )
            )
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            embed=success_embed(
                f"{member.mention} has been granted **{vip_role.name}** for **{duration}**.\n"
                f"**Expires:** <t:{int(expires_at.timestamp())}:R> 🎩"
            ),
            ephemeral=True,
        )

    # ── Expiry checker ────────────────────────────────────────────────────────

    @tasks.loop(minutes=5)
    async def _check_vip_expiry(self) -> None:
        """Remove VIP roles from members whose grants have expired."""
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(VIPRole).where(VIPRole.expires_at <= now)
            )
            expired = result.scalars().all()

            for record in expired:
                guild = self.bot.get_guild(record.guild_id)
                if guild is None:
                    await session.delete(record)
                    continue

                member = guild.get_member(record.user_id)
                role = guild.get_role(record.role_id)

                if member and role and role in member.roles:
                    try:
                        await member.remove_roles(role, reason="VIP role expired.")
                    except discord.Forbidden:
                        log.warning("Could not remove VIP role from %s.", record.user_id)

                    try:
                        await member.send(
                            embed=base_embed(
                                "⭐ VIP Status Expired",
                                f"Your **{role.name}** VIP status has expired. 🎩",
                            )
                        )
                    except discord.Forbidden:
                        pass

                await session.delete(record)

            await session.commit()

    @_check_vip_expiry.before_loop
    async def _before_check(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VIPCog(bot))

