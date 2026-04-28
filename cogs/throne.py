"""Throne cog — Throne link registry (stub for Phase 2)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from cogs.permissions import handle_check_failure, is_domme


class ThroneCog(commands.Cog, name="Throne"):
    """Register and display Domme Throne wishlist links."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    @app_commands.command(
        name="throne",
        description="Register or display your Throne wishlist link. (Domme only)",
    )
    @is_domme()
    async def throne_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "🎩 The Throne registry is coming soon, Mistress.",
            ephemeral=True,
        )

    @app_commands.command(
        name="wishlist",
        description="View a Domme's Throne wishlist link.",
    )
    async def wishlist_command(
        self,
        interaction: discord.Interaction,
        domme: discord.Member,
    ) -> None:
        await interaction.response.send_message(
            "🎩 Wishlist lookup is coming soon.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ThroneCog(bot))
