# Project roadmap

RoomLedger is being built in small, verified increments. This document separates implemented behavior from future goals.

## Implemented

- File-backed SQLite storage for rooms and bookings.
- Time-zone-aware timestamps normalized to UTC.
- Overlap detection with adjacent bookings allowed.
- A transaction covering the availability check and booking insert.
- A command-line interface and eight automated tests.

## Next: complete the booking model

- Cancellation and its effect on availability.
- Room capacity and management.
- Clear rules for who may create, view, and cancel bookings.
- An HTTP API with validation, predictable errors, filtering, and pagination.
- A documented database migration process.

## Then: a usable application

- Authentication and booking ownership checks.
- Room availability and booking screens.
- Clear conflict feedback, accessible controls, and responsive layouts.
- A reproducible demo using fictional sample data.

## Reliability and release

- Audit history, useful logs, and health checks.
- Automated CI checks.
- Measured concurrency and query performance with stated limits.
- Verified backup and restore instructions.
- Setup documentation, architecture notes, and a walkthrough.

Each milestone is complete only when its behavior is verified and its limitations are recorded. The initial SQLite implementation is intended for a small local deployment; scaling decisions should follow measured needs.
