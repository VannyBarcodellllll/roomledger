# RoomLedger

A room-booking project for small teams and study groups. The first milestone provides persistent bookings and prevents overlapping reservations, including when two requests arrive together.

**Status:** Day 1 prototype. A local Python library and command-line interface are implemented. The HTTP API, authentication, browser interface, and hosted demo are planned and are not available yet.

## Run it

Requires Python 3.11 or later. This milestone uses only the Python standard library; there are no third-party packages to install. Run these commands from the folder containing this README, starting with a fresh database:

```console
python -m roomledger add-room "Study Room A"
python -m roomledger book 1 Vanny 2026-09-30T10:00:00+07:00 2026-09-30T11:00:00+07:00
python -m roomledger list
```

Try an overlapping reservation. It should print an error and exit with status 2:

```console
python -m roomledger book 1 Alex 2026-09-30T10:30:00+07:00 2026-09-30T11:30:00+07:00
```

The examples assume the newly created room has ID 1. If using an existing database, use the ID printed by `add-room`. Pass `--db path/to/demo.db` before a command to choose another database. The parent directory must exist. Reusing a room name returns an error; it does not create a duplicate.

## Verify behavior

```console
python -m unittest discover -s tests -v
```

Tests cover persistent data, interval overlap, adjacent bookings, equivalent timestamps in different time zones, separate rooms, invalid input, and simultaneous requests.

## Design

`roomledger/bookings.py` contains the rules and SQLite persistence. `roomledger/__main__.py` provides a thin CLI. Each operation opens its own database connection.

Time intervals are half-open: `[start, end)`. Two bookings overlap when:

```text
existing.start < requested.end AND existing.end > requested.start
```

This allows a booking to start exactly when the preceding one ends. All input timestamps require explicit offsets and are normalized to a fixed-width UTC representation before storage or comparison.

`BEGIN IMMEDIATE` takes the SQLite write reservation before checking for a conflict. The check and insert occur in the same transaction. Other writers must wait before checking availability; errors roll the transaction back. This guarantee applies to writes through `BookingStore.book`, not arbitrary external SQL writers.

## Current limits and decisions

- Booking names are labels, not authenticated identities. This prototype is intended for local use.
- Past bookings are permitted so examples and historical imports remain reproducible.
- SQLite serializes writers and has a five-second lock timeout. The test demonstrates correctness for two simultaneous local requests, not production-scale throughput.
- No cancellation, capacity management, recurring bookings, migration system, or permission enforcement yet.
- The database must be file-backed. Keep it on a local filesystem.

## Development and learning

This portfolio project is being developed with Codex assistance. Features and claims should match verified behavior; the repository is not evidence of unaided authorship. See [progress](docs/progress.md) for what has actually been checked and the next learning exercise.

See the [project roadmap](docs/roadmap.md) for planned milestones.
