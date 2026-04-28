"""Reactions cog — passive keyword/emoji GIF reactions (stub for Phase 2)."""

from __future__ import annotations

import discord
from discord.ext import commands


class ReactionsCog(commands.Cog, name="Reactions"):
    """Listens to messages and responds with GIFs based on keywords/emojis."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Ignore bot messages
        if message.author.bot:
            return
        # Passive reaction logic will be added in Phase 2


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionsCog(bot))
