"""SQLAlchemy ORM models for The Butler bot."""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


# ── Guild-level configuration ─────────────────────────────────────────────────

class GuildConfig(Base):
    """Server-wide configuration set by admins via /set* commands."""

    __tablename__ = "guild_config"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    domme_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    sub_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    admin_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    jail_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    verified_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    unverified_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mod_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    welcome_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    leaderboard_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    verification_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mod_verify_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    vip_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    announcement_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)


# ── Domme profiles ────────────────────────────────────────────────────────────

class DommeProfile(Base):
    """Per-domme configuration, set during the /domsetup wizard."""

    __tablename__ = "domme_profiles"

    discord_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    throne_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tribute_links: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_coffee_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    time_scaling: Mapped[bool] = mapped_column(Boolean, default=False)
    day_scaling: Mapped[bool] = mapped_column(Boolean, default=False)
    drought_scaling: Mapped[bool] = mapped_column(Boolean, default=False)
    leaderboard_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    setup_complete: Mapped[bool] = mapped_column(Boolean, default=False)


# ── Sub profiles ──────────────────────────────────────────────────────────────

class SubProfile(Base):
    """Per-sub data tracked by the bot."""

    __tablename__ = "sub_profiles"

    discord_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    about: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_puppy_sub: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


# ── Tributes ──────────────────────────────────────────────────────────────────

class Tribute(Base):
    """Record of every tribute payment logged through the bot."""

    __tablename__ = "tributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    domme_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sub_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    tribute_type: Mapped[str] = mapped_column("type", String(20), nullable=False, default="tribute")  # coffee/tribute/gift
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


# ── Jail records ──────────────────────────────────────────────────────────────

class JailRecord(Base):
    """Tracks active and historical jail sentences."""

    __tablename__ = "jail_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    jailed_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    jailed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    release_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    released: Mapped[bool] = mapped_column(Boolean, default=False)
    _saved_roles: Mapped[Optional[str]] = mapped_column("saved_roles", Text, nullable=True)

    @property
    def saved_roles(self) -> list[int]:
        if self._saved_roles is None:
            return []
        return json.loads(self._saved_roles)

    @saved_roles.setter
    def saved_roles(self, value: list[int]) -> None:
        self._saved_roles = json.dumps(value)


# ── Expiring VIP roles ────────────────────────────────────────────────────────

class VIPRole(Base):
    """Tracks time-limited VIP roles assigned to members."""

    __tablename__ = "vip_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


# ── Tribute streaks ───────────────────────────────────────────────────────────

class TributeStreak(Base):
    """Gamification — tracks consecutive-day tribute streaks per sub/domme pair."""

    __tablename__ = "tribute_streaks"

    sub_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    domme_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_tribute_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
