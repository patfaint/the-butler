from __future__ import annotations

from datetime import datetime, timezone

import discord

from bot import messages
from bot.config import BotConfig
from bot.database import DommeProfile, VerificationRequest
from bot.utils import mention_channel, user_mention

PURPLE = discord.Color.from_rgb(181, 101, 255)
PINK = discord.Color.from_rgb(255, 101, 178)
GREEN = discord.Color.from_rgb(59, 201, 122)
RED = discord.Color.from_rgb(235, 87, 87)
ORANGE = discord.Color.from_rgb(245, 145, 61)
SOFT_DARK = discord.Color.from_rgb(42, 37, 58)


def _styled_embed(
    *,
    title: str,
    description: str,
    color: discord.Color,
) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)


def _profile_value(value: str | None) -> str:
    return value.strip() if value and value.strip() else "Not provided"


def _feature_value(enabled: bool) -> str:
    return "Yes" if enabled else "No"


def _add_chunked_field(
    embed: discord.Embed,
    *,
    name: str,
    lines: list[str],
) -> None:
    chunks: list[str] = []
    current_lines: list[str] = []
    current_length = 0

    for line in lines:
        line_length = len(line)
        projected_length = line_length if not current_lines else current_length + 1 + line_length
        if current_lines and projected_length > 1024:
            chunks.append("\n".join(current_lines))
            current_lines = [line]
            current_length = line_length
            continue

        current_lines.append(line)
        current_length = projected_length

    if current_lines:
        chunks.append("\n".join(current_lines))

    for index, chunk in enumerate(chunks):
        heading = name if index == 0 else f"{name} (cont.)"
        embed.add_field(name=heading, value=chunk, inline=False)


def _payment_lines(
    *,
    throne: str | None,
    paypal: str | None,
    youpay: str | None,
    cashapp: str | None,
    venmo: str | None,
    beemit: str | None,
    loyalfans: str | None,
    onlyfans: str | None,
) -> list[str]:
    return [
        f"**Throne:** {_profile_value(throne)}",
        f"**PayPal:** {_profile_value(paypal)}",
        f"**YouPay:** {_profile_value(youpay)}",
        f"**Cashapp:** {_profile_value(cashapp)}",
        f"**Venmo:** {_profile_value(venmo)}",
        f"**Beemit:** {_profile_value(beemit)}",
        f"**Loyalfans:** {_profile_value(loyalfans)}",
        f"**Onlyfans:** {_profile_value(onlyfans)}",
    ]


def welcome_embed(member: discord.Member) -> discord.Embed:
    embed = _styled_embed(
        title=messages.WELCOME_TITLE,
        description=messages.WELCOME_DESCRIPTION.format(user_mention=member.mention),
        color=PINK,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="The Butler • 18+ verification required")
    return embed


def verification_panel_embed() -> discord.Embed:
    embed = _styled_embed(
        title=messages.VERIFICATION_PANEL_TITLE,
        description=messages.VERIFICATION_PANEL_DESCRIPTION,
        color=PURPLE,
    )
    embed.set_footer(text="The Butler • Age verification")
    return embed


def initial_verification_dm_embed(notice: str | None = None) -> discord.Embed:
    embed = _styled_embed(
        title=messages.INITIAL_VERIFICATION_DM_TITLE,
        description=messages.INITIAL_VERIFICATION_DM_DESCRIPTION,
        color=PURPLE,
    )
    if notice:
        embed.add_field(name="Invalid Submission", value=notice, inline=False)
    embed.set_footer(text="The Butler • Verification expires in 5 minutes")
    return embed


def role_prompt_embed(selected_role: str | None = None) -> discord.Embed:
    embed = _styled_embed(
        title=messages.ROLE_PROMPT_TITLE,
        description=messages.ROLE_PROMPT_DESCRIPTION,
        color=PINK,
    )
    if selected_role:
        embed.add_field(name="Selected Role", value=selected_role, inline=False)
    embed.set_footer(text="The Butler • Role selection")
    return embed


def pending_review_embed() -> discord.Embed:
    embed = _styled_embed(
        title=messages.PENDING_REVIEW_TITLE,
        description=messages.PENDING_REVIEW_DESCRIPTION,
        color=PURPLE,
    )
    embed.set_footer(text="The Butler • Staff review pending")
    return embed


