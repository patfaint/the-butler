"""Coffee cog — "Where's my coffee" alert system (stub for Phase 2)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from cogs.permissions import handle_check_failure, is_domme


class CoffeeCog(commands.Cog, name="Coffee"):
    """Coffee alert DM system for Dommes."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    @app_commands.command(
        name="coffee",
        description="Alert all subs that you're seeking coffee. (Domme only)",
    )
    @is_domme()
    async def coffee_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "☕ The coffee alert system is coming soon, Mistress.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoffeeCog(bot))
