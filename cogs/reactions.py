"""Reactions cog — passive keyword/emoji GIF reactions using the Tenor API."""

from __future__ import annotations

import logging
import random

import discord
import httpx
from discord.ext import commands

import config

log = logging.getLogger("butler.reactions")

# ── Keyword → Tenor search term map ──────────────────────────────────────────

_KEYWORDS: dict[str, str] = {
    "good boy": "good boy dog",
    "good girl": "good girl praise",
    "kneel": "bow down",
    "serve": "butler serving",
    "worship": "worship",
    "tribute": "money offering",
    "coffee": "coffee serve",
    "yes mistress": "yes queen",
    "yes goddess": "yes queen",
    "thank you mistress": "bowing thank you",
    "thank you goddess": "bowing thank you",
    "pamper": "luxury pampering",
    "spoil": "spoil queen",
    "obey": "obey queen",
}


async def _fetch_gif(query: str) -> str | None:
    """Fetch a random GIF URL from the Tenor API for the given search query."""
    api_key = config.TENOR_API_KEY
    if not api_key:
        return None
    url = "https://tenor.googleapis.com/v2/search"
    params = {"q": query, "key": api_key, "limit": 20, "media_filter": "gif"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        chosen = random.choice(results)
        return chosen["media_formats"]["gif"]["url"]
    except Exception:
        log.debug("Tenor API request failed for query: %s", query, exc_info=True)
        return None


class ReactionsCog(commands.Cog, name="Reactions"):
    """Listens to messages and responds with GIFs based on keywords."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Ignore bot messages
        if message.author.bot:
            return
        if not config.TENOR_API_KEY:
            return

        content_lower = message.content.lower()
        for keyword, search_term in _KEYWORDS.items():
            if keyword in content_lower:
                gif_url = await _fetch_gif(search_term)
                if gif_url:
                    try:
                        await message.channel.send(gif_url)
                    except discord.Forbidden:
                        pass
                break  # Only one reaction per message


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionsCog(bot))

