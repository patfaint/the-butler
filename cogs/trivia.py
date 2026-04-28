"""Trivia cog — button-based trivia game and /meme Tenor GIF command."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass

import discord
import httpx
from discord import app_commands
from discord.ext import commands

import config
from cogs.permissions import handle_check_failure
from utils.embeds import base_embed, PINK

log = logging.getLogger("butler.trivia")


# ── Trivia question bank ──────────────────────────────────────────────────────

@dataclass
class Question:
    text: str
    options: list[str]  # 4 options
    answer_index: int   # 0-based index of the correct answer


_QUESTIONS: list[Question] = [
    Question(
        "What does 'findom' stand for?",
        ["Financial domination", "Fine dominatrix", "Finger domination", "Fit domain"],
        0,
    ),
    Question(
        "Which of these is considered proper etiquette when addressing a Domme?",
        ["Shouting her name", "Using her preferred title", "Ignoring her preferences", "Using first name only"],
        1,
    ),
    Question(
        "What is a 'tribute' in the context of this server?",
        ["A war tax", "A monetary gift to a Domme", "A thank-you card", "A type of dance"],
        1,
    ),
    Question(
        "What does 'SSC' stand for in kink communities?",
        ["Safe, Sane, Consensual", "Strict, Secure, Controlled", "Safe, Secure, Clean", "Submit, Serve, Comply"],
        0,
    ),
    Question(
        "What is a 'safeword' used for?",
        ["A password for the server", "To immediately stop a scene", "A greeting between members", "A type of punishment"],
        1,
    ),
    Question(
        "What is a 'Throne' link most commonly associated with?",
        ["A gaming platform", "A Domme's wishlist", "A photo album", "A scheduling tool"],
        1,
    ),
    Question(
        "Which of the following is a cardinal rule of this community?",
        ["Never say no", "Respect everyone's stated limits", "Always comply immediately", "Share personal details freely"],
        1,
    ),
    Question(
        "What does 'D/s' stand for?",
        ["Desire/Submission", "Dominant/submissive", "Drama/serious", "Demanding/soft"],
        1,
    ),
    Question(
        "What is 'aftercare'?",
        ["Post-session emotional and physical support", "Cleaning the play space", "A follow-up tribute", "A goodbye message"],
        0,
    ),
    Question(
        "In a power exchange, who typically sets the rules and structure?",
        ["The submissive", "The dominant", "Both equally always", "Neither — it's chaos"],
        1,
    ),
]


# ── Tenor GIF helper ──────────────────────────────────────────────────────────

async def _fetch_gif(query: str) -> str | None:
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
        return random.choice(results)["media_formats"]["gif"]["url"]
    except Exception:
        log.debug("Tenor API request failed.", exc_info=True)
        return None


# ── Trivia View ───────────────────────────────────────────────────────────────

class TriviaView(discord.ui.View):
    """A view with 4 answer buttons for a trivia question."""

    def __init__(self, question: Question, invoker_id: int) -> None:
        super().__init__(timeout=30)
        self.question = question
        self.invoker_id = invoker_id
        self.answered = False

        labels = ["A", "B", "C", "D"]
        for i, option in enumerate(question.options):
            button = discord.ui.Button(
                label=f"{labels[i]}. {option}",
                style=discord.ButtonStyle.primary,
                custom_id=str(i),
            )
            button.callback = self._make_callback(i)
            self.add_item(button)

    def _make_callback(self, index: int):
        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id != self.invoker_id:
                await interaction.response.send_message(
                    "This trivia question isn't for you, darling. 🎩", ephemeral=True
                )
                return
            if self.answered:
                await interaction.response.send_message(
                    "You've already answered, darling. 🎩", ephemeral=True
                )
                return
            self.answered = True
            self.stop()

            correct = index == self.question.answer_index
            correct_label = self.question.options[self.question.answer_index]
            result_text = (
                f"✅ Correct! The answer was **{correct_label}**. Well done. 🎩"
                if correct
                else f"❌ Incorrect. The correct answer was **{correct_label}**. 🎩"
            )
            embed = base_embed("🎭 Trivia Result", result_text)
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
                    if int(item.custom_id) == self.question.answer_index:
                        item.style = discord.ButtonStyle.success
                    elif int(item.custom_id) == index and not correct:
                        item.style = discord.ButtonStyle.danger

            await interaction.response.edit_message(embed=embed, view=self)

        return callback

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True


# ── Cog ───────────────────────────────────────────────────────────────────────

class TriviaCog(commands.Cog, name="Trivia"):
    """Hosts trivia games and serves meme GIFs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    @app_commands.command(
        name="trivia",
        description="Start a trivia game about this server's culture.",
    )
    async def trivia_command(self, interaction: discord.Interaction) -> None:
        """Ask a random trivia question with button-based answers."""
        question = random.choice(_QUESTIONS)
        embed = base_embed(
            "🎭 Trivia Time",
            f"**{question.text}**\n\nYou have 30 seconds to answer, darling. 🎩",
        )
        view = TriviaView(question, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(
        name="meme",
        description="Get a random meme GIF.",
    )
    async def meme_command(self, interaction: discord.Interaction) -> None:
        """Fetch and post a random meme GIF from Tenor."""
        if not config.TENOR_API_KEY:
            await interaction.response.send_message(
                "🎭 Meme GIFs require a Tenor API key to be configured. 🎩",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        queries = ["funny meme", "mood meme", "relatable meme", "queen energy", "sassy meme"]
        gif_url = await _fetch_gif(random.choice(queries))
        if gif_url:
            await interaction.followup.send(gif_url)
        else:
            await interaction.followup.send(
                "I'm afraid the GIF vaults are momentarily unavailable, darling. 🎩"
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TriviaCog(bot))

