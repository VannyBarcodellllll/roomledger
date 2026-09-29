# Development log

## Day 1 — September 29, 2026

Implemented a Python booking engine, SQLite storage, and CLI. The core problem is preventing two users from reserving the same room for overlapping times.

Verification: all 8 automated tests passed. A separate CLI smoke check verified room creation, a successful booking, overlap rejection with exit status 2, and persistence across separate command invocations. These were local checks; hosted CI has not been configured yet.

### Your walkthrough

1. Create a room and a booking using the README commands.
2. Try a second overlapping booking and explain the error.
3. Try a booking that starts exactly when the first one ends.
4. Read the overlap condition and the transaction comment.

### Explain these in your own words

- Why does the overlap condition use two comparisons joined by AND?
- Why does checking availability before taking the write lock allow a race?
- Why normalize times before comparing them?

### Small exercise

Write a test showing that two bookings using different UTC offsets can still overlap, even when their displayed clock hours differ. Explain the expected UTC interval before running it.

Next milestone: cancellation with tests, plus refining requirements based on your current skills.
