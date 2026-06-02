import unittest

from app.media import (
    AUDIO_UPLOAD_LIMIT_BYTES,
    VIDEO_UPLOAD_LIMIT_BYTES,
    detect_media_type,
    suffix_for,
    upload_limit_bytes,
)


class MediaTest(unittest.TestCase):
    def test_detects_audio_by_suffix(self) -> None:
        self.assertEqual(detect_media_type("sample.M4A"), "audio")

    def test_detects_video_by_suffix(self) -> None:
        self.assertEqual(detect_media_type("sample.MP4"), "video")

    def test_rejects_unknown_suffix(self) -> None:
        with self.assertRaises(ValueError):
            detect_media_type("sample.txt")

    def test_returns_lowercase_suffix(self) -> None:
        self.assertEqual(suffix_for("sample.MOV"), ".mov")

    def test_uses_larger_upload_limit_for_video(self) -> None:
        self.assertEqual(upload_limit_bytes("audio"), AUDIO_UPLOAD_LIMIT_BYTES)
        self.assertEqual(upload_limit_bytes("video"), VIDEO_UPLOAD_LIMIT_BYTES)


if __name__ == "__main__":
    unittest.main()
