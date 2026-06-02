from __future__ import annotations

from typing import Any

from app.segment_by_gap import format_time


def format_srt_time(ms: int) -> str:
    return format_time(ms).replace(".", ",")


def render_srt(segments: list[dict[str, Any]]) -> str:
    blocks = []
    for index, segment in enumerate(segments, start=1):
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{format_srt_time(segment['startMs'])} --> {format_srt_time(segment['endMs'])}",
                    str(segment.get("text", "")),
                ]
            )
        )
    return "\n\n".join(blocks)


def render_vtt(segments: list[dict[str, Any]]) -> str:
    blocks = ["WEBVTT"]
    for segment in segments:
        blocks.append(
            "\n".join(
                [
                    f"{format_time(segment['startMs'])} --> {format_time(segment['endMs'])}",
                    str(segment.get("text", "")),
                ]
            )
        )
    return "\n\n".join(blocks)


def enrich_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for index, segment in enumerate(segments, start=1):
        enriched.append(
            {
                "index": index,
                "startMs": segment["startMs"],
                "endMs": segment["endMs"],
                "start": format_time(segment["startMs"]),
                "end": format_time(segment["endMs"]),
                "text": segment.get("text", ""),
                "gapBeforeMs": segment.get("gapBeforeMs", 0),
            }
        )
    return enriched
