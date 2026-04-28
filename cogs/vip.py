"""VIP cog — expiring VIP roles (stub for Phase 2)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from cogs.permissions import handle_check_failure, is_admin


class VIPCog(commands.Cog, name="VIP"):
    """Manages time-limited VIP roles."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VIPCog(bot))
