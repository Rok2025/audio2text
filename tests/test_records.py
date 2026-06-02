import tempfile
import unittest
from pathlib import Path

from app.records import RecordStore, build_record


class RecordStoreTest(unittest.TestCase):
    def test_appends_and_lists_records_newest_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = RecordStore(Path(tmp))

            store.append({"taskId": "one", "status": "success"})
            store.append({"taskId": "two", "status": "failed"})

            records = store.list(limit=2)

            self.assertEqual([record["taskId"] for record in records], ["two", "one"])

    def test_finds_records_by_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = RecordStore(Path(tmp))

            store.append({"taskId": "abc", "status": "queued"})
            store.append({"taskId": "abc", "status": "success"})
            store.append({"taskId": "other", "status": "success"})

            records = store.find_by_task_id("abc")

            self.assertEqual(len(records), 2)
            self.assertTrue(all(record["taskId"] == "abc" for record in records))

    def test_build_record_summarizes_result(self) -> None:
        record = build_record(
            task_id="abc",
            mode="sync",
            status="success",
            started_at="2026-06-02T00:00:00+00:00",
            finished_at="2026-06-02T00:00:01+00:00",
            result={
                "source": {"filename": "a.mp4", "mediaType": "video", "durationMs": 1000},
                "text": "测试文本",
                "segments": [{"text": "测试"}],
                "files": {"srt": "/tmp/a.srt"},
            },
        )

        self.assertEqual(record["filename"], "a.mp4")
        self.assertEqual(record["mediaType"], "video")
        self.assertEqual(record["textLength"], 4)
        self.assertEqual(record["segmentCount"], 1)
        self.assertEqual(record["elapsedMs"], 1000)


if __name__ == "__main__":
    unittest.main()
