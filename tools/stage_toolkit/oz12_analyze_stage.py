#!/usr/bin/env python3
"""Analyze WAV renders for an OZONE12_MASTERING_LAB stage.

Outputs: metrics.csv, sample_identity.csv, band_deltas.csv, mid_side_deltas.csv, decision_draft.md
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

from oz12_common import (
    bands_rms_db, compare_sample_identity, ensure_dir, fast_loudness,
    ffprobe_info, load_audio, peak_db, rms_db, stereo_stats, write_csv,
)

BANDS: List[Tuple[str, Tuple[float, float]]] = [
    ("sub_20_40", (20, 40)),
    ("low_40_80", (40, 80)),
    ("bass_80_140", (80, 140)),
    ("low_mid_140_250", (140, 250)),
    ("mud_250_500", (250, 500)),
    ("mid_500_1000", (500, 1000)),
    ("presence_1k_4k", (1000, 4000)),
    ("harsh_4k_8k", (4000, 8000)),
    ("sparkle_8k_12k", (8000, 12000)),
    ("air_12k_18k", (12000, 18000)),
]


def analyze_one(path: Path) -> Dict[str, object]:
    sr, audio, backend = load_audio(path)
    dur = audio.shape[0] / sr if sr else 0
    info = ffprobe_info(path)
    loud = fast_loudness(audio, sr)
    st = stereo_stats(audio)
    row: Dict[str, object] = {
        "file": path.name,
        "path": str(path),
        "sample_rate": sr,
        "channels": audio.shape[1] if audio.ndim == 2 else 1,
        "duration_sec": round(dur, 3),
        "load_backend": backend,
        "sample_peak_dbfs": round(peak_db(audio), 3),
        "rms_dbfs": round(rms_db(audio), 3),
        "crest_db": round(peak_db(audio) - rms_db(audio), 3),
    }
    for k in ["codec_name", "bits_per_sample", "format_name", "bit_rate"]:
        if k in info:
            row[k] = info[k]
    for k, v in loud.items():
        row[k] = round(v, 3) if isinstance(v, float) else v
    for k, v in st.items():
        row[k] = round(v, 6) if isinstance(v, float) else v
    band_levels = bands_rms_db(audio, sr, BANDS)
    for name, value in band_levels.items():
        row[f"band_{name}_dbfs"] = round(value, 3)
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, help="Stage name, e.g. width_stage_v14")
    ap.add_argument("--base", required=True, help="Base/reference WAV")
    ap.add_argument("--renders", nargs="+", required=True, help="Candidate WAV renders")
    ap.add_argument("--outdir", required=True, help="Output reports directory")
    args = ap.parse_args()

    outdir = ensure_dir(args.outdir)
    base = Path(args.base)
    renders = [Path(p) for p in args.renders]
    all_files = [base] + renders

    missing = [str(p) for p in all_files if not p.exists()]
    if missing:
        raise SystemExit("Missing files:\n" + "\n".join(missing))

    metrics = [analyze_one(p) for p in all_files]
    write_csv(outdir / "metrics.csv", metrics)

    base_sr, base_audio, _ = load_audio(base)
    identity_rows = []
    band_rows = []
    ms_rows = []
    base_metric = metrics[0]
    for p, m in zip(all_files[1:], metrics[1:]):
        sr, audio, _ = load_audio(p)
        ident = compare_sample_identity(base_audio, audio)
        ident.update({"stage": args.stage, "base": base.name, "candidate": p.name})
        identity_rows.append(ident)
        brow = {"stage": args.stage, "base": base.name, "candidate": p.name}
        for band_name, _ in BANDS:
            key = f"band_{band_name}_dbfs"
            bv = base_metric.get(key)
            cv = m.get(key)
            try:
                brow[f"delta_{band_name}_db"] = round(float(cv) - float(bv), 3)  # type: ignore[arg-type]
            except Exception:
                brow[f"delta_{band_name}_db"] = None
        band_rows.append(brow)
        msrow = {"stage": args.stage, "base": base.name, "candidate": p.name}
        for key in ["corr", "mid_rms_db", "side_rms_db", "side_minus_mid_db", "lufs_i", "true_peak_dbfs"]:
            try:
                msrow[f"delta_{key}"] = round(float(m.get(key)) - float(base_metric.get(key)), 6)  # type: ignore[arg-type]
            except Exception:
                msrow[f"delta_{key}"] = None
        ms_rows.append(msrow)

    write_csv(outdir / "sample_identity.csv", identity_rows)
    write_csv(outdir / "band_deltas.csv", band_rows)
    write_csv(outdir / "mid_side_deltas.csv", ms_rows)

    md = []
    md.append(f"# {args.stage} — decision draft\n")
    md.append("## Files\n")
    md.append(f"Base: `{base.name}`\n")
    for p in renders:
        md.append(f"Candidate: `{p.name}`\n")
    md.append("\n## Quick metrics\n\n")
    md.append("| File | LUFS-I | True Peak | Peak | Corr | Side/Mid | Crest |\n")
    md.append("|---|---:|---:|---:|---:|---:|---:|\n")
    for row in metrics:
        md.append(
            f"| `{row.get('file')}` | {row.get('lufs_i')} | {row.get('true_peak_dbfs')} | {row.get('sample_peak_dbfs')} | {row.get('corr')} | {row.get('side_minus_mid_db')} | {row.get('crest_db')} |\n"
        )
    md.append("\n## Sample identity check\n\n")
    md.append("| Candidate | sample_identical | max_abs_diff | rms_diff_dbfs | null_residual_vs_ref_db |\n")
    md.append("|---|---:|---:|---:|---:|\n")
    for row in identity_rows:
        md.append(f"| `{row['candidate']}` | {row['sample_identical']} | {row['max_abs_diff']} | {row['rms_diff_dbfs']} | {row['null_residual_vs_ref_db']} |\n")
    md.append("\n## Decision checklist\n\n")
    md.append("- [ ] Reject non-control renders if `sample_identical=True`.\n")
    md.append("- [ ] Check low-end deltas: 40–140 Hz must not collapse.\n")
    md.append("- [ ] Check 4–12 kHz harshness does not worsen.\n")
    md.append("- [ ] Check correlation/Side-Mid does not become unsafe.\n")
    md.append("- [ ] Pick winner by sound + metrics, not LUFS only.\n")
    md.append("\n## Verdict\n\n```text\nWINNER = TBD\nFALLBACK = TBD\nNEXT_STAGE_BASE = TBD\n```\n")
    (outdir / "decision_draft.md").write_text("".join(md), encoding="utf-8")

    print(f"OK: wrote reports to {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
