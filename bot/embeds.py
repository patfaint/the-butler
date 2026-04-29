from __future__ import annotations

from datetime import datetime, timezone

import discord

from bot.config import BotConfig
from bot.database import VerificationRequest
from bot import messages
from bot.utils import mention_channel, user_mention

PURPLE = discord.Color.from_rgb(181, 101, 255)
PINK = discord.Color.from_rgb(255, 101, 178)
GREEN = discord.Color.from_rgb(59, 201, 122)
RED = discord.Color.from_rgb(235, 87, 87)
ORANGE = discord.Color.from_rgb(245, 145, 61)
SOFT_DARK = discord.Color.from_rgb(42, 37, 58)


def welcome_embed(member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title=messages.WELCOME_TITLE,
        description=messages.WELCOME_DESCRIPTION.format(user_mention=member.mention),
        color=PINK,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="The Butler • 18+ verification required")
    return embed


def verification_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title=messages.VERIFICATION_PANEL_TITLE,
        description=messages.VERIFICATION_PANEL_DESCRIPTION,
        color=PURPLE,
    )
    embed.set_footer(text="The Butler • Age verification")
    return embed


def initial_verification_dm_embed() -> discord.Embed:
    embed = discord.Embed(
        title=messages.INITIAL_VERIFICATION_DM_TITLE,
        description=messages.INITIAL_VERIFICATION_DM_DESCRIPTION,
        color=PURPLE,
    )
    embed.set_footer(text="The Butler • Verification expires in 5 minutes")
    return embed


def role_prompt_embed() -> discord.Embed:
    embed = discord.Embed(
        title=messages.ROLE_PROMPT_TITLE,
        description=messages.ROLE_PROMPT_DESCRIPTION,
        color=PINK,
    )
    embed.set_footer(text="The Butler • Role selection")
    return embed


def pending_review_embed() -> discord.Embed:
    embed = discord.Embed(
        title=messages.PENDING_REVIEW_TITLE,
        description=messages.PENDING_REVIEW_DESCRIPTION,
        color=PURPLE,
    )
    embed.set_footer(text="The Butler • Staff review pending")
    return embed


def approved_dm_embed(config: BotConfig) -> discord.Embed:
    embed = discord.Embed(
        title=messages.APPROVED_DM_TITLE,
        description=messages.APPROVED_DM_DESCRIPTION.format(
            roles_channel=mention_channel(config.roles_channel_id),
            introductions_channel=mention_channel(config.introductions_channel_id),
            general_channel=mention_channel(config.general_channel_id),
        ),
        color=GREEN,
    )
    embed.set_footer(text="The Butler • Welcome to The Drain Gang")
    return embed


def denied_underage_dm_embed() -> discord.Embed:
    embed = discord.Embed(
        title=messages.DENIED_UNDERAGE_DM_TITLE,
        description=messages.DENIED_UNDERAGE_DM_DESCRIPTION,
        color=RED,
    )
    embed.set_footer(text="The Butler • Verification denied")
    return embed


def denied_invalid_dm_embed() -> discord.Embed:
    embed = discord.Embed(
        title=messages.DENIED_INVALID_DM_TITLE,
        description=messages.DENIED_INVALID_DM_DESCRIPTION,
        color=ORANGE,
    )
    embed.set_footer(text="The Butler • Verification denied")
    return embed


def session_expired_dm_embed() -> discord.Embed:
    embed = discord.Embed(
        title=messages.SESSION_EXPIRED_DM_TITLE,
        description=messages.SESSION_EXPIRED_DM_DESCRIPTION,
        color=SOFT_DARK,
    )
    embed.set_footer(text="The Butler • Verification expired")
    return embed


def invalid_submission_dm_embed() -> discord.Embed:
    embed = discord.Embed(
        title=messages.INVALID_SUBMISSION_DM_TITLE,
        description=messages.INVALID_SUBMISSION_DM_DESCRIPTION,
        color=ORANGE,
    )
    embed.set_footer(text="The Butler • Try again")
    return embed


