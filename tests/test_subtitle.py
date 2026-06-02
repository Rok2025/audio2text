import unittest

from app.subtitle import (
    enrich_segments,
    ensure_sentence_punctuation,
    punctuate_segments,
    render_punctuated_text,
    render_segments_text,
    render_srt,
    render_vtt,
)


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

    def test_adds_sentence_punctuation_when_missing(self) -> None:
        self.assertEqual(ensure_sentence_punctuation("测试文本"), "测试文本。")
        self.assertEqual(ensure_sentence_punctuation("测试文本。"), "测试文本。")

    def test_punctuates_segments_and_renders_text(self) -> None:
        segments = [
            {"index": 1, "start": "00:00.000", "end": "00:01.000", "text": "第一句"},
            {"index": 2, "start": "00:01.500", "end": "00:02.000", "text": "第二句"},
        ]

        punctuated = punctuate_segments(segments)

        self.assertEqual(render_punctuated_text(punctuated), "第一句。第二句。")
        self.assertEqual(
            render_segments_text(punctuated),
            "[00:00.000-00:01.000] 第一句。\n[00:01.500-00:02.000] 第二句。",
        )


if __name__ == "__main__":
    unittest.main()
