"""Setup cog — Domme onboarding wizard using a Discord Modal."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from cogs.permissions import handle_check_failure, is_domme
from database.db import AsyncSessionLocal
from database.models import DommeProfile
from utils.embeds import base_embed, success_embed, error_embed


# ── Modal ─────────────────────────────────────────────────────────────────────

class SetupModal(discord.ui.Modal, title="🎩 Butler Profile Setup"):
    """Collect Domme profile information in a single modal."""

    display_name_input = discord.ui.TextInput(
        label="Display Name",
        placeholder="The name you'd like The Butler to use for you",
        required=True,
        max_length=100,
    )
    throne_link_input = discord.ui.TextInput(
        label="Throne Wishlist Link",
        placeholder="https://throne.com/your-username  (leave blank to skip)",
        required=False,
        max_length=500,
    )
    base_coffee_input = discord.ui.TextInput(
        label="Base Coffee Amount (£/$)",
        placeholder="e.g. 10.00",
        required=True,
        max_length=10,
    )
    scaling_input = discord.ui.TextInput(
        label="Dynamic Pricing Modifiers",
        placeholder="Enter any of: time, day, drought  (comma-separated, or leave blank)",
        required=False,
        max_length=50,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        # Validate base amount
        try:
            base_amount = float(self.base_coffee_input.value.strip().lstrip("£$"))
            if base_amount <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                embed=error_embed("Base coffee amount must be a positive number, darling. 🎩"),
                ephemeral=True,
            )
            return

        # Parse scaling options
        raw_scaling = [s.strip().lower() for s in self.scaling_input.value.split(",") if s.strip()]
        time_scaling = "time" in raw_scaling
        day_scaling = "day" in raw_scaling
        drought_scaling = "drought" in raw_scaling

        # Validate throne link if provided
        throne_link: str | None = self.throne_link_input.value.strip() or None
        if throne_link and not (throne_link.startswith("http://") or throne_link.startswith("https://")):
            throne_link = "https://" + throne_link

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

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

            profile.display_name = self.display_name_input.value.strip()
            profile.throne_link = throne_link
            profile.base_coffee_amount = base_amount
            profile.time_scaling = time_scaling
            profile.day_scaling = day_scaling
            profile.drought_scaling = drought_scaling
            profile.setup_complete = True
            await session.commit()

        # Build confirmation embed
        modifiers = [m for flag, m in [(time_scaling, "time-of-day"), (day_scaling, "day-of-week"), (drought_scaling, "drought")] if flag]
        modifier_text = ", ".join(modifiers) if modifiers else "none"

        embed = base_embed(
            "🎩 Profile Configured",
            (
                f"Your Butler profile has been set up, {profile.display_name}.\n\n"
                f"**Base Coffee Amount:** £{base_amount:.2f}\n"
                f"**Dynamic Pricing:** {modifier_text}\n"
                f"**Throne Link:** {throne_link or 'Not set'}"
            ),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            embed=error_embed("Something went wrong with your setup. Please try again. 🎩"),
            ephemeral=True,
        )


# ── Cog ───────────────────────────────────────────────────────────────────────

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
        """Open the profile setup modal."""
        await interaction.response.send_modal(SetupModal())

    @app_commands.command(
        name="myprofile",
        description="View your current Butler profile. (Domme only)",
    )
    @is_domme()
    async def myprofile_command(self, interaction: discord.Interaction) -> None:
        """Display the domme's current profile."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DommeProfile).where(
                    DommeProfile.discord_id == interaction.user.id,
                    DommeProfile.guild_id == interaction.guild.id,
                )
            )
            profile = result.scalar_one_or_none()

        if profile is None or not profile.setup_complete:
            await interaction.response.send_message(
                embed=error_embed("You haven't set up your profile yet. Run `/setup` first, Mistress. 🎩"),
                ephemeral=True,
            )
            return

        modifiers = [m for flag, m in [(profile.time_scaling, "time-of-day"), (profile.day_scaling, "day-of-week"), (profile.drought_scaling, "drought")] if flag]
        modifier_text = ", ".join(modifiers) if modifiers else "none"

        embed = base_embed(
            f"🎩 {profile.display_name}'s Profile",
            (
                f"**Base Coffee Amount:** £{profile.base_coffee_amount:.2f}\n"
                f"**Dynamic Pricing:** {modifier_text}\n"
                f"**Throne Link:** {profile.throne_link or 'Not set'}\n"
                f"**Setup Complete:** {'Yes' if profile.setup_complete else 'No'}"
            ),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))

