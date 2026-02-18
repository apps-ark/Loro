"""I/O helpers for JSON and RTTM files."""

import json
from pathlib import Path


def write_json(data: dict | list, path: Path):
    """Write data to JSON file with pretty formatting."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_json(path: Path) -> dict | list:
    """Read JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_rttm(path: Path) -> list[dict]:
    """Parse an RTTM file into a list of speaker turn dicts.

    RTTM format (per line):
        SPEAKER <file_id> 1 <start> <duration> <NA> <NA> <speaker_id> <NA> <NA>

    Returns:
        List of dicts with keys: start, end, duration, speaker.
    """
    turns = []
    with open(path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 8 or parts[0] != "SPEAKER":
                continue
            start = float(parts[3])
            duration = float(parts[4])
            speaker = parts[7]
            turns.append({
                "start": round(start, 3),
                "end": round(start + duration, 3),
                "duration": round(duration, 3),
                "speaker": speaker,
            })
    return turns
