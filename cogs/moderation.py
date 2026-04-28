"""Moderation cog — /timeout command and admin /set* configuration commands."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from cogs.permissions import handle_check_failure, is_admin, is_mod_or_domme
from database.db import AsyncSessionLocal
from database.helpers import get_or_create_guild_config
from database.models import GuildConfig
from utils.embeds import success_embed

log = logging.getLogger("butler.moderation")

_MAX_TIMEOUT_MINUTES = 40320  # 28 days


class ModerationCog(commands.Cog, name="Moderation"):
    """Admin configuration and moderation commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    # ── /timeout ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="timeout",
        description="Timeout a user. (Mod/Domme only)",
    )
    @is_mod_or_domme()
    async def timeout_command(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        duration: app_commands.Range[int, 1, _MAX_TIMEOUT_MINUTES],
        reason: str | None = None,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        invoker = interaction.user
        if not isinstance(invoker, discord.Member):
            await interaction.response.send_message("Could not resolve your member details.", ephemeral=True)
            return

        # Dommes may only timeout users with the Sub role
        invoker_is_admin = invoker.guild_permissions.administrator
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == interaction.guild.id)
            )
            config = result.scalar_one_or_none()

        domme_role_id = config.domme_role_id if config else None
        sub_role_id = config.sub_role_id if config else None
        mod_role_id = config.mod_role_id if config else None

        invoker_is_mod = invoker_is_admin or (
            mod_role_id is not None and any(r.id == mod_role_id for r in invoker.roles)
        )
        invoker_is_domme = domme_role_id is not None and any(r.id == domme_role_id for r in invoker.roles)

        if invoker_is_domme and not invoker_is_mod:
            target_is_sub = sub_role_id is not None and any(r.id == sub_role_id for r in user.roles)
            if not target_is_sub:
                await interaction.response.send_message(
                    "You can only use this on subs.", ephemeral=True
                )
                return

        # Apply the Discord timeout
        until = datetime.now(timezone.utc) + timedelta(minutes=duration)
        try:
            await user.edit(timed_out_until=until, reason=reason or "No reason provided.")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to timeout that user.", ephemeral=True
            )
            return

        # Format duration string
        if duration >= 1440:
            duration_str = f"{duration // 1440}d {duration % 1440 // 60}h" if duration % 1440 else f"{duration // 1440}d"
        elif duration >= 60:
            duration_str = f"{duration // 60}h {duration % 60}m" if duration % 60 else f"{duration // 60}h"
        else:
            duration_str = f"{duration}m"

        reason_str = reason if reason else "No reason provided"
        await interaction.response.send_message(
            f"{user.mention} has been timed out for **{duration_str}** by {invoker.mention}. "
            f"Reason: {reason_str}"
        )

    # ── Channel setters ───────────────────────────────────────────────────────

    @app_commands.command(
        name="setwelcomechannel",
        description="Set the welcome channel. (Admin only)",
    )
    @is_admin()
    async def set_welcome_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.welcome_channel_id = channel.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Welcome channel set to {channel.mention}. 🎩"),
            ephemeral=True,
        )

    @app_commands.command(
        name="setleaderboardchannel",
        description="Set the leaderboard channel. (Admin only)",
    )
    @is_admin()
    async def set_leaderboard_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.leaderboard_channel_id = channel.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Leaderboard channel set to {channel.mention}. 🎩"),
            ephemeral=True,
        )

    # ── Role setters ──────────────────────────────────────────────────────────

    @app_commands.command(
        name="setdommerole",
        description="Set the Domme role. (Admin only)",
    )
    @is_admin()
    async def set_domme_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.domme_role_id = role.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Domme role set to {role.mention}. 🎩"),
            ephemeral=True,
        )

    @app_commands.command(
        name="setsubrole",
        description="Set the Sub role. (Admin only)",
    )
    @is_admin()
    async def set_sub_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.sub_role_id = role.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Sub role set to {role.mention}. 🎩"),
            ephemeral=True,
        )

    @app_commands.command(
        name="setjailrole",
        description="Set the jail role. (Admin only)",
    )
    @is_admin()
    async def set_jail_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.jail_role_id = role.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Jail role set to {role.mention}. 🎩"),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModerationCog(bot))
