"""The Butler — Discord bot entry point."""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from config import require_discord_token, require_guild_id
from database.db import init_db

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("butler")

# ── Bot class ─────────────────────────────────────────────────────────────────

class Butler(commands.Bot):
    """The Butler — Discord bot for The Drain Server."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True        # Required for on_member_join
        intents.message_content = True  # Required for message-based features

        super().__init__(
            command_prefix="!",   # Fallback prefix (slash commands are primary)
            intents=intents,
            help_command=None,
        )
        self.guild_id = require_guild_id()

    async def setup_hook(self) -> None:
        """Called once before the bot connects — initialise DB and sync commands."""
        log.info("Initialising database…")
        await init_db()

        # Sync slash commands to the home guild for instant availability.
        # Add cogs above this line before calling sync.
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        log.info("Synced %d slash command(s) to guild %d.", len(synced), self.guild_id)

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)  # type: ignore[union-attr]
        await self.change_presence(
            activity=discord.Game(name="At your service. 🎩")
        )


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    async with Butler() as bot:
        await bot.start(require_discord_token())


if __name__ == "__main__":
    asyncio.run(main())
