"""Setup cog — /setup (admin), /domsetup (domme), /subsetup (sub)."""

from __future__ import annotations

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from cogs.permissions import handle_check_failure, is_admin, is_domme, is_sub
from database.db import AsyncSessionLocal
from database.helpers import get_or_create_guild_config
from database.models import DommeProfile, SubProfile

log = logging.getLogger("butler.setup")

# ── DM conversation helpers ───────────────────────────────────────────────────

_DM_TIMEOUT = 300  # seconds to wait for each answer


def _dm_check(user: discord.User | discord.Member):
    """Return a wait_for predicate: message from *user* in a DM channel."""
    def check(m: discord.Message) -> bool:
        return m.author.id == user.id and isinstance(m.channel, discord.DMChannel)
    return check


async def _ask(dm: discord.DMChannel, bot: commands.Bot, user: discord.User | discord.Member, question: str) -> str | None:
    """Send *question* and wait for the user's reply. Returns None on timeout or cancel."""
    await dm.send(question)
    try:
        msg = await bot.wait_for("message", check=_dm_check(user), timeout=_DM_TIMEOUT)
    except asyncio.TimeoutError:
        await dm.send(
            "The Butler has stepped away — the setup session has timed out. "
            "Run the command again whenever you're ready. 🎩"
        )
        return None
    if msg.content.strip().lower() == "cancel":
        await dm.send("No problem — the setup has been cancelled. Run the command again whenever you're ready. 🎩")
        return None
    return msg.content.strip()