def verification_log_embed(
    request: VerificationRequest,
    member: discord.Member | None,
) -> discord.Embed:
    nickname_or_username = member.display_name if member else request.username
    verification_value = request.verification_value or "Not provided"
    verification_display = verification_value
    if request.verification_type == "Photo":
        verification_display = "Photo submitted below."

    embed = discord.Embed(
        title="New Age Verification Request",
        description=(
            f"**User:** {user_mention(request.user_id)} ({nickname_or_username})\n\n"
            f"**Verification Type:** {request.verification_type or 'Unknown'}\n\n"
            f"**Verification:**\n{verification_display}\n\n"
            f"**User has marked they are a {request.selected_role or 'Unknown'}**"
        ),
        color=PURPLE,
        timestamp=datetime.now(timezone.utc),
    )
    if member:
        embed.set_thumbnail(url=member.display_avatar.url)
    if request.verification_type == "Photo" and request.verification_value:
        embed.set_image(url=request.verification_value)
    embed.set_footer(text=f"The Butler • Request ID #{request.id}")
    return embed


def verification_outcome_embed(
    *,
    request: VerificationRequest,
    moderator: discord.Member | discord.User,
    title: str,
    color: discord.Color,
    status: str,
) -> discord.Embed:
    embed = discord.Embed(title=title, color=color)
    embed.add_field(
        name="User",
        value=f"{user_mention(request.user_id)} ({request.username})",
        inline=False,
    )
    embed.add_field(
        name="Selected Role",
        value=request.selected_role or "Unknown",
        inline=False,
    )
    embed.add_field(
        name="Verification Date",
        value=datetime.now(timezone.utc).strftime("%m/%d/%Y"),
        inline=False,
    )
    embed.add_field(
        name="Mod Responsible for Verification",
        value=f"{moderator.name} ({moderator.mention})",
        inline=False,
    )
    embed.add_field(
        name="Verification method",
        value=request.verification_type or "Unknown",
        inline=False,
    )
    embed.add_field(name="Status", value=status, inline=False)
    embed.set_footer(text=f"The Butler • Request ID #{request.id}")
    return embed


def verification_status_embed(
    request: VerificationRequest | None,
    user: discord.User | discord.Member,
) -> discord.Embed:
    embed = discord.Embed(title="Verification Status", color=PURPLE)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="User", value=f"{user.mention} ({user.name})", inline=False)

    if request is None:
        embed.description = "No verification record was found for this user."
    else:
        embed.add_field(name="Status", value=request.status, inline=True)
        embed.add_field(
            name="Selected Role",
            value=request.selected_role or "Not selected",
            inline=True,
        )
        embed.add_field(
            name="Verification method",
            value=request.verification_type or "Not submitted",
            inline=True,
        )
        embed.add_field(name="Submitted", value=request.submitted_at, inline=False)
        if request.reviewed_at:
            embed.add_field(name="Reviewed", value=request.reviewed_at, inline=False)
    embed.set_footer(text="The Butler • Staff only")
    return embed


def verification_cleanup_embed(
    *,
    role: discord.Role,
    members: list[discord.Member],
) -> discord.Embed:
    embed = discord.Embed(title="Unverified Cleanup", color=PURPLE)
    embed.description = f"Users who still have {role.mention}: **{len(members)}**"
    if members:
        visible_members = members[:25]
        lines = [f"• {member.mention} ({member.display_name})" for member in visible_members]
        if len(members) > len(visible_members):
            lines.append(f"• +{len(members) - len(visible_members)} more")
        embed.add_field(name="Members", value="\n".join(lines), inline=False)
    else:
        embed.add_field(name="Members", value="No users currently have this role.", inline=False)
    embed.set_footer(text="The Butler • Staff only")
    return embed


def help_page_embed(page_index: int, total_pages: int) -> discord.Embed:
    pages = (
        (
            "Verification Commands",
            (
                "**/setup-verification**\n"
                "Posts the verification panel in the configured verification channel.\n\n"
                "**/verify-status**\n"
                "Checks a user's verification status."
            ),
        ),
        (
            "Moderation Commands",
            (
                "**/verify-cleanup**\n"
                "Shows users who still have the Unverified role."
            ),
        ),
        (
            "System Commands",
            (
                "**/help**\n"
                "Shows the restricted bot help menu."
            ),
        ),
    )
    title, description = pages[page_index]
    embed = discord.Embed(
        title=title,
        description=description,
        color=PINK if page_index == 0 else PURPLE,
    )
    embed.set_footer(text=f"The Butler • Page {page_index + 1}/{total_pages}")
    return embed
