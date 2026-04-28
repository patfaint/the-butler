"""Verification cog — new member onboarding quiz (stub for Phase 2)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from cogs.permissions import handle_check_failure, is_admin
from database.db import AsyncSessionLocal
from database.helpers import get_or_create_guild_config
from utils.embeds import success_embed


class VerificationCog(commands.Cog, name="Verification"):
    """Handles new member verification flow."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    @app_commands.command(
        name="setverificationchannel",
        description="Set the verification channel. (Admin only)",
    )
    @is_admin()
    async def set_verification_channel(
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
            config.verification_channel_id = channel.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Verification channel set to {channel.mention}. 🎩"),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationCog(bot))
