import unittest

from app.segment_by_gap import parse_tokens, segment_tokens_by_gap


class SegmentByGapTest(unittest.TestCase):
    def test_splits_text_when_pause_reaches_threshold(self) -> None:
        tokens = ["这", "是", "测", "试"]
        timestamps = [[0, 100], [100, 200], [850, 1000], [1000, 1200]]

        segments = segment_tokens_by_gap(tokens, timestamps, threshold_ms=600)

        self.assertEqual(
            segments,
            [
                {"startMs": 0, "endMs": 200, "text": "这是", "gapBeforeMs": 0},
                {"startMs": 850, "endMs": 1200, "text": "测试", "gapBeforeMs": 650},
            ],
        )

    def test_parses_spaced_funasr_text_by_timestamp_count(self) -> None:
        tokens = parse_tokens("这 是 测 试", [[0, 100], [100, 200], [200, 300], [300, 400]])

        self.assertEqual(tokens, ["这", "是", "测", "试"])


if __name__ == "__main__":
    unittest.main()
