"""Setup cog — Domme onboarding wizard (stub for Phase 2)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from cogs.permissions import handle_check_failure, is_domme


class SetupCog(commands.Cog, name="Setup"):
    """Domme profile setup wizard."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    @app_commands.command(
        name="setup",
        description="Configure your Butler profile. (Domme only)",
    )
    @is_domme()
    async def setup_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "🎩 The setup wizard is coming soon, Mistress. Stay tuned.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))
