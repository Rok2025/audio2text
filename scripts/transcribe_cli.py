#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_config
from app.transcriber import AudioTranscriber


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe an audio file with local FunASR models.")
    parser.add_argument("audio", help="Audio file path, for example .m4a/.mp3/.wav.")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"), help="Config file path.")
    parser.add_argument("--threshold-ms", type=int, help="Pause threshold used for segmenting text.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    result = AudioTranscriber(config).transcribe_file(args.audio, threshold_ms=args.threshold_ms)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
