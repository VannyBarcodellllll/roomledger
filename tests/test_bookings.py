from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest

from roomledger.bookings import BookingConflict, BookingStore


def moment(value):
    return datetime.fromisoformat(value)


class BookingTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "test.db"
        self.store = BookingStore(self.path)
        self.room = self.store.add_room("Study Room A")

    def book(self, start="2026-09-30T10:00:00+07:00", end="2026-09-30T11:00:00+07:00", room=None):
        return self.store.book(self.room if room is None else room, "Vanny", moment(start), moment(end))

    def test_persists_and_normalizes_to_utc(self):
        booking = self.book()
        self.assertEqual(booking.starts_at, "2026-09-30T03:00:00.000000+00:00")
        self.assertEqual(BookingStore(self.path).list_bookings(), [booking])

    def test_rejects_every_overlap_shape(self):
        self.book()
        for start, end in [("09:30", "10:30"), ("10:30", "11:30"), ("10:15", "10:45"), ("09:00", "12:00"), ("10:00", "11:00")]:
            with self.subTest(start=start, end=end), self.assertRaises(BookingConflict):
                self.book(f"2026-09-30T{start}:00+07:00", f"2026-09-30T{end}:00+07:00")
        self.assertEqual(len(self.store.list_bookings()), 1)

    def test_adjacent_bookings_are_allowed(self):
        self.book()
        self.book("2026-09-30T09:00:00+07:00", "2026-09-30T10:00:00+07:00")
        self.book("2026-09-30T11:00:00+07:00", "2026-09-30T12:00:00+07:00")
        self.assertEqual(len(self.store.list_bookings()), 3)

    def test_same_instant_in_another_timezone_conflicts(self):
        self.book()
        with self.assertRaises(BookingConflict):
            self.book("2026-09-30T03:00:00Z", "2026-09-30T04:00:00Z")

    def test_other_rooms_remain_available(self):
        first = self.book()
        second_room = self.store.add_room("Study Room B")
        self.book(room=second_room)
        self.assertEqual(self.store.list_bookings(self.room), [first])

    def test_rejects_invalid_intervals(self):
        for start, end in [("10:00", "10:00"), ("11:00", "10:00")]:
            with self.subTest(start=start), self.assertRaises(ValueError):
                self.book(f"2026-09-30T{start}:00Z", f"2026-09-30T{end}:00Z")
        with self.assertRaises(ValueError):
            self.book("2026-09-30T10:00:00", "2026-09-30T11:00:00")
        self.assertEqual(self.store.list_bookings(), [])

    def test_rejects_missing_room_and_blank_names(self):
        with self.assertRaises(ValueError):
            self.book(room=999)
        with self.assertRaises(ValueError):
            self.store.add_room("  ")
        with self.assertRaises(ValueError):
            self.store.book(self.room, " ", moment("2026-09-30T10:00Z"), moment("2026-09-30T11:00Z"))
        self.assertEqual(self.store.list_bookings(), [])

    def test_only_one_simultaneous_request_wins(self):
        barrier = Barrier(2)

        def attempt():
            barrier.wait(timeout=5)
            try:
                self.book()
                return "booked"
            except BookingConflict:
                return "conflict"

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _: attempt(), range(2)))
        self.assertCountEqual(outcomes, ["booked", "conflict"])
        self.assertEqual(len(self.store.list_bookings()), 1)


if __name__ == "__main__":
    unittest.main()
