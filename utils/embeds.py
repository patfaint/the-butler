"""Reusable embed builders — all embeds use the pink server theme."""

from typing import Optional

import discord

PINK = 0xFF69B4
FOOTER_TEXT = "The Butler — At your service. 🎩"


def base_embed(
    title: str,
    description: str = "",
    colour: int = PINK,
) -> discord.Embed:
    """Return a pink embed with the standard footer."""
    embed = discord.Embed(title=title, description=description, colour=colour)
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def error_embed(description: str) -> discord.Embed:
    """Ephemeral error embed in a slightly darker pink."""
    embed = discord.Embed(description=f"⚠️ {description}", colour=PINK)
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def success_embed(description: str) -> discord.Embed:
    """Success confirmation embed."""
    embed = discord.Embed(description=f"✅ {description}", colour=PINK)
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def welcome_embed(member: discord.Member) -> discord.Embed:
    """Welcome embed sent to the welcome channel on member join."""
    description = (
        f"Hello {member.mention} and welcome to **The Drain Server**!\n\n"
        "you didn't end up here by accident.\n"
        "this is a space built on power, trust, and indulgence — "
        "where desire meets control and boundaries are respected above all else.\n\n"
        "whether you're here to serve, explore, or simply observe… "
        "take a moment to settle in.\n\n"
        "🔒 read the rules\n"
        "💬 choose your roles\n"
        "💖 know your limits — and respect everyone else's\n\n"
        "this is a consensual, 18+ space. everything here runs on "
        "communication, respect, and mutual understanding.\n\n"
        "now breathe, read the rules, verify… and enjoy your stay."
    )

    embed = discord.Embed(
        title="Welcome to The Drain Server 🌙",
        description=description,
        colour=PINK,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def help_page_embed(page: int, total_pages: int) -> discord.Embed:
    """Return the correct help page embed."""
    pages = _build_help_pages(total_pages)
    return pages[page]


def _build_help_pages(total_pages: int) -> list[discord.Embed]:
    """Build all help page embeds."""

    def _page(title: str, fields: list[tuple[str, str]], page_num: int) -> discord.Embed:
        embed = discord.Embed(title=title, colour=PINK)
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
        embed.set_footer(
            text=f"{FOOTER_TEXT} | Page {page_num} of {total_pages}"
        )
        return embed

    page1 = _page(
        "👑 Domme Commands",
        [
            ("`/setup`", "Configure your Butler profile *(Domme only)*"),
            ("`/coffee`", "Alert all subs you're seeking coffee *(Domme only)*"),
            ("`/throne`", "Register or display your Throne wishlist link *(Domme only)*"),
            ("`/confirm @sub $amount`", "Confirm a sub's tribute *(Domme only)*"),
            ("`/jail @user <duration>`", "Send someone to jail *(Domme/Admin only)*"),
            ("`/release @user`", "Release someone from jail early *(Domme/Admin only)*"),
        ],
        1,
    )

    page2 = _page(
        "🐾 Sub Commands",
        [
            ("`/tribute @domme $amount`", "Log a tribute to a domme"),
            ("`/wishlist @domme`", "View a domme's Throne wishlist link"),
            ("`/leaderboard`", "View the server tribute leaderboard"),
            ("`/stats`", "View your personal tribute stats"),
        ],
        2,
    )

    page3 = _page(
        "🎭 Fun Commands",
        [
            ("`/trivia`", "Start a trivia game"),
            ("`/meme`", "Get a random meme GIF"),
        ],
        3,
    )

    page4 = _page(
        "🔧 Admin Commands",
        [
            ("`/setverificationchannel #channel`", "Set the verification channel"),
            ("`/setwelcomechannel #channel`", "Set the welcome channel"),
            ("`/setleaderboardchannel #channel`", "Set the leaderboard channel"),
            ("`/setjailrole @role`", "Set the jail role"),
            ("`/setdommerole @role`", "Set the Domme role"),
            ("`/setsubrole @role`", "Set the Sub role"),
        ],
        4,
    )

    return [page1, page2, page3, page4]
