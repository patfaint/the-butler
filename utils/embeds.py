"""Reusable embed builders — all embeds use the pink server theme."""

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
    """Ephemeral error embed using the standard pink theme."""
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
        "You didn't end up here by accident.\n"
        "This is a space built on power, trust, and indulgence — "
        "where desire meets control and boundaries are respected above all else.\n\n"
        "Whether you're here to serve, explore, or simply observe… "
        "take a moment to settle in.\n\n"
        "🔒 Read the rules\n"
        "💬 Choose your roles\n"
        "💖 Know your limits — and respect everyone else's\n\n"
        "This is a consensual, 18+ space. Everything here runs on "
        "communication, respect, and mutual understanding.\n\n"
        "Now breathe, read the rules, verify… and enjoy your stay."
    )

    embed = discord.Embed(
        title="Welcome to The Drain Server 🌙",
        description=description,
        colour=PINK,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=FOOTER_TEXT)
    return embed
