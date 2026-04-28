"""Welcome cog — sends a pink embed when a new member joins."""

from __future__ import annotations

import discord
from discord.ext import commands
from sqlalchemy import select

from database.db import AsyncSessionLocal
from database.models import GuildConfig
from utils.embeds import welcome_embed


class WelcomeCog(commands.Cog, name="Welcome"):
    """Listens for member join events and sends the welcome embed."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Send the welcome embed to the configured welcome channel."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GuildConfig).where(GuildConfig.guild_id == member.guild.id)
            )
            config: GuildConfig | None = result.scalar_one_or_none()

        if config is None or config.welcome_channel_id is None:
            return

        channel = member.guild.get_channel(config.welcome_channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        await channel.send(embed=welcome_embed(member))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
