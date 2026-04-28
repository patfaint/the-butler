"""Tribute cog — tribute logging and leaderboard (stub for Phase 2)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from cogs.permissions import handle_check_failure, is_domme


class TributeCog(commands.Cog, name="Tribute"):
    """Tribute logging, confirmation, and leaderboard."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    @app_commands.command(
        name="tribute",
        description="Log a tribute to a Domme.",
    )
    async def tribute_command(
        self,
        interaction: discord.Interaction,
        domme: discord.Member,
        amount: float,
    ) -> None:
        await interaction.response.send_message(
            "💸 Tribute logging is coming soon.",
            ephemeral=True,
        )

    @app_commands.command(
        name="confirm",
        description="Confirm a sub's tribute. (Domme only)",
    )
    @is_domme()
    async def confirm_command(
        self,
        interaction: discord.Interaction,
        sub: discord.Member,
        amount: float,
    ) -> None:
        await interaction.response.send_message(
            "✅ Tribute confirmation is coming soon, Mistress.",
            ephemeral=True,
        )

    @app_commands.command(
        name="leaderboard",
        description="View the server tribute leaderboard.",
    )
    async def leaderboard_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "🏆 The leaderboard is coming soon.",
            ephemeral=True,
        )

    @app_commands.command(
        name="stats",
        description="View your personal tribute stats.",
    )
    async def stats_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "📊 Personal stats are coming soon.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TributeCog(bot))
