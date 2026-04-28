"""Verification cog — button-based member verification flow."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from cogs.permissions import handle_check_failure, is_admin
from database.db import AsyncSessionLocal
from database.models import GuildConfig, SubProfile
from utils.embeds import base_embed, error_embed, success_embed

log = logging.getLogger("butler.verification")

_RULES = (
    "1️⃣ You must be **18 years or older** to participate in this server.\n"
    "2️⃣ All interactions must be **consensual** — no means no.\n"
    "3️⃣ **Respect everyone's limits** — Dommes, subs, and observers alike.\n"
    "4️⃣ No sharing of personal information without explicit consent.\n"
    "5️⃣ No unsolicited DMs — get permission first.\n"
    "6️⃣ What happens in this server stays in this server — no screenshots.\n"
    "7️⃣ The Butler's decisions are final. 🎩"
)


# ── Verification Button View ──────────────────────────────────────────────────

class VerificationView(discord.ui.View):
    """Persistent view with the 'I Agree' verification button."""

    def __init__(self) -> None:
        super().__init__(timeout=None)  # Persistent across restarts

    @discord.ui.button(
        label="✅ I Agree — Verify Me",
        style=discord.ButtonStyle.success,
        custom_id="butler:verify",
    )
    async def verify_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """Mark the member as verified in the database and assign the sub role if configured."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This can only be used in a server.", ephemeral=True
            )
            return

        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Unable to verify at this time. Please try again. 🎩", ephemeral=True
            )
            return

        async with AsyncSessionLocal() as session:
            # Check if already verified
            result = await session.execute(
                select(SubProfile).where(
                    SubProfile.discord_id == interaction.user.id,
                    SubProfile.guild_id == interaction.guild.id,
                )
            )
            profile = result.scalar_one_or_none()
            if profile and profile.is_verified:
                await interaction.response.send_message(
                    embed=base_embed(
                        "🎩 Already Verified",
                        "You're already verified, darling. Welcome back. 🎩",
                    ),
                    ephemeral=True,
                )
                return

            # Create or update profile
            if profile is None:
                profile = SubProfile(
                    discord_id=interaction.user.id,
                    guild_id=interaction.guild.id,
                    username=interaction.user.display_name,
                )
                session.add(profile)
            profile.is_verified = True
            profile.username = interaction.user.display_name

            # Load guild config for sub role
            cfg_result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == interaction.guild.id)
            )
            config = cfg_result.scalar_one_or_none()
            await session.commit()

        # Assign the sub role if configured
        if config and config.sub_role_id:
            sub_role = interaction.guild.get_role(config.sub_role_id)
            if sub_role:
                try:
                    await interaction.user.add_roles(
                        sub_role, reason="Member completed verification."
                    )
                except discord.Forbidden:
                    log.warning(
                        "Could not assign sub role to %s — missing permissions.",
                        interaction.user.id,
                    )

        await interaction.response.send_message(
            embed=success_embed(
                "You have been verified and welcomed to The Drain Server. 🎩\n\n"
                "Choose your roles, explore the channels, and remember — respect is everything."
            ),
            ephemeral=True,
        )


# ── Cog ───────────────────────────────────────────────────────────────────────

class VerificationCog(commands.Cog, name="Verification"):
    """Handles new member verification flow."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Register the persistent view so it survives bot restarts
        bot.add_view(VerificationView())

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
            result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == interaction.guild.id)
            )
            config = result.scalar_one_or_none()
            if config is None:
                from database.helpers import get_or_create_guild_config
                config = await get_or_create_guild_config(session, interaction.guild.id)
            config.verification_channel_id = channel.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Verification channel set to {channel.mention}. 🎩"),
            ephemeral=True,
        )

    @app_commands.command(
        name="sendverification",
        description="Post the verification embed with button to the verification channel. (Admin only)",
    )
    @is_admin()
    async def send_verification(self, interaction: discord.Interaction) -> None:
        """Post the verification rules embed with the agree button."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == interaction.guild.id)
            )
            config = result.scalar_one_or_none()

        if config is None or config.verification_channel_id is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Verification channel not set. Run `/setverificationchannel` first. 🎩"
                ),
                ephemeral=True,
            )
            return

        channel = interaction.guild.get_channel(config.verification_channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                embed=error_embed("The configured verification channel could not be found. 🎩"),
                ephemeral=True,
            )
            return

        embed = base_embed(
            "🔒 Server Verification",
            (
                "Welcome to **The Drain Server**.\n\n"
                "Before you can access this community, you must read and agree to the following rules:\n\n"
                f"{_RULES}\n\n"
                "By clicking the button below you confirm that you are **18 or older** "
                "and that you agree to abide by these rules. 🎩"
            ),
        )
        await channel.send(embed=embed, view=VerificationView())
        await interaction.response.send_message(
            embed=success_embed(f"Verification embed posted to {channel.mention}. 🎩"),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationCog(bot))

