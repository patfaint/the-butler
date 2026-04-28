"""Trivia cog — trivia game (stub for Phase 2)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from cogs.permissions import handle_check_failure


class TriviaCog(commands.Cog, name="Trivia"):
    """Hosts trivia games in the server."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    @app_commands.command(
        name="trivia",
        description="Start a trivia game.",
    )
    async def trivia_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "🎭 Trivia is coming soon. Stay tuned!",
            ephemeral=True,
        )

    @app_commands.command(
        name="meme",
        description="Get a random meme GIF.",
    )
    async def meme_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "🎭 Meme GIFs are coming soon!",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TriviaCog(bot))
