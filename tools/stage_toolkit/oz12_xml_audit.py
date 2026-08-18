#!/usr/bin/env python3
"""Audit Ozone 12 XML presets: ElementChain and Param diffs."""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

from oz12_common import decode_element_chain, ensure_dir, write_csv


def parse_xml(path: Path) -> ET.ElementTree:
    return ET.parse(str(path))


def get_element_chain(root: ET.Element) -> List[str]:
    for eb in root.findall(".//ExtraBytes"):
        if eb.attrib.get("ElementID") == "ElementChain":
            data = eb.attrib.get("Data", "")
            if data:
                return decode_element_chain(data)
    return []


def collect_params(root: ET.Element) -> Dict[Tuple[str, str], str]:
    d: Dict[Tuple[str, str], str] = {}
    for p in root.findall(".//Param"):
        eid = p.attrib.get("ElementID", "")
        pid = p.attrib.get("ParamID", "")
        val = p.attrib.get("Value", "")
        if eid or pid:
            d[(eid, pid)] = val
    return d


def collect_module_enabled(root: ET.Element) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for child in root.iter():
        if "Enabled" in child.attrib:
            out[child.tag] = child.attrib.get("Enabled", "")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-xml", required=True)
    ap.add_argument("--xmls", nargs="+", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    outdir = ensure_dir(args.outdir)
    base = Path(args.base_xml)
    xmls = [Path(p) for p in args.xmls]
    for p in [base] + xmls:
        if not p.exists():
            raise SystemExit(f"Missing XML: {p}")

    base_root = parse_xml(base).getroot()
    base_chain = get_element_chain(base_root)
    base_params = collect_params(base_root)

    chain_rows = []
    diff_rows = []
    enabled_rows = []

    def add_chain_row(label: str, path: Path, root: ET.Element) -> None:
        chain = get_element_chain(root)
        chain_rows.append({
            "file": path.name,
            "role": label,
            "chain": " -> ".join(chain),
            "module_count": len(chain),
        })
        for mod, en in collect_module_enabled(root).items():
            enabled_rows.append({"file": path.name, "xml_tag": mod, "Enabled": en})

    add_chain_row("base", base, base_root)

    for cand in xmls:
        root = parse_xml(cand).getroot()
        add_chain_row("candidate", cand, root)
        cparams = collect_params(root)
        keys = sorted(set(base_params.keys()) | set(cparams.keys()))
        for eid, pid in keys:
            bv = base_params.get((eid, pid))
            cv = cparams.get((eid, pid))
            if bv != cv:
                diff_rows.append({
                    "candidate": cand.name,
                    "ElementID": eid,
                    "ParamID": pid,
                    "base_value": bv,
                    "candidate_value": cv,
                })

    write_csv(outdir / "xml_chain.csv", chain_rows)
    write_csv(outdir / "xml_enabled_tags.csv", enabled_rows)
    write_csv(outdir / "xml_param_diffs.csv", diff_rows)

    md = []
    md.append("# Ozone XML audit\n\n")
    md.append(f"Base XML: `{base.name}`\n\n")
    md.append("## ElementChain\n\n")
    md.append("| File | Role | Module count | Chain |\n")
    md.append("|---|---|---:|---|\n")
    for row in chain_rows:
        md.append(f"| `{row['file']}` | {row['role']} | {row['module_count']} | {row['chain']} |\n")
    md.append("\n## Param diffs\n\n")
    if not diff_rows:
        md.append("No Param differences found. If audio differs, check ElementChain, ExtraBytes, or host state.\n")
    else:
        md.append("| Candidate | ElementID | ParamID | Base | Candidate |\n")
        md.append("|---|---|---|---:|---:|\n")
        for row in diff_rows[:500]:
            md.append(f"| `{row['candidate']}` | {row['ElementID']} | {row['ParamID']} | {row['base_value']} | {row['candidate_value']} |\n")
        if len(diff_rows) > 500:
            md.append(f"\nDiff table truncated in MD. Full CSV has {len(diff_rows)} rows.\n")
    md.append("\n## Audit notes\n\n")
    md.append("- Active Ozone module order must be read from ElementChain, not Enabled=1.\n")
    md.append("- If a candidate changes only Target Loudness and not Maximizer/Gain, render may be unchanged.\n")
    md.append("- For Stabilizer TS, check ProcessingMode, TameTransients and Aux:* params.\n")
    (outdir / "xml_audit.md").write_text("".join(md), encoding="utf-8")

    print(f"OK: wrote XML audit to {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
