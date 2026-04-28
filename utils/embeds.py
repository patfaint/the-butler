"""Reusable embed builders — all embeds use the pink server theme."""

import discord

PINK = 0xFF69B4
FOOTER_TEXT = "The Butler — At your service. 🎩"
TOTAL_HELP_PAGES = 5  # Single source of truth for the help paginator page count.


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


def help_page_embed(page: int) -> discord.Embed:
    """Return the help page embed for *page* (0-indexed)."""
    return _build_help_pages()[page]


def _build_help_pages() -> list[discord.Embed]:
    """Build all help page embeds."""

    def _page(title: str, fields: list[tuple[str, str]], page_num: int) -> discord.Embed:
        embed = discord.Embed(title=title, colour=PINK)
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
        embed.set_footer(
            text=f"{FOOTER_TEXT} | Page {page_num} of {TOTAL_HELP_PAGES}"
        )
        return embed

    page1 = _page(
        "👑 Domme Commands",
        [
            ("`/setup`", "Configure your Butler profile — display name, Throne link, coffee amount & scaling"),
            ("`/myprofile`", "View your current Butler profile"),
            ("`/throne <link>`", "Register or update your Throne wishlist link"),
            ("`/coffee`", "Alert all subs you're seeking coffee with dynamic pricing"),
            ("`/confirm @sub $amount`", "Confirm a sub's tribute"),
            ("`/jail @user <duration> [reason]`", "Send someone to jail (e.g. `1h`, `30m`, `2d`)"),
            ("`/release @user`", "Release someone from jail early"),
            ("`/givevip @member <duration>`", "Grant a member a time-limited VIP role"),
        ],
        1,
    )

    page2 = _page(
        "🐾 Sub Commands",
        [
            ("`/tribute @domme $amount`", "Submit a tribute to a Domme (awaits confirmation)"),
            ("`/wishlist @domme`", "View a Domme's Throne wishlist link"),
            ("`/leaderboard`", "View the server tribute leaderboard"),
            ("`/stats`", "View your personal tribute stats and longest streak"),
        ],
        2,
    )

    page3 = _page(
        "🎭 Fun & Verification",
        [
            ("`/trivia`", "Start a button-based trivia game (30 second timer)"),
            ("`/meme`", "Get a random meme GIF via Tenor"),
            ("`/sendverification`", "Post the verification embed in the verification channel *(Admin)*"),
        ],
        3,
    )

    page4 = _page(
        "🔧 Admin — Channels",
        [
            ("`/setwelcomechannel #channel`", "Set the welcome channel"),
            ("`/setleaderboardchannel #channel`", "Set the leaderboard/tribute confirmation channel"),
            ("`/setannouncementchannel #channel`", "Set the announcement channel for coffee alerts"),
            ("`/setverificationchannel #channel`", "Set the verification channel"),
        ],
        4,
    )

    page5 = _page(
        "🔧 Admin — Roles",
        [
            ("`/setdommerole @role`", "Set the Domme role"),
            ("`/setsubrole @role`", "Set the Sub role"),
            ("`/setjailrole @role`", "Set the jail role"),
            ("`/setadminrole @role`", "Set the admin role"),
            ("`/setviprole @role`", "Set the VIP role for time-limited grants"),
        ],
        5,
    )

    return [page1, page2, page3, page4, page5]

