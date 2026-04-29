from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import discord

from bot.config import BotConfig
from bot.messages import APPROVED_DOMAINS

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
IMAGE_CONTENT_TYPES = ("image/png", "image/jpeg", "image/jpg", "image/webp")
URL_RE = re.compile(r"(https?://[^\s<>()]+|(?:[\w-]+\.)+[a-z]{2,}(?:/[^\s<>()]*)?)", re.I)
TRAILING_URL_PUNCTUATION = ".,!?;:)]}>\"'"


@dataclass(frozen=True)
class VerificationSubmission:
    verification_type: str
    verification_value: str


def has_moderation_permissions(member: discord.Member, config: BotConfig) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    return any(role.id == config.moderation_role_id for role in member.roles)


async def resolve_message_channel(
    bot: discord.Client,
    guild: discord.Guild,
    channel_id: int,
) -> discord.abc.Messageable | None:
    channel = guild.get_channel(channel_id) or bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            logging.warning("Could not resolve configured channel %s.", channel_id)
            return None

    if isinstance(channel, (discord.TextChannel, discord.Thread, discord.DMChannel)):
        return channel

    logging.warning("Configured channel %s is not messageable.", channel_id)
    return None


async def safe_dm(user: discord.abc.User, **kwargs: object) -> bool:
    try:
        await user.send(**kwargs)
    except (discord.Forbidden, discord.HTTPException):
        return False
    return True


def extract_verification_submission(message: discord.Message) -> VerificationSubmission | None:
    attachment_submission = _extract_image_attachment(message)
    if attachment_submission:
        return attachment_submission

    approved_link = _extract_approved_link(message.content)
    if approved_link:
        return VerificationSubmission("Link", approved_link)

    image_link = _extract_image_link(message.content)
    if image_link:
        return VerificationSubmission("Photo", image_link)

    return None


def mention_channel(channel_id: int) -> str:
    return f"<#{channel_id}>"


def mention_role(role_id: int) -> str:
    return f"<@&{role_id}>"


def user_mention(user_id: int) -> str:
    return f"<@{user_id}>"


def display_username(user: discord.abc.User) -> str:
    return getattr(user, "display_name", None) or user.name


def _extract_image_attachment(message: discord.Message) -> VerificationSubmission | None:
    for attachment in message.attachments:
        filename = attachment.filename.lower()
        content_type = (attachment.content_type or "").lower()
        if filename.endswith(IMAGE_EXTENSIONS) or content_type in IMAGE_CONTENT_TYPES:
            return VerificationSubmission("Photo", attachment.url)
    return None


def _extract_approved_link(content: str) -> str | None:
    for candidate in _url_candidates(content):
        parsed = urlparse(candidate)
        hostname = (parsed.hostname or "").lower()
        if _is_approved_domain(hostname):
            return candidate
    return None


def _extract_image_link(content: str) -> str | None:
    for candidate in _url_candidates(content):
        parsed = urlparse(candidate)
        path = parsed.path.lower()
        if path.endswith(IMAGE_EXTENSIONS):
            return candidate
    return None


def _url_candidates(content: str) -> list[str]:
    candidates: list[str] = []
    for match in URL_RE.finditer(content or ""):
        value = match.group(0).strip().strip("`").rstrip(TRAILING_URL_PUNCTUATION)
        if not value:
            continue
        if not value.startswith(("http://", "https://")):
            value = f"https://{value}"
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            candidates.append(value)
    return candidates


def _is_approved_domain(hostname: str) -> bool:
    hostname = hostname.removeprefix("www.")
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in APPROVED_DOMAINS)
