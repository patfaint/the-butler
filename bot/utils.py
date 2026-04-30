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

# Maps hostname suffixes → display label for smart link detection
_PLATFORM_DOMAIN_MAP: dict[str, str] = {
    # Tribute / wishlist platforms
    "throne.com": "Throne",
    "throne.gifts": "Throne",
    "amazon.com": "Amazon Wishlist",
    "amazon.com.au": "Amazon Wishlist",
    "amazon.co.uk": "Amazon Wishlist",
    "amazon.ca": "Amazon Wishlist",
    "amazon.de": "Amazon Wishlist",
    "amazon.fr": "Amazon Wishlist",
    "amazon.es": "Amazon Wishlist",
    "amazon.it": "Amazon Wishlist",
    "amazon.co.jp": "Amazon Wishlist",
    "wishlst.me": "Wishlst",
    "elfster.com": "Elfster",
    "giftster.com": "Giftster",
    # Payment platforms
    "paypal.me": "PayPal",
    "paypal.com": "PayPal",
    "cash.app": "CashApp",
    "cashapp.com": "CashApp",
    "venmo.com": "Venmo",
    "beemit.com": "Beemit",
    "youpay.co": "YouPay",
    "youpay.com": "YouPay",
    "ko-fi.com": "Ko-fi",
    "buymeacoffee.com": "Buy Me a Coffee",
    "gofundme.com": "GoFundMe",
    "patreon.com": "Patreon",
    "stripe.com": "Stripe",
    "revolut.com": "Revolut",
    "wise.com": "Wise",
    "monzo.me": "Monzo",
    # Adult content platforms
    "onlyfans.com": "OnlyFans",
    "loyalfans.com": "LoyalFans",
    "fansly.com": "Fansly",
    "manyvids.com": "ManyVids",
    "clips4sale.com": "Clips4Sale",
    "iwantclips.com": "iWantClips",
    "fancentro.com": "FanCentro",
    "unfiltrd.com": "Unfiltrd",
    "niteflirt.com": "NiteFlirt",
    "fetishfinder.com": "FetishFinder",
    "feetfinder.com": "FeetFinder",
    "admireme.com": "AdmireMe",
    "justfor.fans": "JustFor.Fans",
    "frisk.chat": "Frisk",
    "avnstars.com": "AVN Stars",
    "avn.com": "AVN",
    "pornhub.com": "Pornhub",
    "modelhub.com": "ModelHub",
    "4based.com": "4Based",
    "slushy.com": "Slushy",
    # Bio / link-in-bio platforms
    "linktr.ee": "Linktree",
    "linktree.com": "Linktree",
    "beacons.ai": "Beacons",
    "beacons.page": "Beacons",
    "allmylinks.com": "AllMyLinks",
    "sentin.bio": "Sentin Bio",
    "bio.link": "Bio.link",
    "solo.to": "Solo.to",
    "msha.ke": "Milkshake",
    "milkshake.app": "Milkshake",
    "snipfeed.co": "Snipfeed",
    "carrd.co": "Carrd",
    "about.me": "About.me",
    "lnk.bio": "Lnk.bio",
    "taplink.cc": "TapLink",
    "tap.bio": "Tap.bio",
    "hoo.be": "Hoo.be",
    "bento.me": "Bento",
    "campsite.bio": "Campsite",
    "flowpage.com": "Flowpage",
    "url.bio": "url.bio",
    "contactinbio.com": "ContactInBio",
    "stan.store": "Stan.store",
    "znap.link": "Znap",
    "koji.com": "Koji",
    "shorby.com": "Shorby",
    "instabio.cc": "InstaBio",
    "mystrikingly.com": "Strikingly",
    "strikingly.com": "Strikingly",
    # Social platforms
    "twitter.com": "Twitter/X",
    "x.com": "Twitter/X",
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "reddit.com": "Reddit",
    "snapchat.com": "Snapchat",
    "telegram.me": "Telegram",
    "t.me": "Telegram",
    "discord.gg": "Discord",
    "discord.com": "Discord",
    "twitch.tv": "Twitch",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "pinterest.com": "Pinterest",
    "tumblr.com": "Tumblr",
    "mastodon.social": "Mastodon",
    "bluesky.app": "Bluesky",
    "bsky.app": "Bluesky",
}


def detect_platform(url: str) -> str:
    """Return a human-readable platform label derived from the URL.

    Falls back to a capitalised hostname stem if the domain is not in the
    known-platform map, or to the raw URL if the hostname cannot be parsed.
    """
    if not url:
        return url
    candidate = url if url.startswith(("http://", "https://")) else f"https://{url}"
    parsed = urlparse(candidate)
    hostname = (parsed.hostname or "").lower().removeprefix("www.")
    # Longest-suffix match so "paypal.me" beats "me"
    for domain in sorted(_PLATFORM_DOMAIN_MAP, key=len, reverse=True):
        if hostname == domain or hostname.endswith(f".{domain}"):
            return _PLATFORM_DOMAIN_MAP[domain]
    # Fall back: capitalise the first label of the hostname
    if hostname:
        return hostname.split(".")[0].capitalize()
    return url


@dataclass(frozen=True)
class VerificationSubmission:
    verification_type: str
    verification_value: str


def has_moderation_role(member: discord.Member, config: BotConfig) -> bool:
    return any(role.id == config.moderation_role_id for role in member.roles)


def has_admin_command_permissions(member: discord.Member, config: BotConfig) -> bool:
    if member.guild_permissions.administrator:
        return True
    return has_moderation_role(member, config)


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
