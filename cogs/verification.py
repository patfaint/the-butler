"""Verification cog — age verification via DM with mod approval."""

from __future__ import annotations

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from cogs.permissions import handle_check_failure
from database.db import AsyncSessionLocal
from database.helpers import get_or_create_guild_config
from database.models import GuildConfig, SubProfile
from utils.embeds import success_embed

log = logging.getLogger("butler.verification")

_DM_TIMEOUT = 600  # 10 minutes to send the photo


# ── Persistent approve / reject view ─────────────────────────────────────────

class VerificationView(discord.ui.View):
    """Persistent view attached to the mod-verify forwarding message."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ Approve",
        style=discord.ButtonStyle.success,
        custom_id="butler_verify_approve",
    )
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._handle(interaction, approved=True)

    @discord.ui.button(
        label="❌ Reject",
        style=discord.ButtonStyle.danger,
        custom_id="butler_verify_reject",
    )
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._handle(interaction, approved=False)

    async def _handle(self, interaction: discord.Interaction, *, approved: bool) -> None:
        # Parse user_id from the embed footer ("User ID: <id>")
        message = interaction.message
        if message is None or not message.embeds:
            await interaction.response.send_message("Could not read the verification request.", ephemeral=True)
            return

        embed = message.embeds[0]
        user_id: int | None = None
        guild_id: int | None = None

        for field in embed.fields:
            if field.name == "User ID" and field.value:
                try:
                    user_id = int(field.value)
                except ValueError:
                    pass
            if field.name == "Guild ID" and field.value:
                try:
                    guild_id = int(field.value)
                except ValueError:
                    pass

        if user_id is None or guild_id is None:
            await interaction.response.send_message("Could not extract user/guild information.", ephemeral=True)
            return

        guild = interaction.client.get_guild(guild_id)
        if guild is None:
            await interaction.response.send_message("Guild not found.", ephemeral=True)
            return

        member = guild.get_member(user_id)
        user = interaction.client.get_user(user_id) or (await interaction.client.fetch_user(user_id) if user_id else None)

        if approved:
            # Assign Verified role, remove Unverified role
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(GuildConfig).where(GuildConfig.guild_id == guild_id)
                )
                config = result.scalar_one_or_none()

            if member and config:
                if config.verified_role_id:
                    verified_role = guild.get_role(config.verified_role_id)
                    if verified_role:
                        await member.add_roles(verified_role, reason="Age verification approved")
                if config.unverified_role_id:
                    unverified_role = guild.get_role(config.unverified_role_id)
                    if unverified_role and unverified_role in member.roles:
                        await member.remove_roles(unverified_role, reason="Age verification approved")

                # Mark as verified in the database
                async with AsyncSessionLocal() as session:
                    db_result = await session.execute(
                        select(SubProfile).where(
                            SubProfile.discord_id == user_id,
                            SubProfile.guild_id == guild_id,
                        )
                    )
                    profile = db_result.scalar_one_or_none()
                    if profile is None:
                        profile = SubProfile(discord_id=user_id, guild_id=guild_id)
                        session.add(profile)
                    profile.is_verified = True
                    await session.commit()

            # DM the user
            if user:
                try:
                    await user.send(
                        "You've been verified! Welcome to the Drain Server. 🎉 "
                        "Head back to the server to get started."
                    )
                except discord.Forbidden:
                    log.warning("Could not DM user %d after approval.", user_id)

            # Update the message
            new_embed = embed.copy()
            new_embed.colour = discord.Colour.green()
            new_embed.set_footer(text=f"✅ Approved by {interaction.user} ({interaction.user.id})")
            await message.edit(embed=new_embed, view=None)
            await interaction.response.send_message(f"✅ Verified <@{user_id}>.", ephemeral=True)

        else:
            # DM the user with rejection
            if user:
                try:
                    await user.send(
                        "Unfortunately we weren't able to verify your age from the photo provided. "
                        "Please try again with a clearer photo, or contact a mod directly for help."
                    )
                except discord.Forbidden:
                    log.warning("Could not DM user %d after rejection.", user_id)

            # Update the message
            new_embed = embed.copy()
            new_embed.colour = discord.Colour.red()
            new_embed.set_footer(text=f"❌ Rejected by {interaction.user} ({interaction.user.id})")
            await message.edit(embed=new_embed, view=None)
            await interaction.response.send_message(f"❌ Rejected <@{user_id}>.", ephemeral=True)


# ── Cog ───────────────────────────────────────────────────────────────────────

class VerificationCog(commands.Cog, name="Verification"):
    """Handles the age verification DM flow."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_view(VerificationView())

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    @app_commands.command(
        name="verify",
        description="Start the age verification process.",
    )
    async def verify_command(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        user = interaction.user
        await interaction.response.send_message(
            "📬 Check your DMs — The Butler will walk you through verification. 🎩",
            ephemeral=True,
        )

        try:
            dm = await user.create_dm()
        except discord.Forbidden:
            await interaction.followup.send(
                "I wasn't able to send you a DM. Please enable DMs from server members and try again.",
                ephemeral=True,
            )
            return

        # Instructions
        await dm.send(
            "Hey there! 👋\n\n"
            "Welcome to the Drain Server! Before you can access the rest of the server, "
            "we need to confirm that you're 18 or older.\n\n"
            "To complete verification, please send us a photo that confirms your age. This could be:\n"
            "— A photo of yourself holding a handwritten note with **today's date** written on it\n"
            "— A photo of a valid ID (you can blur out your full name and address — "
            "we just need your date of birth and face)\n\n"
            "Your photo will be sent directly to our mod team for review. "
            "It will not be shared publicly and will be deleted once verified.\n\n"
            "When you're ready, simply **send your photo here** in this DM and it will be forwarded to the mods. 📸\n\n"
            "If you have any issues, type `help` and a mod will be with you shortly."
        )

        # Wait for photo
        def dm_check(m: discord.Message) -> bool:
            return (
                m.author.id == user.id
                and isinstance(m.channel, discord.DMChannel)
                and (bool(m.attachments) or m.content.strip().lower() == "help")
            )

        try:
            msg = await self.bot.wait_for("message", check=dm_check, timeout=_DM_TIMEOUT)
        except asyncio.TimeoutError:
            await dm.send(
                "The verification session has timed out. Run `/verify` in the server again whenever you're ready. 🎩"
            )
            return

        if msg.content.strip().lower() == "help":
            await dm.send(
                "No problem — a mod has been notified that you need assistance. "
                "Please sit tight and someone will be with you shortly. 🎩"
            )
            # Notify mods via mod-verify channel if configured
            await self._forward_help_request(interaction.guild_id, user)
            return

        # Forward photo to mod-verify channel
        await self._forward_photo(msg, user, interaction.guild_id)
        await dm.send(
            "📸 Your photo has been sent to the mod team for review. "
            "You'll receive a DM once a decision has been made. "
            "This usually doesn't take long — thank you for your patience. 🎩"
        )

    async def _forward_photo(
        self,
        msg: discord.Message,
        user: discord.User | discord.Member,
        guild_id: int,
    ) -> None:
        """Forward the verification photo to the mod-verify channel."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == guild_id)
            )
            config = result.scalar_one_or_none()

        if config is None or config.mod_verify_channel_id is None:
            log.warning("mod_verify_channel_id not configured for guild %d — cannot forward photo.", guild_id)
            return

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return

        channel = guild.get_channel(config.mod_verify_channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        embed = discord.Embed(
            title="🔍 Age Verification Request",
            colour=discord.Colour.gold(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{user.mention} ({user})", inline=False)
        embed.add_field(name="User ID", value=str(user.id), inline=True)
        embed.add_field(name="Guild ID", value=str(guild_id), inline=True)
        embed.set_footer(text="Use the buttons below to approve or reject.")

        files = [await a.to_file() for a in msg.attachments]
        view = VerificationView()
        await channel.send(embed=embed, files=files, view=view)

    async def _forward_help_request(self, guild_id: int, user: discord.User | discord.Member) -> None:
        """Notify the mod-verify channel that a user needs help with verification."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == guild_id)
            )
            config = result.scalar_one_or_none()

        if config is None or config.mod_verify_channel_id is None:
            return

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return

        channel = guild.get_channel(config.mod_verify_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(
                f"🆘 {user.mention} (`{user}`, ID: `{user.id}`) has requested help with verification. "
                "Please reach out to them directly. 🎩"
            )

    # ── Legacy admin channel setter (kept for backwards compatibility) ─────────

    @app_commands.command(
        name="setverificationchannel",
        description="Set the verification channel. (Admin only)",
    )
    @app_commands.checks.has_permissions(administrator=True)
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