def approved_dm_embed(config: BotConfig) -> discord.Embed:
    embed = _styled_embed(
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
    embed = _styled_embed(
        title=messages.DENIED_UNDERAGE_DM_TITLE,
        description=messages.DENIED_UNDERAGE_DM_DESCRIPTION,
        color=RED,
    )
    embed.set_footer(text="The Butler • Verification denied")
    return embed


def denied_invalid_dm_embed() -> discord.Embed:
    embed = _styled_embed(
        title=messages.DENIED_INVALID_DM_TITLE,
        description=messages.DENIED_INVALID_DM_DESCRIPTION,
        color=ORANGE,
    )
    embed.set_footer(text="The Butler • Verification denied")
    return embed


def session_expired_dm_embed() -> discord.Embed:
    embed = _styled_embed(
        title=messages.SESSION_EXPIRED_DM_TITLE,
        description=messages.SESSION_EXPIRED_DM_DESCRIPTION,
        color=SOFT_DARK,
    )
    embed.set_footer(text="The Butler • Verification expired")
    return embed


def invalid_submission_dm_embed() -> discord.Embed:
    embed = _styled_embed(
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
            "Verification",
            PINK,
            "Verification commands and panel setup.",
            (
                ("!setup_verification", "Posts the verification panel in the configured verification channel."),
                ("!verify_status <user>", "Checks a user's verification status."),
            ),
        ),
        (
            "Moderation",
            PURPLE,
            "Moderation tools for the verification queue.",
            (
                ("!verify_cleanup", "Shows users who still have the Unverified role."),
            ),
        ),
        (
            "System",
            SOFT_DARK,
            "Restricted system controls and reference tools.",
            (
                ("/help", "Shows the restricted bot help menu."),
            ),
        ),
        (
            "Profiles",
            PINK,
            "Domme profile setup and profile management.",
            (
                ("/domme", "Starts your Domme profile setup or shows your saved profile."),
                ("/domme action:delete", "Deletes your saved Domme profile after confirmation."),
            ),
        ),
    )
    section, color, blurb, entries = pages[page_index]
    embed = discord.Embed(
        title="The Butler Command Guide",
        description=f"**{section}**\n{blurb}",
        color=color,
    )
    for name, description in entries:
        embed.add_field(name=name, value=description, inline=False)
    embed.set_footer(text=f"The Butler • Page {page_index + 1}/{total_pages}")
    return embed


def domme_setup_intro_embed() -> discord.Embed:
    embed = _styled_embed(
        title=messages.DOMME_SETUP_INTRO_TITLE,
        description=messages.DOMME_SETUP_INTRO_DESCRIPTION,
        color=PINK,
    )
    embed.set_footer(text="The Butler • Domme profile setup")
    return embed


def domme_setup_name_embed(*, name: str | None, honorific: str | None) -> discord.Embed:
    embed = _styled_embed(
        title=messages.DOMME_SETUP_NAME_TITLE,
        description=messages.DOMME_SETUP_NAME_DESCRIPTION,
        color=PINK,
    )
    embed.add_field(name="Name", value=_profile_value(name), inline=False)
    embed.add_field(name="Honorific", value=_profile_value(honorific), inline=False)
    embed.set_footer(text="The Butler • Step 1/5")
    return embed


def domme_setup_details_embed(
    *,
    pronouns: str | None,
    age: str | None,
    tribute_price: str | None,
) -> discord.Embed:
    embed = _styled_embed(
        title=messages.DOMME_SETUP_DETAILS_TITLE,
        description=messages.DOMME_SETUP_DETAILS_DESCRIPTION,
        color=PURPLE,
    )
    embed.add_field(name="Pronouns", value=_profile_value(pronouns), inline=False)
    embed.add_field(name="Age", value=_profile_value(age), inline=True)
    embed.add_field(name="Tribute Fee Price", value=_profile_value(tribute_price), inline=True)
    embed.set_footer(text="The Butler • Step 2/5")
    return embed


def domme_setup_payments_embed(
    *,
    throne: str | None,
    paypal: str | None,
    youpay: str | None,
    cashapp: str | None,
    venmo: str | None,
    beemit: str | None,
    loyalfans: str | None,
    onlyfans: str | None,
) -> discord.Embed:
    embed = _styled_embed(
        title=messages.DOMME_SETUP_PAYMENTS_TITLE,
        description=messages.DOMME_SETUP_PAYMENTS_DESCRIPTION,
        color=PURPLE,
    )
    embed.add_field(name="Throne", value=_profile_value(throne), inline=False)
    embed.add_field(name="PayPal", value=_profile_value(paypal), inline=True)
    embed.add_field(name="YouPay", value=_profile_value(youpay), inline=True)
    embed.add_field(name="Cashapp", value=_profile_value(cashapp), inline=True)
    embed.add_field(name="Venmo", value=_profile_value(venmo), inline=True)
    embed.add_field(name="Beemit", value=_profile_value(beemit), inline=True)
    embed.add_field(name="Loyalfans", value=_profile_value(loyalfans), inline=True)
    embed.add_field(name="Onlyfans", value=_profile_value(onlyfans), inline=True)
    embed.set_footer(text="The Butler • Step 3/5")
    return embed


def domme_setup_throne_embed(*, throne: str | None) -> discord.Embed:
    embed = _styled_embed(
        title=messages.DOMME_SETUP_THRONE_TITLE,
        description=messages.DOMME_SETUP_THRONE_DESCRIPTION,
        color=PINK,
    )
    embed.add_field(name="Throne", value=_profile_value(throne), inline=False)
    embed.set_footer(text="The Butler • Step 4/5")
    return embed