class SetupCog(commands.Cog, name="Setup"):
    """Server setup, domme profile wizard, and sub profile wizard."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    # ── /setup — admin only ───────────────────────────────────────────────────

    @app_commands.command(
        name="setup",
        description="Set up the server roles and channels. (Admin only)",
    )
    @is_admin()
    async def setup_command(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        results: list[str] = []

        # ── Roles ─────────────────────────────────────────────────────────────
        role_names = ["Domme", "Sub", "Verified", "Unverified", "Mod"]
        role_ids: dict[str, int] = {}
        for name in role_names:
            existing = discord.utils.get(guild.roles, name=name)
            if existing:
                role_ids[name] = existing.id
                results.append(f"✅ Role **{name}** already exists.")
            else:
                new_role = await guild.create_role(name=name, reason="/setup")
                role_ids[name] = new_role.id
                results.append(f"✨ Created role **{name}**.")

        # ── Channels ──────────────────────────────────────────────────────────
        mod_role = guild.get_role(role_ids["Mod"])

        channel_specs: list[tuple[str, dict]] = [
            ("welcome", {}),
            ("verify", {}),
            ("mod-verify", {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                **({mod_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)} if mod_role else {}),
            }),
        ]

        channel_ids: dict[str, int] = {}
        for ch_name, overwrites in channel_specs:
            existing_ch = discord.utils.get(guild.text_channels, name=ch_name)
            if existing_ch:
                channel_ids[ch_name] = existing_ch.id
                results.append(f"✅ Channel **#{ch_name}** already exists.")
            else:
                new_ch = await guild.create_text_channel(
                    ch_name,
                    overwrites=overwrites or discord.utils.MISSING,
                    reason="/setup",
                )
                channel_ids[ch_name] = new_ch.id
                results.append(f"✨ Created channel **#{ch_name}**.")

        # ── Save to database ──────────────────────────────────────────────────
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, guild.id)
            config.domme_role_id = role_ids.get("Domme")
            config.sub_role_id = role_ids.get("Sub")
            config.verified_role_id = role_ids.get("Verified")
            config.unverified_role_id = role_ids.get("Unverified")
            config.mod_role_id = role_ids.get("Mod")
            config.welcome_channel_id = channel_ids.get("welcome")
            config.verification_channel_id = channel_ids.get("verify")
            config.mod_verify_channel_id = channel_ids.get("mod-verify")
            await session.commit()

        summary = "\n".join(results)
        await interaction.followup.send(
            f"🎩 **Server Setup Complete**\n\n{summary}",
            ephemeral=True,
        )

    # ── /domsetup — domme only ────────────────────────────────────────────────

    @app_commands.command(
        name="domsetup",
        description="Set up your domme profile. (Domme only)",
    )
    @is_domme()
    async def domsetup_command(self, interaction: discord.Interaction) -> None:
        user = interaction.user
        await interaction.response.send_message(
            "📬 Check your DMs — The Butler will be in touch shortly. 🎩",
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

        # Opening message
        await dm.send(
            f"Hey {user.mention}! 👑\n\n"
            "Thanks for taking the time to set up your domme profile on The Butler. "
            "I'm here to help you get everything configured so the server works exactly how you like it.\n\n"
            "Having a domme profile unlocks features like:\n"
            "— **Throne tracking**, so the server always knows who's been spoiling you\n"
            "— **Coffee alerts**, so when you need your morning coffee funded, a single message in the server lets all the subs know\n"
            "— **Sub management tools**, including timeouts and access controls\n\n"
            "This will only take a few minutes. Let's get started — you can type `cancel` at any time to stop."
        )

        # Q1 — title
        title = await _ask(
            dm, self.bot, user,
            "First things first — what name or title would you like subs to call you? "
            "(e.g. Mistress Sarah, Goddess, etc.)"
        )
        if title is None:
            return

        # Q2 — throne link
        throne_raw = await _ask(
            dm, self.bot, user,
            "Do you have a Throne wishlist link you'd like to share with the server? "
            "If not, just type `skip`."
        )
        if throne_raw is None:
            return
        throne_link = None if throne_raw.lower() == "skip" else throne_raw

        # Q3 — tribute links
        tribute_raw = await _ask(
            dm, self.bot, user,
            "Do you have any other tribute or gifting links? "
            "(e.g. PayPal, Amazon wishlist) Send them all in one message, or type `skip`."
        )
        if tribute_raw is None:
            return
        tribute_links = None if tribute_raw.lower() == "skip" else tribute_raw

        # Q4 — bio
        bio_raw = await _ask(
            dm, self.bot, user,
            "Is there anything you'd like subs to know about you? "
            "This will appear on your profile. Type `skip` to leave this blank."
        )
        if bio_raw is None:
            return
        bio = None if bio_raw.lower() == "skip" else bio_raw

        # Save to database
        guild_id = interaction.guild_id
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DommeProfile).where(
                    DommeProfile.discord_id == user.id,
                    DommeProfile.guild_id == guild_id,
                )
            )
            profile = result.scalar_one_or_none()
            if profile is None:
                profile = DommeProfile(discord_id=user.id, guild_id=guild_id)
                session.add(profile)
            profile.title = title
            profile.display_name = title
            profile.throne_link = throne_link
            profile.tribute_links = tribute_links
            profile.bio = bio
            profile.setup_complete = True
            await session.commit()

        await dm.send(
            f"Perfect — your domme profile is all set up, {user.mention}! 👑\n\n"
            "Your profile is now live on the server. You can update it at any time by running `/domsetup` again.\n\n"
            "The Butler is at your service. 🎩"
        )

    # ── /subsetup — sub only ──────────────────────────────────────────────────

    @app_commands.command(
        name="subsetup",
        description="Set up your sub profile. (Sub only)",
    )
    @is_sub()
    async def subsetup_command(self, interaction: discord.Interaction) -> None:
        user = interaction.user
        await interaction.response.send_message(
            "📬 Check your DMs — The Butler will be in touch shortly. 🎩",
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

        # Opening message
        await dm.send(
            f"Hey {user.mention}! 🎀\n\n"
            "Thanks for setting up your sub profile on The Butler. "
            "This helps the dommes on the server get to know you a little better.\n\n"
            "Having a sub profile means:\n"
            "— Dommes can see your profile when managing the server\n"
            "— You'll appear on the tribute leaderboard when you spoil a domme\n"
            "— You'll get personalised interactions from The Butler\n\n"
            "Let's get you set up — type `cancel` at any time to stop."
        )

        # Q1 — display name
        display_name = await _ask(
            dm, self.bot, user,
            "What name would you like to go by on the server?"
        )
        if display_name is None:
            return

        # Q2 — bio
        bio_raw = await _ask(
            dm, self.bot, user,
            "Tell us a little about yourself — what brings you to the server? "
            "Type `skip` to leave this blank."
        )
        if bio_raw is None:
            return
        bio = None if bio_raw.lower() == "skip" else bio_raw

        # Q3 — about (for dommes)
        about_raw = await _ask(
            dm, self.bot, user,
            "Is there anything you'd like dommes to know about you? "
            "Type `skip` to leave this blank."
        )
        if about_raw is None:
            return
        about = None if about_raw.lower() == "skip" else about_raw

        # Save to database
        guild_id = interaction.guild_id
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SubProfile).where(
                    SubProfile.discord_id == user.id,
                    SubProfile.guild_id == guild_id,
                )
            )
            profile = result.scalar_one_or_none()
            if profile is None:
                profile = SubProfile(discord_id=user.id, guild_id=guild_id)
                session.add(profile)
            profile.display_name = display_name
            profile.username = display_name
            profile.bio = bio
            profile.about = about
            await session.commit()

        await dm.send(
            "All done! Your sub profile is now live. 🎀\n\n"
            "Remember, you can update it any time with `/subsetup`.\n\n"
            "The Butler will take it from here. 🎩"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))
