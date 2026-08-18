#!/usr/bin/env python3
"""Reject repository paths that belong to a concrete mastering session."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_ROOTS = {"audio", "logs", "reports", "runs", "sessions", "tracks"}
AUDIO_SUFFIXES = {".aac", ".aif", ".aiff", ".flac", ".m4a", ".mp3", ".wav"}


def main() -> int:
    failures: list[str] = []
    for path in sorted(item for item in ROOT.rglob("*") if item.is_file()):
        rel = path.relative_to(ROOT)
        if ".git" in rel.parts or "__pycache__" in rel.parts:
            continue
        if rel.parts and rel.parts[0].lower() in FORBIDDEN_ROOTS:
            failures.append(f"forbidden session directory: {rel.as_posix()}")
        if path.suffix.lower() in AUDIO_SUFFIXES:
            failures.append(f"audio file in repository: {rel.as_posix()}")

    if failures:
        print("PROCESS_ONLY_SCOPE FAIL")
        for failure in failures:
            print(failure)
        return 2

    print("PROCESS_ONLY_SCOPE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

