#!/usr/bin/env python3
"""Create a repeatable stage folder for OZONE12_MASTERING_LAB."""
from __future__ import annotations

import argparse
from pathlib import Path

from oz12_common import ensure_dir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--base-wav", default="")
    ap.add_argument("--base-xml", default="")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    root = Path(args.root)
    stage_dir = root / "stages" / args.stage
    for sub in ["presets", "renders", "reports", "input_refs"]:
        ensure_dir(stage_dir / sub)

    commands = f"""# {args.stage} — RUN COMMANDS

## Notes

{args.notes or 'TBD'}

## Base references

```text
base_wav = {args.base_wav or 'TBD'}
base_xml = {args.base_xml or 'TBD'}
```

## 1. Put XML presets here

```text
{stage_dir / 'presets'}
```

## 2. Render WAV files here

```text
{stage_dir / 'renders'}
```

Render settings:

```text
WAV / 48 kHz / 24-bit / Normalize Off / no FX before-after Ozone
```

## 3. Analyze WAV renders

```bash
python tools/stage_toolkit/oz12_analyze_stage.py \\
  --stage {args.stage} \\
  --base "{args.base_wav or 'PATH_TO_BASE.wav'}" \\
  --renders "{stage_dir / 'renders' / 'CANDIDATE_A.wav'}" "{stage_dir / 'renders' / 'CANDIDATE_B.wav'}" \\
  --outdir "{stage_dir / 'reports'}"
```

## 4. Run automatic drum/mono meter

```bash
python tools/stage_toolkit/oz12_mastering_meter.py \\
  --reference "{args.base_wav or 'PATH_TO_BASE.wav'}" \\
  --candidate "{stage_dir / 'renders' / 'CANDIDATE_A.wav'}" \\
  --outdir "{stage_dir / 'reports' / 'mastering_meter'}" \\
  --skip-codecs
```

Remove `--skip-codecs` only for the native final/codec stage. Add
`--decoded-peak-target-dbtp` only when the delivery target is declared.

## 5. Audit XML presets

```bash
python tools/stage_toolkit/oz12_xml_audit.py \\
  --base-xml "{args.base_xml or 'PATH_TO_BASE.xml'}" \\
  --xmls "{stage_dir / 'presets' / 'CANDIDATE_A.xml'}" "{stage_dir / 'presets' / 'CANDIDATE_B.xml'}" \\
  --outdir "{stage_dir / 'reports' / 'xml_audit'}"
```
"""
    (stage_dir / "RUN_COMMANDS.md").write_text(commands, encoding="utf-8")
    print(f"OK: created {stage_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
