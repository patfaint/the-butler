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

# ── Cogs to load ──────────────────────────────────────────────────────────────

COGS: list[str] = [
    "cogs.help",
    "cogs.welcome",
    "cogs.setup",
    "cogs.throne",
    "cogs.coffee",
    "cogs.tribute",
    "cogs.verification",
    "cogs.reactions",
    "cogs.trivia",
    "cogs.jail",
    "cogs.vip",
    "cogs.moderation",
]

# ── Bot class ─────────────────────────────────────────────────────────────────

class Butler(commands.Bot):
    """The Butler — Discord bot for The Drain Server."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True       # Required for on_member_join
        intents.message_content = True  # Required for passive keyword reactions

        super().__init__(
            command_prefix="!",   # Fallback prefix (slash commands are primary)
            intents=intents,
            help_command=None,    # We provide our own /help
        )
        self.guild_id = require_guild_id()

    async def setup_hook(self) -> None:
        """Called once before the bot connects — initialise DB and load cogs."""
        log.info("Initialising database…")
        await init_db()

        for cog in COGS:
            try:
                await self.load_extension(cog)
                log.info("Loaded cog: %s", cog)
            except Exception as exc:
                log.error("Failed to load cog %s: %s", cog, exc)

        # Sync slash commands to the home guild for instant availability.
        # For global rollout, remove the guild argument.
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        log.info("Synced %d slash command(s) to guild %d.", len(synced), self.guild_id)

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)  # type: ignore[union-attr]
        await self.change_presence(
            activity=discord.Game(name="At your service. 🎩")
        )

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """Global fallback error handler for slash commands."""
        from cogs.permissions import handle_check_failure
        await handle_check_failure(interaction, error)


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    async with Butler() as bot:
        await bot.start(require_discord_token())


if __name__ == "__main__":
    asyncio.run(main())
