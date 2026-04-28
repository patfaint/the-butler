"""Coffee cog — "Where's my coffee?" alert system."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from cogs.permissions import handle_check_failure, is_domme
from database.db import AsyncSessionLocal
from database.models import DommeProfile, GuildConfig, SubProfile
from utils.algorithms import calculate_coffee_amount
from utils.embeds import base_embed, error_embed

log = logging.getLogger("butler.coffee")


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
        """Calculate the dynamic coffee amount and DM all verified subs."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        async with AsyncSessionLocal() as session:
            # Load domme profile
            result = await session.execute(
                select(DommeProfile).where(
                    DommeProfile.discord_id == interaction.user.id,
                    DommeProfile.guild_id == interaction.guild.id,
                )
            )
            profile = result.scalar_one_or_none()

            if profile is None or not profile.setup_complete:
                await interaction.followup.send(
                    embed=error_embed(
                        "You need to complete `/setup` before sending a coffee alert, Mistress. 🎩"
                    ),
                    ephemeral=True,
                )
                return

            if profile.base_coffee_amount is None:
                await interaction.followup.send(
                    embed=error_embed(
                        "Your base coffee amount is not set. Please run `/setup` again. 🎩"
                    ),
                    ephemeral=True,
                )
                return

            # Calculate dynamic amount
            amount = calculate_coffee_amount(
                profile.base_coffee_amount,
                time_scaling=profile.time_scaling,
                day_scaling=profile.day_scaling,
                drought_scaling=profile.drought_scaling,
                last_coffee_at=profile.last_coffee_at,
            )

            # Update last coffee timestamp
            profile.last_coffee_at = datetime.now(timezone.utc)
            await session.commit()

            # Load guild config for sub_role_id and announcement channel
            cfg_result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == interaction.guild.id)
            )
            config = cfg_result.scalar_one_or_none()

            # Load verified subs
            sub_result = await session.execute(
                select(SubProfile).where(
                    SubProfile.guild_id == interaction.guild.id,
                    SubProfile.is_verified.is_(True),
                )
            )
            verified_subs = sub_result.scalars().all()

        domme_name = profile.display_name or interaction.user.display_name

        # Build the DM embed
        dm_embed = base_embed(
            "☕ Coffee Request",
            (
                f"**{domme_name}** is in need of coffee and has chosen you.\n\n"
                f"**Amount requested:** £{amount:.2f}\n\n"
                f"Your tribute awaits. Do not keep her waiting, darling. 🎩"
            ),
        )
        if isinstance(interaction.user, discord.Member):
            dm_embed.set_thumbnail(url=interaction.user.display_avatar.url)

        # DM verified subs
        dm_count = 0
        for sub_profile in verified_subs:
            member = interaction.guild.get_member(sub_profile.discord_id)
            if member is None:
                continue
            try:
                await member.send(embed=dm_embed)
                dm_count += 1
            except discord.Forbidden:
                log.debug("Could not DM sub %s — DMs closed.", member.id)

        # Also post to announcement channel if configured
        if config and config.announcement_channel_id:
            channel = interaction.guild.get_channel(config.announcement_channel_id)
            if isinstance(channel, discord.TextChannel):
                # Mention subs with the sub role if configured
                role_mention = ""
                if config.sub_role_id:
                    role = interaction.guild.get_role(config.sub_role_id)
                    if role:
                        role_mention = f"{role.mention} "

                public_embed = base_embed(
                    "☕ Coffee Time",
                    (
                        f"{role_mention}**{domme_name}** is seeking coffee.\n\n"
                        f"**Amount:** £{amount:.2f}\n\n"
                        "Subs — this is your moment. 🎩"
                    ),
                )
                if isinstance(interaction.user, discord.Member):
                    public_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                try:
                    await channel.send(embed=public_embed)
                except discord.Forbidden:
                    log.warning("Could not post to announcement channel %s.", config.announcement_channel_id)

        await interaction.followup.send(
            embed=base_embed(
                "☕ Coffee Alert Sent",
                f"Your coffee alert has been dispatched, Mistress.\n"
                f"**Amount:** £{amount:.2f}\n"
                f"**Subs notified:** {dm_count}",
            ),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoffeeCog(bot))

