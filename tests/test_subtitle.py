import unittest

from app.subtitle import enrich_segments, render_srt, render_vtt


class SubtitleTest(unittest.TestCase):
    def test_enriches_segments_with_index_and_display_times(self) -> None:
        segments = [{"startMs": 550, "endMs": 3335, "text": "测试", "gapBeforeMs": 0}]

        self.assertEqual(
            enrich_segments(segments),
            [
                {
                    "index": 1,
                    "startMs": 550,
                    "endMs": 3335,
                    "start": "00:00.550",
                    "end": "00:03.335",
                    "text": "测试",
                    "gapBeforeMs": 0,
                }
            ],
        )

    def test_renders_srt(self) -> None:
        segments = [{"startMs": 550, "endMs": 3335, "text": "测试"}]

        self.assertEqual(render_srt(segments), "1\n00:00,550 --> 00:03,335\n测试")

    def test_renders_vtt(self) -> None:
        segments = [{"startMs": 550, "endMs": 3335, "text": "测试"}]

        self.assertEqual(render_vtt(segments), "WEBVTT\n\n00:00.550 --> 00:03.335\n测试")


if __name__ == "__main__":
    unittest.main()
