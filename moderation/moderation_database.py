from __future__ import annotations

import asyncio
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class CaseRecord:
    id: int
    guild_id: int
    action_type: str
    target_id: int
    moderator_id: int
    reason: str
    created_at: str
    expires_at: str | None
    active: bool

    @property
    def case_id(self) -> str:
        return f"CASE-{self.id:04d}"


@dataclass(slots=True)
class WarningRecord:
    id: int
    case_id: int
    guild_id: int
    user_id: int
    moderator_id: int
    reason: str
    created_at: str
    active: bool

    @property
    def warning_id(self) -> str:
        return f"HC-WARN-{self.id:04d}"


@dataclass(slots=True)
class NoteRecord:
    id: int
    guild_id: int
    user_id: int
    moderator_id: int
    note: str
    created_at: str


class ModerationDatabase:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._setup()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def _setup(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    target_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    active INTEGER NOT NULL DEFAULT 1
                );
                CREATE INDEX IF NOT EXISTS idx_cases_guild_target ON cases(guild_id, target_id);
                CREATE INDEX IF NOT EXISTS idx_cases_action ON cases(action_type, active);

                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                );
                CREATE INDEX IF NOT EXISTS idx_warnings_guild_user ON warnings(guild_id, user_id, active);

                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_notes_guild_user ON notes(guild_id, user_id);

                CREATE TABLE IF NOT EXISTS settings (
                    guild_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY (guild_id, key)
                );
                """
            )

    async def _run(self, func, *args):
        return await asyncio.to_thread(func, *args)

    @staticmethod
    def _case(row: sqlite3.Row) -> CaseRecord:
        return CaseRecord(
            id=row["id"],
            guild_id=row["guild_id"],
            action_type=row["action_type"],
            target_id=row["target_id"],
            moderator_id=row["moderator_id"],
            reason=row["reason"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            active=bool(row["active"]),
        )

    @staticmethod
    def _warning(row: sqlite3.Row) -> WarningRecord:
        return WarningRecord(
            id=row["id"],
            case_id=row["case_id"],
            guild_id=row["guild_id"],
            user_id=row["user_id"],
            moderator_id=row["moderator_id"],
            reason=row["reason"],
            created_at=row["created_at"],
            active=bool(row["active"]),
        )

    @staticmethod
    def _note(row: sqlite3.Row) -> NoteRecord:
        return NoteRecord(
            id=row["id"],
            guild_id=row["guild_id"],
            user_id=row["user_id"],
            moderator_id=row["moderator_id"],
            note=row["note"],
            created_at=row["created_at"],
        )

    async def create_case(
        self,
        *,
        guild_id: int,
        action_type: str,
        target_id: int,
        moderator_id: int,
        reason: str,
        expires_at: str | None = None,
    ) -> CaseRecord:
        def op() -> CaseRecord:
            with self._connect() as db:
                cur = db.execute(
                    """
                    INSERT INTO cases (guild_id, action_type, target_id, moderator_id, reason, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (guild_id, action_type.upper(), target_id, moderator_id, reason, utc_now_iso(), expires_at),
                )
                row = db.execute("SELECT * FROM cases WHERE id = ?", (cur.lastrowid,)).fetchone()
                return self._case(row)

        return await self._run(op)

    async def close_case(self, case_id: int) -> None:
        def op() -> None:
            with self._connect() as db:
                db.execute("UPDATE cases SET active = 0 WHERE id = ?", (case_id,))

        await self._run(op)

    async def get_case(self, case_id: int) -> CaseRecord | None:
        def op() -> CaseRecord | None:
            with self._connect() as db:
                row = db.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
                return self._case(row) if row else None

        return await self._run(op)

    async def list_cases(self, guild_id: int, target_id: int | None = None, limit: int = 10) -> list[CaseRecord]:
        def op() -> list[CaseRecord]:
            with self._connect() as db:
                if target_id is None:
                    rows = db.execute(
                        "SELECT * FROM cases WHERE guild_id = ? ORDER BY id DESC LIMIT ?",
                        (guild_id, limit),
                    ).fetchall()
                else:
                    rows = db.execute(
                        "SELECT * FROM cases WHERE guild_id = ? AND target_id = ? ORDER BY id DESC LIMIT ?",
                        (guild_id, target_id, limit),
                    ).fetchall()
                return [self._case(row) for row in rows]

        return await self._run(op)

    async def active_tempbans_due(self, before_iso: str) -> list[CaseRecord]:
        def op() -> list[CaseRecord]:
            with self._connect() as db:
                rows = db.execute(
                    """
                    SELECT * FROM cases
                    WHERE action_type = 'TEMPBAN' AND active = 1 AND expires_at IS NOT NULL AND expires_at <= ?
                    ORDER BY expires_at ASC
                    """,
                    (before_iso,),
                ).fetchall()
                return [self._case(row) for row in rows]

        return await self._run(op)

    async def add_warning(self, *, case_id: int, guild_id: int, user_id: int, moderator_id: int, reason: str) -> WarningRecord:
        def op() -> WarningRecord:
            with self._connect() as db:
                cur = db.execute(
                    """
                    INSERT INTO warnings (case_id, guild_id, user_id, moderator_id, reason, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (case_id, guild_id, user_id, moderator_id, reason, utc_now_iso()),
                )
                row = db.execute("SELECT * FROM warnings WHERE id = ?", (cur.lastrowid,)).fetchone()
                return self._warning(row)

        return await self._run(op)

    async def list_warnings(self, guild_id: int, user_id: int, active_only: bool = True) -> list[WarningRecord]:
        def op() -> list[WarningRecord]:
            with self._connect() as db:
                if active_only:
                    rows = db.execute(
                        "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? AND active = 1 ORDER BY id DESC",
                        (guild_id, user_id),
                    ).fetchall()
                else:
                    rows = db.execute(
                        "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY id DESC",
                        (guild_id, user_id),
                    ).fetchall()
                return [self._warning(row) for row in rows]

        return await self._run(op)

    async def remove_warning(self, warning_id: int) -> WarningRecord | None:
        def op() -> WarningRecord | None:
            with self._connect() as db:
                row = db.execute("SELECT * FROM warnings WHERE id = ?", (warning_id,)).fetchone()
                if not row:
                    return None
                db.execute("UPDATE warnings SET active = 0 WHERE id = ?", (warning_id,))
                return self._warning(row)

        return await self._run(op)

    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        def op() -> int:
            with self._connect() as db:
                cur = db.execute(
                    "UPDATE warnings SET active = 0 WHERE guild_id = ? AND user_id = ? AND active = 1",
                    (guild_id, user_id),
                )
                return cur.rowcount

        return await self._run(op)

    async def add_note(self, *, guild_id: int, user_id: int, moderator_id: int, note: str) -> NoteRecord:
        def op() -> NoteRecord:
            with self._connect() as db:
                cur = db.execute(
                    "INSERT INTO notes (guild_id, user_id, moderator_id, note, created_at) VALUES (?, ?, ?, ?, ?)",
                    (guild_id, user_id, moderator_id, note, utc_now_iso()),
                )
                row = db.execute("SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)).fetchone()
                return self._note(row)

        return await self._run(op)

    async def list_notes(self, guild_id: int, user_id: int) -> list[NoteRecord]:
        def op() -> list[NoteRecord]:
            with self._connect() as db:
                rows = db.execute(
                    "SELECT * FROM notes WHERE guild_id = ? AND user_id = ? ORDER BY id DESC",
                    (guild_id, user_id),
                ).fetchall()
                return [self._note(row) for row in rows]

        return await self._run(op)

    async def stats(self, guild_id: int) -> dict[str, Any]:
        def op() -> dict[str, Any]:
            with self._connect() as db:
                counts = {
                    row["action_type"]: row["total"]
                    for row in db.execute(
                        "SELECT action_type, COUNT(*) total FROM cases WHERE guild_id = ? GROUP BY action_type",
                        (guild_id,),
                    ).fetchall()
                }
                mods = db.execute(
                    """
                    SELECT moderator_id, COUNT(*) total FROM cases
                    WHERE guild_id = ?
                    GROUP BY moderator_id
                    ORDER BY total DESC
                    LIMIT 5
                    """,
                    (guild_id,),
                ).fetchall()
                recent = db.execute(
                    "SELECT * FROM cases WHERE guild_id = ? ORDER BY id DESC LIMIT 5",
                    (guild_id,),
                ).fetchall()
                return {
                    "counts": counts,
                    "moderators": [(row["moderator_id"], row["total"]) for row in mods],
                    "recent": [self._case(row) for row in recent],
                }

        return await self._run(op)

    async def get_setting(self, guild_id: int, key: str) -> str | None:
        def op() -> str | None:
            with self._connect() as db:
                row = db.execute(
                    "SELECT value FROM settings WHERE guild_id = ? AND key = ?",
                    (guild_id, key),
                ).fetchone()
                return row["value"] if row else None

        return await self._run(op)

    async def set_setting(self, guild_id: int, key: str, value: str) -> None:
        def op() -> None:
            with self._connect() as db:
                db.execute(
                    "INSERT OR REPLACE INTO settings (guild_id, key, value) VALUES (?, ?, ?)",
                    (guild_id, key, value),
                )

        await self._run(op)