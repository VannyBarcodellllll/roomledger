"""Persistence and booking rules, independent of any web framework."""

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


class BookingConflict(ValueError):
    """The room is already booked for part of the requested interval."""


@dataclass(frozen=True)
class Booking:
    id: int
    room_id: int
    booked_by: str
    starts_at: str
    ends_at: str


def utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Use a timestamp with a time zone, such as +07:00 or Z.")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


class BookingStore:
    """Use a file-backed SQLite database; each operation owns its connection."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path == ":memory:":
            raise ValueError("Use a file path; operations use separate connections.")
        with closing(self._connect()) as connection, connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE CHECK(length(trim(name)) > 0)
                );
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY,
                    room_id INTEGER NOT NULL REFERENCES rooms(id),
                    booked_by TEXT NOT NULL CHECK(length(trim(booked_by)) > 0),
                    starts_at TEXT NOT NULL,
                    ends_at TEXT NOT NULL,
                    CHECK(starts_at < ends_at)
                );
                CREATE INDEX IF NOT EXISTS bookings_room_start
                    ON bookings(room_id, starts_at);
            """)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sqlite3.Row
        return connection

    def add_room(self, name: str) -> int:
        name = name.strip()
        if not name:
            raise ValueError("Room name must not be blank.")
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute("INSERT INTO rooms(name) VALUES (?)", (name,))
            return cursor.lastrowid

    def book(self, room_id: int, booked_by: str, start: datetime, end: datetime) -> Booking:
        start_text, end_text = utc_timestamp(start), utc_timestamp(end)
        if start_text >= end_text:
            raise ValueError("The end must be after the start.")
        booked_by = booked_by.strip()
        if not booked_by:
            raise ValueError("Booking name must not be blank.")
        with closing(self._connect()) as connection, connection:
            # Reserve the write lock before checking availability. Otherwise two
            # requests could both observe an empty room before either inserts.
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT id FROM rooms WHERE id = ?", (room_id,)).fetchone() is None:
                raise ValueError("Room does not exist.")
            conflict = connection.execute(
                "SELECT id FROM bookings WHERE room_id = ? AND starts_at < ? AND ends_at > ? LIMIT 1",
                (room_id, end_text, start_text),
            ).fetchone()
            if conflict:
                raise BookingConflict("This room is already booked during that time.")
            cursor = connection.execute(
                "INSERT INTO bookings(room_id, booked_by, starts_at, ends_at) VALUES (?, ?, ?, ?)",
                (room_id, booked_by, start_text, end_text),
            )
            return Booking(cursor.lastrowid, room_id, booked_by, start_text, end_text)

    def list_bookings(self, room_id: int | None = None) -> list[Booking]:
        query = "SELECT id, room_id, booked_by, starts_at, ends_at FROM bookings"
        parameters = ()
        if room_id is not None:
            query += " WHERE room_id = ?"
            parameters = (room_id,)
        query += " ORDER BY starts_at, id"
        with closing(self._connect()) as connection:
            return [Booking(**dict(row)) for row in connection.execute(query, parameters)]
