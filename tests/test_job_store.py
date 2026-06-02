import tempfile
import unittest
from pathlib import Path

from app.job_store import JobStore


class JobStoreTest(unittest.TestCase):
    def test_creates_updates_reads_and_deletes_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp))

            store.create("abc", {"source": {"filename": "a.m4a"}})
            updated = store.update("abc", status="success", result={"text": "ok"})

            self.assertEqual(updated["status"], "success")
            self.assertEqual(store.read("abc")["result"]["text"], "ok")
            self.assertTrue(store.delete("abc"))
            self.assertIsNone(store.read("abc"))

    def test_rejects_path_like_task_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp))

            with self.assertRaises(ValueError):
                store.read("../bad")


if __name__ == "__main__":
    unittest.main()
