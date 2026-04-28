"""Reactions cog — Giphy GIF auto-reactions on keywords and random triggers."""

from __future__ import annotations

import logging
import random
from typing import Optional

import aiohttp
import discord
from discord.ext import commands

from config import GIPHY_API_KEY

log = logging.getLogger("butler.reactions")

# ── Giphy configuration ───────────────────────────────────────────────────────

_GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"
_GIPHY_RATING = "r"
_GIPHY_LIMIT = 10

# ── Keyword → Giphy search query mapping ─────────────────────────────────────

_KEYWORD_TRIGGERS: list[tuple[tuple[str, ...], str]] = [
    (("good morning", "gm"), "good morning"),
    (("good night", "gn"), "good night"),
    (("coffee",), "coffee"),
    (("worship", "kneel"), "worship kneel"),
    (("spoil", "tribute", "paypig"), "money tribute"),
    (("owned", "collared"), "owned collared"),
    (("punish", "punishment"), "punishment"),
    (("beg", "begging"), "begging"),
]

# Random-reaction pool
_RANDOM_POOL: list[str] = [
    "dominant",
    "submissive",
    "femdom",
    "luxury",
    "spoiled",
]

_RANDOM_CHANCE = 0.10  # 10%


# ── Giphy helper ──────────────────────────────────────────────────────────────

async def _fetch_gif(query: str) -> Optional[str]:
    """Return a random GIF URL for *query* via Giphy, or None on failure."""
    if not GIPHY_API_KEY:
        log.warning("GIPHY_API_KEY is not set — skipping GIF reaction.")
        return None

    params = {
        "api_key": GIPHY_API_KEY,
        "q": query,
        "limit": _GIPHY_LIMIT,
        "rating": _GIPHY_RATING,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(_GIPHY_SEARCH_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    log.warning("Giphy API returned HTTP %d for query '%s'.", resp.status, query)
                    return None
                data = await resp.json()
                gifs = data.get("data", [])
                if not gifs:
                    return None
                gif = random.choice(gifs)
                # Use downsized URL for faster loading; fall back to original
                return (
                    gif.get("images", {}).get("downsized", {}).get("url")
                    or gif.get("images", {}).get("original", {}).get("url")
                )
    except Exception:
        log.exception("Error fetching GIF from Giphy for query '%s'.", query)
        return None


# ── Cog ───────────────────────────────────────────────────────────────────────

class ReactionsCog(commands.Cog, name="Reactions"):
    """Listens to messages and responds with Giphy GIFs based on keywords or random chance."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._last_random_user: Optional[int] = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Only respond in guild channels, never to bots
        if message.author.bot:
            return
        if message.guild is None:
            return

        content_lower = message.content.lower()

        # ── Keyword triggers ──────────────────────────────────────────────────
        for keywords, giphy_query in _KEYWORD_TRIGGERS:
            if any(kw in content_lower for kw in keywords):
                gif_url = await _fetch_gif(giphy_query)
                if gif_url:
                    await message.reply(gif_url, mention_author=False)
                return  # Only one keyword trigger per message

        # ── Random 10% reaction (don't repeat the same user twice) ────────────
        if random.random() < _RANDOM_CHANCE:
            if message.author.id != self._last_random_user:
                self._last_random_user = message.author.id
                query = random.choice(_RANDOM_POOL)
                gif_url = await _fetch_gif(query)
                if gif_url:
                    await message.reply(gif_url, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionsCog(bot))