def domme_setup_coffee_embed(*, coffee_enabled: bool | None = None) -> discord.Embed:
    embed = _styled_embed(
        title=messages.DOMME_SETUP_COFFEE_TITLE,
        description=messages.DOMME_SETUP_COFFEE_DESCRIPTION,
        color=PINK,
    )
    if coffee_enabled is not None:
        embed.add_field(name="Current Selection", value=_feature_value(coffee_enabled), inline=False)
    embed.set_footer(text="The Butler • Step 5/5")
    return embed


def domme_setup_review_embed(
    *,
    name: str | None,
    honorific: str | None,
    pronouns: str | None,
    age: str | None,
    tribute_price: str | None,
    throne: str | None,
    paypal: str | None,
    youpay: str | None,
    cashapp: str | None,
    venmo: str | None,
    beemit: str | None,
    loyalfans: str | None,
    onlyfans: str | None,
    throne_tracking_enabled: bool,
    coffee_enabled: bool,
) -> discord.Embed:
    embed = _styled_embed(
        title=messages.DOMME_SETUP_REVIEW_TITLE,
        description=messages.DOMME_SETUP_REVIEW_DESCRIPTION,
        color=GREEN,
    )
    embed.add_field(
        name="Identity",
        value=(
            f"**Name:** {_profile_value(name)}\n"
            f"**Honorific:** {_profile_value(honorific)}\n"
            f"**Pronouns:** {_profile_value(pronouns)}"
        ),
        inline=False,
    )
    embed.add_field(
        name="Details",
        value=(
            f"**Age:** {_profile_value(age)}\n"
            f"**Tribute Fee Price:** {_profile_value(tribute_price)}"
        ),
        inline=False,
    )
    _add_chunked_field(
        embed,
        name="Payment Methods",
        lines=_payment_lines(
            throne=throne,
            paypal=paypal,
            youpay=youpay,
            cashapp=cashapp,
            venmo=venmo,
            beemit=beemit,
            loyalfans=loyalfans,
            onlyfans=onlyfans,
        ),
    )
    embed.add_field(
        name="Features",
        value=(
            f"**Throne Tracking:** {_feature_value(throne_tracking_enabled)}\n"
            f"**Coffee Feature:** {_feature_value(coffee_enabled)}"
        ),
        inline=False,
    )
    embed.set_footer(text="The Butler • Ready to save")
    return embed


def domme_setup_complete_embed() -> discord.Embed:
    embed = _styled_embed(
        title=messages.DOMME_SETUP_COMPLETE_TITLE,
        description=messages.DOMME_SETUP_COMPLETE_DESCRIPTION,
        color=GREEN,
    )
    embed.set_footer(text="The Butler • Profile saved")
    return embed


def domme_setup_later_embed() -> discord.Embed:
    embed = _styled_embed(
        title=messages.DOMME_SETUP_LATER_TITLE,
        description=messages.DOMME_SETUP_LATER_DESCRIPTION,
        color=SOFT_DARK,
    )
    embed.set_footer(text="The Butler • Setup paused")
    return embed


def domme_setup_cancelled_embed() -> discord.Embed:
    embed = _styled_embed(
        title=messages.DOMME_SETUP_CANCELLED_TITLE,
        description=messages.DOMME_SETUP_CANCELLED_DESCRIPTION,
        color=SOFT_DARK,
    )
    embed.set_footer(text="The Butler • Setup cancelled")
    return embed


def domme_profile_embed(
    profile: DommeProfile,
    member: discord.Member | discord.User,
) -> discord.Embed:
    embed = discord.Embed(
        title=f"{member.display_name if isinstance(member, discord.Member) else member.name}'s Domme Profile",
        color=PINK,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(
        name="Identity",
        value=(
            f"**Name:** {_profile_value(profile.name)}\n"
            f"**Honorific:** {_profile_value(profile.honorific)}\n"
            f"**Pronouns:** {_profile_value(profile.pronouns)}"
        ),
        inline=False,
    )
    embed.add_field(
        name="Details",
        value=(
            f"**Age:** {_profile_value(profile.age)}\n"
            f"**Tribute Fee Price:** {_profile_value(profile.tribute_price)}"
        ),
        inline=False,
    )
    _add_chunked_field(
        embed,
        name="Payment Methods",
        lines=_payment_lines(
            throne=profile.throne,
            paypal=profile.paypal,
            youpay=profile.youpay,
            cashapp=profile.cashapp,
            venmo=profile.venmo,
            beemit=profile.beemit,
            loyalfans=profile.loyalfans,
            onlyfans=profile.onlyfans,
        ),
    )
    embed.add_field(
        name="Features",
        value=(
            f"**Throne Tracking:** {_feature_value(profile.throne_tracking_enabled)}\n"
            f"**Coffee Feature:** {_feature_value(profile.coffee_enabled)}"
        ),
        inline=False,
    )
    try:
        created = datetime.fromisoformat(profile.created_at)
        created_label = created.strftime("%m/%d/%Y")
    except ValueError:
        created_label = profile.created_at
    embed.set_footer(text=f"The Butler • Profile created {created_label}")
    return embed
