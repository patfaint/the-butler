"""Jail cog — jail system (stub for Phase 2)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from cogs.permissions import handle_check_failure, is_domme_or_admin


class JailCog(commands.Cog, name="Jail"):
    """Jails and releases members."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

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
        await interaction.response.send_message(
            f"🔒 The jail system is coming soon. {user.mention} got lucky — for now.",
            ephemeral=True,
        )

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
        await interaction.response.send_message(
            "🔓 Early release is coming soon.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JailCog(bot))
