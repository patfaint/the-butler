from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite


@dataclass(frozen=True)
class VerificationRequest:
    id: int
    user_id: int
    guild_id: int
    username: str
    verification_type: str | None
    verification_value: str | None
    selected_role: str | None
    status: str
    submitted_at: str
    reviewed_at: str | None
    reviewed_by: int | None
    log_message_id: int | None
    log_channel_id: int | None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "VerificationRequest":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            guild_id=row["guild_id"],
            username=row["username"],
            verification_type=row["verification_type"],
            verification_value=row["verification_value"],
            selected_role=row["selected_role"],
            status=row["status"],
            submitted_at=row["submitted_at"],
            reviewed_at=row["reviewed_at"],
            reviewed_by=row["reviewed_by"],
            log_message_id=row["log_message_id"],
            log_channel_id=row["log_channel_id"],
        )


@dataclass(frozen=True)
class DommeProfile:
    user_id: int
    name: str | None
    honorific: str | None
    pronouns: str | None
    age: str | None
    tribute_price: str | None
    throne: str | None
    paypal: str | None
    youpay: str | None
    cashapp: str | None
    venmo: str | None
    beemit: str | None
    loyalfans: str | None
    onlyfans: str | None
    throne_tracking_enabled: bool
    coffee_enabled: bool
    created_at: str

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "DommeProfile":
        return cls(
            user_id=row["user_id"],
            name=row["name"],
            honorific=row["honorific"],
            pronouns=row["pronouns"],
            age=row["age"],
            tribute_price=row["tribute_price"],
            throne=row["throne"],
            paypal=row["paypal"],
            youpay=row["youpay"],
            cashapp=row["cashapp"],
            venmo=row["venmo"],
            beemit=row["beemit"],
            loyalfans=row["loyalfans"],
            onlyfans=row["onlyfans"],
            throne_tracking_enabled=bool(row["throne_tracking_enabled"]),
            coffee_enabled=bool(row["coffee_enabled"]),
            created_at=row["created_at"],
        )


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._connection: aiosqlite.Connection | None = None

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("Database has not been initialized")
        return self._connection

    async def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.path)
        self._connection.row_factory = aiosqlite.Row
        await self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS verification_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                verification_type TEXT,
                verification_value TEXT,
                selected_role TEXT,
                status TEXT NOT NULL CHECK (
                    status IN (
                        'pending',
                        'approved',
                        'denied_underage',
                        'denied_invalid',
                        'expired'
                    )
                ),
                submitted_at TEXT NOT NULL,
                reviewed_at TEXT,
                reviewed_by INTEGER,
                log_message_id INTEGER,
                log_channel_id INTEGER
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_verification_one_pending
            ON verification_requests(user_id, guild_id)
            WHERE status = 'pending';

            CREATE INDEX IF NOT EXISTS idx_verification_user_guild
            ON verification_requests(user_id, guild_id);

            CREATE INDEX IF NOT EXISTS idx_verification_status
            ON verification_requests(status);

            CREATE TABLE IF NOT EXISTS domme_profiles (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                honorific TEXT,
                pronouns TEXT,
                age TEXT,
                tribute_price TEXT,
                throne TEXT,
                paypal TEXT,
                youpay TEXT,
                cashapp TEXT,
                venmo TEXT,
                beemit TEXT,
                loyalfans TEXT,
                onlyfans TEXT,
                throne_tracking_enabled INTEGER NOT NULL DEFAULT 0,
                coffee_enabled INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            UPDATE verification_requests
            SET reviewed_by = NULL
            WHERE status = 'pending';
            """
        )
        await self.connection.commit()

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def create_request(
        self,
        *,
        user_id: int,
        guild_id: int,
        username: str,
        verification_type: str | None,
        verification_value: str | None,
        selected_role: str | None,
        status: str = "pending",
    ) -> int:
        async with self.connection.execute(
            """
            INSERT INTO verification_requests (
                user_id,
                guild_id,
                username,
                verification_type,
                verification_value,
                selected_role,
                status,
                submitted_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                guild_id,
                username,
                verification_type,
                verification_value,
                selected_role,
                status,
                _utc_now(),
            ),
        ) as cursor:
            request_id = int(cursor.lastrowid)
        await self.connection.commit()
        return request_id

    async def set_log_message(
        self,
        *,
        request_id: int,
        log_message_id: int,
        log_channel_id: int,
    ) -> None:
        async with self.connection.execute(
            """
            UPDATE verification_requests
            SET log_message_id = ?, log_channel_id = ?
            WHERE id = ?
            """,
            (log_message_id, log_channel_id, request_id),
        ):
            pass
        await self.connection.commit()

    async def claim_pending_request(self, *, request_id: int, reviewed_by: int) -> bool:
        async with self.connection.execute(
            """
            UPDATE verification_requests
            SET reviewed_by = ?
            WHERE id = ?
            AND status = 'pending'
            AND reviewed_by IS NULL
            """,
            (reviewed_by, request_id),
        ) as cursor:
            claimed = cursor.rowcount > 0
        await self.connection.commit()
        return claimed

    async def release_request_claim(self, *, request_id: int, reviewed_by: int) -> None:
        async with self.connection.execute(
            """
            UPDATE verification_requests
            SET reviewed_by = NULL
            WHERE id = ?
            AND status = 'pending'
            AND reviewed_by = ?
            """,
            (request_id, reviewed_by),
        ):
            pass
        await self.connection.commit()

    async def get_request(self, request_id: int) -> VerificationRequest | None:
        return await self._fetch_one(
            "SELECT * FROM verification_requests WHERE id = ?",
            (request_id,),
        )

    async def get_pending_request(
        self,
        *,
        user_id: int,
        guild_id: int,
    ) -> VerificationRequest | None:
        return await self._fetch_one(
            """
            SELECT *
            FROM verification_requests
            WHERE user_id = ? AND guild_id = ? AND status = 'pending'
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, guild_id),
        )

    async def get_latest_request(
        self,
        *,
        user_id: int,
        guild_id: int,
    ) -> VerificationRequest | None:
        return await self._fetch_one(
            """
            SELECT *
            FROM verification_requests
            WHERE user_id = ? AND guild_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, guild_id),
        )

    async def get_pending_log_requests(self) -> list[VerificationRequest]:
        async with self.connection.execute(
            """
            SELECT *
            FROM verification_requests
            WHERE status = 'pending'
            AND log_message_id IS NOT NULL
            AND log_channel_id IS NOT NULL
            ORDER BY id ASC
            """
        ) as cursor:
            rows = await cursor.fetchall()
        return [VerificationRequest.from_row(row) for row in rows]

    async def mark_reviewed(
        self,
        *,
        request_id: int,
        status: str,
        reviewed_by: int | None,
    ) -> bool:
        async with self.connection.execute(
            """
            UPDATE verification_requests
            SET status = ?, reviewed_at = ?, reviewed_by = ?
            WHERE id = ?
            AND status = 'pending'
            AND (reviewed_by IS NULL OR reviewed_by = ?)
            """,
            (status, _utc_now(), reviewed_by, request_id, reviewed_by),
        ) as cursor:
            updated = cursor.rowcount > 0
        await self.connection.commit()
        return updated

    async def get_domme_profile(self, *, user_id: int) -> DommeProfile | None:
        async with self.connection.execute(
            "SELECT * FROM domme_profiles WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return DommeProfile.from_row(row)

    async def save_domme_profile(
        self,
        *,
        user_id: int,
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
    ) -> None:
        async with self.connection.execute(
            """
            INSERT INTO domme_profiles (
                user_id,
                name,
                honorific,
                pronouns,
                age,
                tribute_price,
                throne,
                paypal,
                youpay,
                cashapp,
                venmo,
                beemit,
                loyalfans,
                onlyfans,
                throne_tracking_enabled,
                coffee_enabled,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                honorific = excluded.honorific,
                pronouns = excluded.pronouns,
                age = excluded.age,
                tribute_price = excluded.tribute_price,
                throne = excluded.throne,
                paypal = excluded.paypal,
                youpay = excluded.youpay,
                cashapp = excluded.cashapp,
                venmo = excluded.venmo,
                beemit = excluded.beemit,
                loyalfans = excluded.loyalfans,
                onlyfans = excluded.onlyfans,
                throne_tracking_enabled = excluded.throne_tracking_enabled,
                coffee_enabled = excluded.coffee_enabled,
                created_at = domme_profiles.created_at
            """,
            (
                user_id,
                name,
                honorific,
                pronouns,
                age,
                tribute_price,
                throne,
                paypal,
                youpay,
                cashapp,
                venmo,
                beemit,
                loyalfans,
                onlyfans,
                int(throne_tracking_enabled),
                int(coffee_enabled),
                _utc_now(),
            ),
        ):
            pass
        await self.connection.commit()

    async def delete_domme_profile(self, *, user_id: int) -> bool:
        async with self.connection.execute(
            "DELETE FROM domme_profiles WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            deleted = cursor.rowcount > 0
        await self.connection.commit()
        return deleted

    async def _fetch_one(
        self,
        query: str,
        params: tuple[Any, ...],
    ) -> VerificationRequest | None:
        async with self.connection.execute(query, params) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return VerificationRequest.from_row(row)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
