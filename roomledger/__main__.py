"""A tiny CLI for exercising the first working milestone."""

import argparse
from dataclasses import asdict
from datetime import datetime
import json
import sqlite3

from .bookings import BookingStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Create rooms and reserve time without double-booking.")
    parser.add_argument("--db", default="roomledger.db", help="Path to the SQLite database")
    commands = parser.add_subparsers(dest="command", required=True)
    room = commands.add_parser("add-room")
    room.add_argument("name")
    book = commands.add_parser("book")
    book.add_argument("room_id", type=int)
    book.add_argument("name")
    book.add_argument("start", help="ISO timestamp with time zone")
    book.add_argument("end", help="ISO timestamp with time zone")
    listing = commands.add_parser("list")
    listing.add_argument("--room", type=int)
    args = parser.parse_args()
    try:
        store = BookingStore(args.db)
        if args.command == "add-room":
            result = {"room_id": store.add_room(args.name)}
        elif args.command == "book":
            result = asdict(store.book(args.room_id, args.name, datetime.fromisoformat(args.start), datetime.fromisoformat(args.end)))
        else:
            result = [asdict(booking) for booking in store.list_bookings(args.room)]
    except (ValueError, sqlite3.Error) as error:
        parser.exit(2, f"Error: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
