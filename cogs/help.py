"""Help menu — paginated slash command with Previous/Next navigation."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import TOTAL_HELP_PAGES, help_page_embed


class HelpPaginator(discord.ui.View):
    """Previous / Next button view for the /help command."""

    def __init__(self, interaction: discord.Interaction) -> None:
        super().__init__(timeout=120)
        self.interaction = interaction
        self.page = 0
        self._update_buttons()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _update_buttons(self) -> None:
        self.previous_button.disabled = self.page == 0
        self.next_button.disabled = self.page == TOTAL_HELP_PAGES - 1

    def _current_embed(self) -> discord.Embed:
        return help_page_embed(self.page)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only the original invoker may press the pagination buttons."""
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message(
                "These buttons belong to someone else, darling. 🎩",
                ephemeral=True,
            )
            return False
        return True

    # ── Buttons ───────────────────────────────────────────────────────────────

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.page -= 1
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self._current_embed(), view=self
        )

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self._current_embed(), view=self
        )

    # ── Timeout ───────────────────────────────────────────────────────────────

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass


class HelpCog(commands.Cog, name="Help"):
    """Provides the /help slash command."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="Browse all of The Butler's commands.")
    async def help_command(self, interaction: discord.Interaction) -> None:
        """Send the paginated help menu."""
        view = HelpPaginator(interaction)
        await interaction.response.send_message(
            embed=help_page_embed(0),
            view=view,
            ephemeral=False,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
