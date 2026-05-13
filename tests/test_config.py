import tempfile
import unittest
from pathlib import Path

from app.config import load_config


class ConfigTest(unittest.TestCase):
    def test_resolves_relative_paths_from_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.yaml"
            config_path.write_text(
                """
asr:
  model_path: ./models/paraformer-zh
  vad_model_path: ./models/fsmn-vad
  device: cpu
  batch_size_s: 60
  gap_threshold_ms: 700
storage:
  input_dir: ./storage/input
  wav_dir: ./storage/wav
  result_dir: ./storage/result
""",
                encoding="utf-8",
            )

            config = load_config(config_path)

            self.assertEqual(config.asr.model_path, (root / "models/paraformer-zh").resolve())
            self.assertEqual(config.asr.vad_model_path, (root / "models/fsmn-vad").resolve())
            self.assertEqual(config.asr.gap_threshold_ms, 700)
            self.assertEqual(config.storage.result_dir, (root / "storage/result").resolve())


if __name__ == "__main__":
    unittest.main()
