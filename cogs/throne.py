"""Throne cog — Throne link registry."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from cogs.permissions import handle_check_failure, is_domme
from database.db import AsyncSessionLocal
from database.models import DommeProfile
from utils.embeds import base_embed, error_embed, success_embed


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
        description="Register or update your Throne wishlist link. (Domme only)",
    )
    @is_domme()
    async def throne_command(
        self,
        interaction: discord.Interaction,
        link: str,
    ) -> None:
        """Set or update the Domme's Throne wishlist link."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        # Normalise URL
        url = link.strip()
        if url and not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DommeProfile).where(
                    DommeProfile.discord_id == interaction.user.id,
                    DommeProfile.guild_id == interaction.guild.id,
                )
            )
            profile = result.scalar_one_or_none()
            if profile is None:
                profile = DommeProfile(
                    discord_id=interaction.user.id,
                    guild_id=interaction.guild.id,
                )
                session.add(profile)
            profile.throne_link = url
            await session.commit()

        await interaction.response.send_message(
            embed=success_embed(f"Your Throne link has been updated, Mistress. 🎩\n{url}"),
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
        """Look up a Domme's registered Throne wishlist link."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DommeProfile).where(
                    DommeProfile.discord_id == domme.id,
                    DommeProfile.guild_id == interaction.guild.id,
                )
            )
            profile = result.scalar_one_or_none()

        if profile is None or not profile.throne_link:
            await interaction.response.send_message(
                embed=error_embed(
                    f"{domme.display_name} has not registered a Throne link yet. 🎩"
                ),
                ephemeral=True,
            )
            return

        name = profile.display_name or domme.display_name
        embed = base_embed(
            f"🎁 {name}'s Wishlist",
            f"Treat her well, darling.\n\n**Throne:** {profile.throne_link}",
        )
        embed.set_thumbnail(url=domme.display_avatar.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ThroneCog(bot))

