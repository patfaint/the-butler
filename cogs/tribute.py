"""Tribute cog — tribute logging, confirmation, leaderboard, and stats."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import func, select

from cogs.permissions import handle_check_failure, is_domme
from database.db import AsyncSessionLocal
from database.models import DommeProfile, GuildConfig, Tribute, TributeStreak
from utils.embeds import base_embed, error_embed, success_embed

log = logging.getLogger("butler.tribute")


def _update_streak(streak: TributeStreak) -> None:
    """Advance or reset the tribute streak based on last tribute date."""
    now = datetime.now(timezone.utc)
    if streak.last_tribute_date is not None:
        last = streak.last_tribute_date
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        days_since = (now.date() - last.date()).days
        if days_since == 0:
            pass  # Same day — streak unchanged
        elif days_since == 1:
            streak.current_streak += 1
        else:
            streak.current_streak = 1  # Reset
    else:
        streak.current_streak = 1
    streak.last_tribute_date = now
    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak


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

    # ── /tribute ──────────────────────────────────────────────────────────────

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
        """Record an unconfirmed tribute from a sub to a Domme."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        if amount <= 0:
            await interaction.response.send_message(
                embed=error_embed("Amount must be greater than zero, darling. 🎩"),
                ephemeral=True,
            )
            return

        if domme.id == interaction.user.id:
            await interaction.response.send_message(
                embed=error_embed("You cannot tribute yourself, darling. 🎩"),
                ephemeral=True,
            )
            return

        async with AsyncSessionLocal() as session:
            tribute = Tribute(
                guild_id=interaction.guild.id,
                domme_id=domme.id,
                sub_id=interaction.user.id,
                amount=amount,
                tribute_type="tribute",
                confirmed=False,
            )
            session.add(tribute)
            await session.commit()
            tribute_id = tribute.id

        # Notify the Domme via DM
        embed = base_embed(
            "💸 Tribute Received",
            (
                f"**{interaction.user.display_name}** has submitted a tribute of **£{amount:.2f}**.\n\n"
                f"Use `/confirm @{interaction.user.display_name} {amount:.2f}` to confirm it. 🎩"
            ),
        )
        try:
            await domme.send(embed=embed)
        except discord.Forbidden:
            log.debug("Could not DM Domme %s.", domme.id)

        await interaction.response.send_message(
            embed=success_embed(
                f"Your tribute of **£{amount:.2f}** to {domme.mention} has been submitted.\n"
                "Awaiting Domme confirmation. 🎩"
            ),
            ephemeral=True,
        )

    # ── /confirm ──────────────────────────────────────────────────────────────

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
        """Confirm a tribute from a sub, marking it as verified."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        if amount <= 0:
            await interaction.response.send_message(
                embed=error_embed("Amount must be greater than zero, darling. 🎩"),
                ephemeral=True,
            )
            return

        async with AsyncSessionLocal() as session:
            # Find the most recent unconfirmed tribute from this sub to this domme
            result = await session.execute(
                select(Tribute)
                .where(
                    Tribute.guild_id == interaction.guild.id,
                    Tribute.domme_id == interaction.user.id,
                    Tribute.sub_id == sub.id,
                    Tribute.confirmed == False,  # noqa: E712
                )
                .order_by(Tribute.timestamp.desc())
                .limit(1)
            )
            tribute = result.scalar_one_or_none()

            if tribute is None:
                # No pending tribute — create a directly confirmed one
                tribute = Tribute(
                    guild_id=interaction.guild.id,
                    domme_id=interaction.user.id,
                    sub_id=sub.id,
                    amount=amount,
                    tribute_type="tribute",
                    confirmed=True,
                )
                session.add(tribute)
            else:
                tribute.amount = amount
                tribute.confirmed = True

            # Update / create streak
            streak_result = await session.execute(
                select(TributeStreak).where(
                    TributeStreak.sub_id == sub.id,
                    TributeStreak.guild_id == interaction.guild.id,
                    TributeStreak.domme_id == interaction.user.id,
                )
            )
            streak = streak_result.scalar_one_or_none()
            if streak is None:
                streak = TributeStreak(
                    sub_id=sub.id,
                    guild_id=interaction.guild.id,
                    domme_id=interaction.user.id,
                )
                session.add(streak)
            _update_streak(streak)

            # Load guild config for leaderboard channel
            cfg_result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == interaction.guild.id)
            )
            config = cfg_result.scalar_one_or_none()

            await session.commit()

        # Notify sub via DM
        try:
            sub_embed = base_embed(
                "✅ Tribute Confirmed",
                (
                    f"Your tribute of **£{amount:.2f}** to **{interaction.user.display_name}** "
                    f"has been confirmed. Your streak is now **{streak.current_streak} day(s)**. 🎩"
                ),
            )
            await sub.send(embed=sub_embed)
        except discord.Forbidden:
            log.debug("Could not DM sub %s.", sub.id)

        # Post to leaderboard channel if configured
        if config and config.leaderboard_channel_id:
            channel = interaction.guild.get_channel(config.leaderboard_channel_id)
            if isinstance(channel, discord.TextChannel):
                public_embed = base_embed(
                    "💸 Tribute Confirmed",
                    (
                        f"{sub.mention} has tributed **£{amount:.2f}** to "
                        f"{interaction.user.mention}. 🎩\n"
                        f"*Streak: {streak.current_streak} day(s)*"
                    ),
                )
                try:
                    await channel.send(embed=public_embed)
                except discord.Forbidden:
                    pass

        await interaction.response.send_message(
            embed=success_embed(
                f"Tribute of **£{amount:.2f}** from {sub.mention} confirmed. "
                f"Their streak: **{streak.current_streak} day(s)**. 🎩"
            ),
            ephemeral=True,
        )

    # ── /leaderboard ──────────────────────────────────────────────────────────

    @app_commands.command(
        name="leaderboard",
        description="View the server tribute leaderboard.",
    )
    async def leaderboard_command(self, interaction: discord.Interaction) -> None:
        """Show the top subs by total confirmed tributes."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Tribute.sub_id, func.sum(Tribute.amount).label("total"))
                .where(
                    Tribute.guild_id == interaction.guild.id,
                    Tribute.confirmed == True,  # noqa: E712
                )
                .group_by(Tribute.sub_id)
                .order_by(func.sum(Tribute.amount).desc())
                .limit(10)
            )
            rows = result.all()

        if not rows:
            await interaction.response.send_message(
                embed=base_embed("🏆 Tribute Leaderboard", "No confirmed tributes yet, darling. 🎩"),
            )
            return

        lines: list[str] = []
        medals = ["🥇", "🥈", "🥉"]
        for i, (sub_id, total) in enumerate(rows):
            member = interaction.guild.get_member(sub_id)
            name = member.display_name if member else f"User {sub_id}"
            medal = medals[i] if i < 3 else f"**{i + 1}.**"
            lines.append(f"{medal} {name} — **£{total:.2f}**")

        embed = base_embed(
            "🏆 Tribute Leaderboard",
            "\n".join(lines),
        )
        await interaction.response.send_message(embed=embed)

    # ── /stats ────────────────────────────────────────────────────────────────

    @app_commands.command(
        name="stats",
        description="View your personal tribute stats.",
    )
    async def stats_command(self, interaction: discord.Interaction) -> None:
        """Show the user's tribute stats (given and received)."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        async with AsyncSessionLocal() as session:
            # Total given (as sub)
            given_result = await session.execute(
                select(func.sum(Tribute.amount))
                .where(
                    Tribute.guild_id == interaction.guild.id,
                    Tribute.sub_id == interaction.user.id,
                    Tribute.confirmed == True,  # noqa: E712
                )
            )
            total_given = given_result.scalar() or 0.0

            # Total received (as domme)
            received_result = await session.execute(
                select(func.sum(Tribute.amount))
                .where(
                    Tribute.guild_id == interaction.guild.id,
                    Tribute.domme_id == interaction.user.id,
                    Tribute.confirmed == True,  # noqa: E712
                )
            )
            total_received = received_result.scalar() or 0.0

            # Tribute count given
            count_result = await session.execute(
                select(func.count(Tribute.id))
                .where(
                    Tribute.guild_id == interaction.guild.id,
                    Tribute.sub_id == interaction.user.id,
                    Tribute.confirmed == True,  # noqa: E712
                )
            )
            tribute_count = count_result.scalar() or 0

            # Best streak
            streak_result = await session.execute(
                select(func.max(TributeStreak.longest_streak))
                .where(
                    TributeStreak.guild_id == interaction.guild.id,
                    TributeStreak.sub_id == interaction.user.id,
                )
            )
            best_streak = streak_result.scalar() or 0

        lines = [
            f"**Total Tributed:** £{total_given:.2f}",
            f"**Total Received:** £{total_received:.2f}",
            f"**Tribute Count:** {tribute_count}",
            f"**Longest Streak:** {best_streak} day(s)",
        ]
        embed = base_embed(
            f"📊 {interaction.user.display_name}'s Stats",
            "\n".join(lines),
        )
        if isinstance(interaction.user, discord.Member):
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TributeCog(bot))

