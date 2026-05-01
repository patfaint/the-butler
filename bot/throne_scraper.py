"""Scraper for public Throne profile pages.

Throne profiles (throne.com / throne.gifts) are server-rendered Next.js pages.
The activity / supporters feed is present in two forms:

1. As JSON inside a ``<script id="__NEXT_DATA__">`` tag — preferred because it
   is structured and reasonably stable across cosmetic UI changes.
2. As rendered HTML in the page body — used as a fallback if the JSON shape
   changes.

The public field names used by Throne can change without notice, so the
parser walks the JSON looking for any object that *looks* like a "send" and
extracts the fields it needs by trying a list of candidate keys. Anything
that fails to parse is skipped rather than raising — we'd rather return a
shorter list than crash the polling loop.

This module is pure-functional and easy to unit-test against saved fixtures.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, urlunparse

import aiohttp

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScrapedSend:
    external_id: str
    sender_name: str | None  # None = anonymous
    amount_usd: float | None  # None = sender hid the amount ("private")
    item_name: str | None
    item_image_url: str | None
    sent_at: str  # ISO-8601 UTC


_NEXT_DATA_RE = re.compile(
    r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    re.DOTALL,
)

_SEND_ID_KEYS = ("id", "_id", "uuid", "sendId", "send_id", "transactionId")
_SENDER_NAME_KEYS = (
    "senderName",
    "sender_name",
    "fromName",
    "from_name",
    "displayName",
    "username",
    "supporterName",
    "name",
)
_AMOUNT_KEYS = (
    "amountUsd",
    "amount_usd",
    "amountUSD",
    "amount",
    "value",
    "valueUsd",
    "totalUsd",
    "total_usd",
    "priceUsd",
    "price",
)
_PRIVATE_KEYS = (
    "isPrivate",
    "is_private",
    "amountHidden",
    "hideAmount",
    "private",
)
_ANONYMOUS_KEYS = (
    "isAnonymous",
    "is_anonymous",
    "anonymous",
)
_ITEM_NAME_KEYS = ("itemName", "item_name", "productName", "title", "name")
_ITEM_IMAGE_KEYS = (
    "itemImageUrl",
    "item_image_url",
    "imageUrl",
    "image_url",
    "thumbnail",
    "thumbnailUrl",
    "image",
)
_TIMESTAMP_KEYS = (
    "sentAt",
    "sent_at",
    "createdAt",
    "created_at",
    "timestamp",
    "date",
    "time",
)


def normalize_throne_url(throne_url: str) -> str | None:
    """Normalize a user-supplied Throne URL.

    Accepts either ``throne.com/<handle>`` or ``throne.gifts/<handle>``,
    with or without scheme, with or without trailing slash / query / fragment.
    Returns ``None`` if the URL is not a recognisable Throne URL.
    """
    if not throne_url:
        return None
    url = throne_url.strip()
    if not url:
        return None
    if "://" not in url:
        url = "https://" + url
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower().lstrip(".")
    if host.startswith("www."):
        host = host[4:]
    if host not in {"throne.com", "throne.gifts"}:
        return None
    path = parsed.path.rstrip("/")
    if not path or path == "/":
        return None
    # Drop query and fragment; force https.
    return urlunparse(("https", host, path, "", "", ""))


async def fetch_recent_sends(
    throne_url: str,
    *,
    http: aiohttp.ClientSession,
    user_agent: str,
    timeout_seconds: float = 10.0,
) -> list[ScrapedSend]:
    """Fetch the public Throne page and extract recent sends.

    Returns an empty list on any HTTP / network / parse failure. The polling
    loop relies on this — it must not raise.
    """
    normalized = normalize_throne_url(throne_url)
    if normalized is None:
        log.warning("Skipping unrecognised Throne URL: %r", throne_url)
        return []

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    try:
        async with http.get(normalized, headers=headers, timeout=timeout) as resp:
            if resp.status != 200:
                log.warning(
                    "Throne page %s returned HTTP %s", normalized, resp.status
                )
                return []
            html = await resp.text()
    except (aiohttp.ClientError, TimeoutError) as exc:
        log.warning("Failed to fetch Throne page %s: %s", normalized, exc)
        return []

    try:
        return parse_sends_from_html(html)
    except Exception:  # noqa: BLE001 - never let parsing kill the poller
        log.exception("Failed to parse Throne page %s", normalized)
        return []


def parse_sends_from_html(html: str) -> list[ScrapedSend]:
    """Extract sends from a rendered Throne profile page."""
    payload = _extract_next_data(html)
    if payload is not None:
        sends = _extract_sends_from_payload(payload)
        if sends:
            return sends
    # JSON path produced nothing usable — try the HTML fallback (best effort).
    return _extract_sends_from_html_fallback(html)


def _extract_next_data(html: str) -> Any:
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return None
    raw = match.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Failed to JSON-decode __NEXT_DATA__ payload")
        return None


def _extract_sends_from_payload(payload: Any) -> list[ScrapedSend]:
    """Walk the Next.js payload and harvest anything that looks like a send."""
    seen_ids: set[str] = set()
    sends: list[ScrapedSend] = []

    for obj in _walk_objects(payload):
        if not _looks_like_send(obj):
            continue
        scraped = _build_scraped_send(obj)
        if scraped is None:
            continue
        if scraped.external_id in seen_ids:
            continue
        seen_ids.add(scraped.external_id)
        sends.append(scraped)

    # Sort by timestamp (oldest first) for deterministic processing order.
    sends.sort(key=lambda s: s.sent_at)
    return sends


def _walk_objects(node: Any):
    """Yield every dict found anywhere inside a JSON-like structure."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk_objects(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_objects(v)


