from __future__ import annotations

from typing import Any


def format_time(ms: int) -> str:
    total_seconds, millis = divmod(ms, 1000)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"
    return f"{minutes:02d}:{seconds:02d}.{millis:03d}"


def parse_tokens(text: str, timestamps: list[list[int]]) -> list[str]:
    spaced_tokens = text.split()
    if len(spaced_tokens) == len(timestamps):
        return spaced_tokens

    compact_tokens = list(text.replace(" ", ""))
    if len(compact_tokens) == len(timestamps):
        return compact_tokens

    raise ValueError(
        "Text token count does not match timestamp count: "
        f"space_split={len(spaced_tokens)}, compact={len(compact_tokens)}, timestamps={len(timestamps)}"
    )


def segment_tokens_by_gap(
    tokens: list[str],
    timestamps: list[list[int]],
    threshold_ms: int,
) -> list[dict[str, Any]]:
    if len(tokens) != len(timestamps):
        raise ValueError(f"tokens and timestamps length mismatch: {len(tokens)} != {len(timestamps)}")
    if not tokens:
        return []

    segments: list[dict[str, Any]] = []
    current_tokens = [tokens[0]]
    current_start = int(timestamps[0][0])
    gap_before = 0

    for index in range(1, len(tokens)):
        previous_end = int(timestamps[index - 1][1])
        current_start_ms = int(timestamps[index][0])
        gap = current_start_ms - previous_end

        if gap >= threshold_ms:
            segments.append(
                {
                    "startMs": current_start,
                    "endMs": previous_end,
                    "text": "".join(current_tokens),
                    "gapBeforeMs": gap_before,
                }
            )
            current_tokens = [tokens[index]]
            current_start = current_start_ms
            gap_before = gap
        else:
            current_tokens.append(tokens[index])

    segments.append(
        {
            "startMs": current_start,
            "endMs": int(timestamps[-1][1]),
            "text": "".join(current_tokens),
            "gapBeforeMs": gap_before,
        }
    )
    return segments


def segment_funasr_result(result: list[dict[str, Any]], threshold_ms: int) -> list[dict[str, Any]]:
    output = []
    for item in result:
        timestamps = item.get("timestamp") or []
        text = item.get("text") or ""
        if not timestamps:
            output.append({"key": item.get("key", ""), "segments": []})
            continue
        tokens = parse_tokens(text, timestamps)
        output.append(
            {
                "key": item.get("key", ""),
                "thresholdMs": threshold_ms,
                "segments": segment_tokens_by_gap(tokens, timestamps, threshold_ms),
            }
        )
    return output


def render_segments_text(segmented: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in segmented:
        for segment in item.get("segments", []):
            lines.append(
                f"[{format_time(segment['startMs'])}-{format_time(segment['endMs'])}] {segment['text']}"
            )
    return "\n".join(lines)
