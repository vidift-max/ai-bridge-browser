import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from server.presence_service import PresenceService
from server.sqlite_store import SQLiteMessengerStore


class PresenceConcurrencyTest(unittest.TestCase):
    def test_parallel_heartbeats_leave_one_complete_snapshot(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as tmp:
            store = SQLiteMessengerStore(tmp.name)
            try:
                service = PresenceService(store._connection)
                rooms = [f"room-{index}" for index in range(12)]

                def beat(room):
                    return service.heartbeat("AI-A", [room], rooms, now=1000)

                with ThreadPoolExecutor(max_workers=12) as pool:
                    results = list(pool.map(beat, rooms))

                self.assertEqual(len(results), 12)
                final = service.list_room(rooms[-1], ["AI-A"], now=1000)
                active_rooms = [
                    room for room in rooms
                    if service.list_room(room, ["AI-A"], now=1000)[0]["activeInRoom"]
                ]
                self.assertEqual(len(active_rooms), 1)
                self.assertEqual(final[0]["status"], "ONLINE")
            finally:
                store.close()

    def test_rejected_heartbeat_does_not_overwrite_previous_state(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as tmp:
            store = SQLiteMessengerStore(tmp.name)
            try:
                service = PresenceService(store._connection)
                service.heartbeat("AI-A", ["room-1"], ["room-1"], now=1000)
                with self.assertRaises(PermissionError):
                    service.heartbeat("AI-A", ["room-secret"], ["room-1"], now=1010)
                row = service.list_room("room-1", ["AI-A"], now=1010)[0]
                self.assertEqual(row["status"], "ONLINE")
                self.assertTrue(row["activeInRoom"])
                self.assertEqual(row["lastSeenAt"], 1000)
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
