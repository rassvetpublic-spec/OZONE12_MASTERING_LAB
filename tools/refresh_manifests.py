#!/usr/bin/env python3
"""Regenerate or verify deterministic package manifests."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.csv"
MANIFEST_SHA = ROOT / "MANIFEST_SHA256.csv"
FILE_AUDIT = ROOT / "validation" / "FILE_AUDIT.csv"
CONTROL_PATHS = {"MANIFEST.csv", "MANIFEST_SHA256.csv", "validation/FILE_AUDIT.csv"}


def role(path: str) -> str:
    if path in {".gitattributes", ".gitignore", "README.md", "requirements-analysis.txt"} or path.startswith(("checklists/", "migration/", "prompts/", "templates/", "snippets/")):
        return "support"
    if path.startswith(".github/"):
        return "repository automation"
    if path.startswith("dist/"):
        return "release/source bundle"
    if path.startswith("docs/"):
        return "priority rule document"
    if path.startswith("profiles/"):
        return "optional mastering profile"
    if path.startswith("skills/"):
        return "priority reusable skill/data"
    if path.startswith("source_consolidated/"):
        return "archival consolidated old source"
    if path.startswith("tables/"):
        return "priority reference table"
    if path.startswith("tools/"):
        return "tool/script/schema"
    if path.startswith("validation/"):
        return "validation/audit"
    raise ValueError(f"No manifest role for {path}")


def csv_text(header: list[str], rows: list[list[object]]) -> str:
    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


def base_files() -> list[tuple[str, bytes]]:
    out = []
    for file in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        rel = file.relative_to(ROOT).as_posix()
        if rel in CONTROL_PATHS:
            continue
        if ".git" in file.parts or "__pycache__" in file.parts or file.suffix in {".pyc", ".pyo"}:
            continue
        out.append((rel, file.read_bytes()))
    return out


def expected() -> tuple[str, str, str]:
    files = base_files()
    audit_rows = [[path, len(data), hashlib.sha256(data).hexdigest(), role(path)] for path, data in files]
    audit = csv_text(["path", "bytes", "sha256", "role"], audit_rows)

    manifest_files = files + [("validation/FILE_AUDIT.csv", audit.encode("utf-8"))]
    manifest_files.sort(key=lambda item: item[0])
    plain_rows = [[path, len(data), role(path)] for path, data in manifest_files]
    hash_rows = [[path, len(data), hashlib.sha256(data).hexdigest(), role(path)] for path, data in manifest_files]
    plain = csv_text(["path", "bytes", "role"], plain_rows)
    hashed = csv_text(["path", "bytes", "sha256", "role"], hash_rows)
    return plain, hashed, audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write refreshed manifests")
    args = parser.parse_args()
    plain, hashed, audit = expected()
    if args.write:
        MANIFEST.write_text(plain, encoding="utf-8", newline="")
        MANIFEST_SHA.write_text(hashed, encoding="utf-8", newline="")
        FILE_AUDIT.write_text(audit, encoding="utf-8", newline="")
        print("WROTE", len(plain.splitlines()) - 1, "manifest entries")
        return 0

    expected_by_path = {MANIFEST: plain, MANIFEST_SHA: hashed, FILE_AUDIT: audit}
    failures = []
    for path, wanted in expected_by_path.items():
        current = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        if current != wanted:
            failures.append(path.relative_to(ROOT).as_posix())
    if failures:
        print("FAIL", ", ".join(failures))
        return 2
    print("PASS", len(plain.splitlines()) - 1, "manifest entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