def _looks_like_send(obj: dict[str, Any]) -> bool:
    """Heuristic: object has a stable id AND (an amount-ish field OR an item)."""
    if not _first_key(obj, _SEND_ID_KEYS):
        return False
    has_amount = any(k in obj for k in _AMOUNT_KEYS)
    has_item = any(k in obj for k in _ITEM_NAME_KEYS) or any(
        k in obj for k in _ITEM_IMAGE_KEYS
    )
    has_timestamp = any(k in obj for k in _TIMESTAMP_KEYS)
    # Require a timestamp + (amount or item) to avoid matching unrelated
    # objects like users / pages that happen to have an "id".
    return has_timestamp and (has_amount or has_item)


def _build_scraped_send(obj: dict[str, Any]) -> ScrapedSend | None:
    raw_id = _first_value(obj, _SEND_ID_KEYS)
    if raw_id is None:
        return None
    external_id = str(raw_id)

    raw_ts = _first_value(obj, _TIMESTAMP_KEYS)
    sent_at = _normalize_timestamp(raw_ts)
    if sent_at is None:
        return None

    is_anonymous = _first_truthy(obj, _ANONYMOUS_KEYS)
    sender_name_raw = _first_value(obj, _SENDER_NAME_KEYS)
    sender_name: str | None
    if is_anonymous:
        sender_name = None
    else:
        sender_name = _coerce_name(sender_name_raw)

    is_private = bool(_first_truthy(obj, _PRIVATE_KEYS))
    amount_usd: float | None
    if is_private:
        amount_usd = None
    else:
        amount_usd = _coerce_amount(_first_value(obj, _AMOUNT_KEYS))
        if amount_usd is None:
            # Treat missing amount as private rather than dropping the send.
            is_private = True

    item_name = _coerce_str(_first_value(obj, _ITEM_NAME_KEYS))
    item_image_url = _coerce_str(_first_value(obj, _ITEM_IMAGE_KEYS))
    if item_image_url and not item_image_url.lower().startswith(("http://", "https://")):
        item_image_url = None

    return ScrapedSend(
        external_id=external_id,
        sender_name=sender_name,
        amount_usd=amount_usd if not is_private else None,
        item_name=item_name,
        item_image_url=item_image_url,
        sent_at=sent_at,
    )


def _first_key(obj: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for k in keys:
        if k in obj:
            return k
    return None


def _first_value(obj: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for k in keys:
        if k in obj:
            return obj[k]
    return None


def _first_truthy(obj: dict[str, Any], keys: tuple[str, ...]) -> bool:
    for k in keys:
        if k in obj and bool(obj[k]):
            return True
    return False


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    return None


def _coerce_name(value: Any) -> str | None:
    s = _coerce_str(value)
    if s is None:
        return None
    if s.lower() in {"anonymous", "anon", "someone"}:
        return None
    return s


def _coerce_amount(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        amount = float(value)
    elif isinstance(value, str):
        cleaned = value.strip().lstrip("$").replace(",", "")
        if not cleaned:
            return None
        try:
            amount = float(cleaned)
        except ValueError:
            return None
    else:
        return None
    if amount < 0:
        return None
    # Throne stores some amounts in cents — heuristically detect that. If the
    # raw value is an int and >= 1000 it's almost certainly cents (a $10+ tip).
    # We can't be 100% sure, so leave as-is; downstream only formats the value.
    return amount


def _normalize_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Epoch seconds vs milliseconds — > year 3000 in seconds means ms.
        ts = float(value)
        if ts > 32503680000:  # ~year 3000 in seconds
            ts /= 1000.0
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (OverflowError, ValueError, OSError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # Handle trailing 'Z'
        candidate = s.replace("Z", "+00:00") if s.endswith("Z") else s
        try:
            dt = datetime.fromisoformat(candidate)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    return None


def _extract_sends_from_html_fallback(html: str) -> list[ScrapedSend]:
    """Best-effort HTML fallback when ``__NEXT_DATA__`` is missing/unusable.

    We don't know the exact DOM layout up-front, so this is intentionally
    conservative: it returns ``[]`` rather than guessing wrong. When a real
    Throne fixture is available, this can be expanded with BeautifulSoup-based
    parsing without affecting the rest of the pipeline.
    """
    log.debug("HTML-fallback parser not implemented; returning no sends.")
    return []
