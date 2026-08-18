#!/usr/bin/env python3
"""Autonomous repository and P0 evidence checks for OZONE12_MASTERING_LAB.

The checker never fabricates REAPER/Ozone evidence. Missing prerequisites are
reported as BLOCKED; an observed mismatch is FAIL. Reports are deterministic
JSON/Markdown and every requested mode returns a meaningful process exit code.
"""

from __future__ import annotations

import argparse
import compileall
import hashlib
import json
import math
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_PATH = ROOT / "dist" / "OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1_3.zip"
ARCHIVE_SHA256 = "f78e8dac9dc81fe60e110442281c4da988a128f4591e1cb515c64761e89e100e"
VALID_STATUSES = {"PASS", "FAIL", "BLOCKED", "SKIP"}
STATUS_RANK = {"PASS": 0, "SKIP": 0, "BLOCKED": 1, "FAIL": 2}
EXIT_BY_STATUS = {"PASS": 0, "SKIP": 0, "BLOCKED": 3, "FAIL": 2}
REQUIRED_NEGATIVE_TESTS = {"wrong_target_hash", "api_failure", "readback_mismatch"}
REQUIRED_READBACK_FIELDS = {
    "schema_version",
    "state_id",
    "backend",
    "source_sha256",
    "target_state_sha256",
    "loaded_state_sha256",
    "plugin_identity",
    "plugin_version",
    "plugin_build",
    "element_chain",
    "readback_ok",
    "render_invoked",
}


@dataclass
class CheckResult:
    check_id: str
    phase: str
    status: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid status: {self.status}")


class Results:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.items: list[CheckResult] = []

    def add(
        self,
        check_id: str,
        phase: str,
        status: str,
        summary: str,
        **details: Any,
    ) -> CheckResult:
        item = CheckResult(check_id, phase, status, summary, details)
        self.items.append(item)
        print(f"[{status:7}] {check_id}: {summary}")
        return item

    @property
    def overall(self) -> str:
        if not self.items:
            return "BLOCKED"
        return max((item.status for item in self.items), key=STATUS_RANK.__getitem__)

    @property
    def exit_code(self) -> int:
        return EXIT_BY_STATUS[self.overall]

    def write(self, outdir: Path, extra: dict[str, Any] | None = None) -> None:
        outdir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
            "overall_status": self.overall,
            "exit_code": self.exit_code,
            "checks": [asdict(item) for item in self.items],
        }
        if extra:
            payload.update(extra)
        (outdir / "autocheck.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        lines = [
            "# OZONE12 autonomous checks\n\n",
            f"Overall: **{self.overall}**  \n",
            f"Mode: `{self.mode}`  \n",
            f"Generated UTC: `{payload['generated_utc']}`\n\n",
            "| Check | Phase | Status | Summary |\n",
            "|---|---|---|---|\n",
        ]
        for item in self.items:
            summary = item.summary.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| `{item.check_id}` | `{item.phase}` | **{item.status}** | {summary} |\n"
            )
        lines.append("\n`BLOCKED` means that required evidence/prerequisites are missing; it is never treated as PASS.\n")
        (outdir / "autocheck.md").write_text("".join(lines), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command: Sequence[str], cwd: Path = ROOT, timeout: int = 600) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": list(command),
            "returncode": completed.returncode,
            "stdout": completed.stdout[-8000:],
            "stderr": completed.stderr[-8000:],
        }
    except FileNotFoundError as exc:
        return {"command": list(command), "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": list(command),
            "returncode": 124,
            "stdout": str(exc.stdout or "")[-8000:],
            "stderr": str(exc.stderr or "timeout")[-8000:],
        }


def add_command_check(
    results: Results,
    check_id: str,
    phase: str,
    command: Sequence[str],
    summary: str,
    timeout: int = 600,
) -> None:
    observed = run_command(command, timeout=timeout)
    status = "PASS" if observed["returncode"] == 0 else "FAIL"
    results.add(check_id, phase, status, summary, **observed)


def run_repository_checks(results: Results) -> None:
    version_ok = sys.version_info[:2] == (3, 12)
    results.add(
        "repo.python",
        "repository",
        "PASS" if version_ok else "FAIL",
        f"Python {platform.python_version()} (required 3.12.x)",
        executable=sys.executable,
    )

    if not ARCHIVE_PATH.exists():
        results.add("repo.archive", "repository", "FAIL", "frozen v1.3 archive is missing")
    else:
        observed_hash = sha256_file(ARCHIVE_PATH)
        bad_member: str | None = None
        zip_error: str | None = None
        try:
            with zipfile.ZipFile(ARCHIVE_PATH) as archive:
                bad_member = archive.testzip()
        except Exception as exc:  # pragma: no cover - defensive corruption path
            zip_error = str(exc)
        archive_ok = observed_hash == ARCHIVE_SHA256 and bad_member is None and zip_error is None
        results.add(
            "repo.archive",
            "repository",
            "PASS" if archive_ok else "FAIL",
            "frozen archive integrity and SHA-256",
            path=str(ARCHIVE_PATH),
            expected_sha256=ARCHIVE_SHA256,
            observed_sha256=observed_hash,
            bad_member=bad_member,
            zip_error=zip_error,
        )

    compiled = compileall.compile_dir(str(ROOT / "tools"), quiet=1, force=True)
    results.add(
        "repo.compile",
        "repository",
        "PASS" if compiled else "FAIL",
        "all Python tools compile",
    )

    add_command_check(
        results,
        "repo.process_only",
        "repository",
        [sys.executable, "tools/validate_process_only_scope.py"],
        "process-only repository scope",
    )
    add_command_check(
        results,
        "repo.manifests",
        "repository",
        [sys.executable, "tools/refresh_manifests.py"],
        "repository manifests match current tree",
    )
    add_command_check(
        results,
        "repo.meter_self_test",
        "repository",
        [sys.executable, "tools/stage_toolkit/oz12_mastering_meter.py", "--self-test"],
        "automatic mastering meter synthetic self-test",
        timeout=900,
    )
    add_command_check(
        results,
        "repo.autocheck_self_test",
        "repository",
        [sys.executable, str(Path(__file__).resolve()), "self-test", "--quiet"],
        "autonomous P0 evaluator positive/negative self-test",
        timeout=300,
    )

    required_programs = {}
    for name in ("ffmpeg", "ffprobe"):
        path = shutil.which(name)
        required_programs[name] = path
    results.add(
        "repo.codec_tools",
        "repository",
        "PASS" if all(required_programs.values()) else "FAIL",
        "ffmpeg and ffprobe are available",
        **required_programs,
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def compare_expected(observed: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            return False
        for key, value in expected.items():
            if key.endswith("_prefix"):
                observed_key = key.removesuffix("_prefix")
                if observed_key not in observed or not str(observed[observed_key]).casefold().startswith(str(value).casefold()):
                    return False
            elif key.endswith("_contains"):
                observed_key = key.removesuffix("_contains")
                if observed_key not in observed or str(value).casefold() not in str(observed[observed_key]).casefold():
                    return False
            elif key not in observed or not compare_expected(observed[key], value):
                return False
        return True
    if isinstance(expected, list):
        return observed == expected
    return str(observed).casefold() == str(expected).casefold()


def evaluate_environment(
    results: Results,
    config: dict[str, Any],
    observed_path: Path | None,
) -> None:
    expected = config.get("expected_environment", {})
    if observed_path is None or not observed_path.exists():
        results.add(
            "p0.0.environment",
            "P0.0",
            "BLOCKED",
            "observed environment snapshot is missing",
            expected=expected,
        )
        return
    try:
        observed = load_json(observed_path)
    except Exception as exc:
        results.add("p0.0.environment", "P0.0", "FAIL", "invalid environment JSON", error=str(exc))
        return

    mismatches = []
    for key, value in expected.items():
        if key not in observed or not compare_expected(observed.get(key), value):
            mismatches.append({"field": key, "expected": value, "observed": observed.get(key)})
    required_binaries = observed.get("required_binaries", {})
    missing = sorted(key for key, value in required_binaries.items() if value is not True)
    ok = not mismatches and not missing
    results.add(
        "p0.0.environment",
        "P0.0",
        "PASS" if ok else "FAIL",
        "environment lock matches config" if ok else "environment lock mismatch",
        observed_path=str(observed_path),
        mismatches=mismatches,
        missing_binaries=missing,
    )


def pcm_samples(raw: bytes, sample_width: int) -> Iterable[int]:
    if sample_width == 1:
        return (value - 128 for value in raw)
    if sample_width == 2:
        count = len(raw) // 2
        return struct.unpack(f"<{count}h", raw)
    if sample_width == 3:
        def values() -> Iterable[int]:
            for index in range(0, len(raw), 3):
                value = raw[index] | (raw[index + 1] << 8) | (raw[index + 2] << 16)
                yield value - (1 << 24) if value & (1 << 23) else value
        return values()
    if sample_width == 4:
        count = len(raw) // 4
        return struct.unpack(f"<{count}i", raw)
    raise ValueError(f"unsupported PCM sample width: {sample_width}")


def read_pcm_wav(path: Path) -> tuple[dict[str, int], bytes]:
    with wave.open(str(path), "rb") as stream:
        if stream.getcomptype() != "NONE":
            raise ValueError(f"compressed WAV is not supported: {stream.getcomptype()}")
        info = {
            "channels": stream.getnchannels(),
            "sample_width": stream.getsampwidth(),
            "sample_rate": stream.getframerate(),
            "frames": stream.getnframes(),
        }
        return info, stream.readframes(stream.getnframes())


def compare_wavs(reference: Path, candidate: Path) -> dict[str, Any]:
    ref_info, ref_raw = read_pcm_wav(reference)
    cand_info, cand_raw = read_pcm_wav(candidate)
    same_format = ref_info == cand_info
    if not same_format:
        return {
            "reference": str(reference),
            "candidate": str(candidate),
            "same_format": False,
            "reference_format": ref_info,
            "candidate_format": cand_info,
            "sample_identical": False,
            "max_abs_diff": None,
            "rms_diff": None,
        }
    ref_values = pcm_samples(ref_raw, ref_info["sample_width"])
    cand_values = pcm_samples(cand_raw, cand_info["sample_width"])
    max_value = float(1 << (8 * ref_info["sample_width"] - 1))
    max_abs = 0.0
    sum_squares = 0.0
    count = 0
    for left, right in zip(ref_values, cand_values):
        delta = (right - left) / max_value
        max_abs = max(max_abs, abs(delta))
        sum_squares += delta * delta
        count += 1
    rms = math.sqrt(sum_squares / count) if count else 0.0
    return {
        "reference": str(reference),
        "candidate": str(candidate),
        "same_format": True,
        "format": ref_info,
        "sample_identical": ref_raw == cand_raw,
        "max_abs_diff": max_abs,
        "rms_diff": rms,
    }


def check_wav_group(
    results: Results,
    check_id: str,
    phase: str,
    paths: list[Path],
    minimum_count: int,
    allowed_max_abs: float | None = None,
) -> float | None:
    missing = [str(path) for path in paths if not path.exists()]
    if len(paths) < minimum_count or missing:
        results.add(
            check_id,
            phase,
            "BLOCKED",
            f"need at least {minimum_count} existing PCM WAV files",
            configured_count=len(paths),
            missing=missing,
        )
        return None
    comparisons = []
    try:
        for candidate in paths[1:]:
            comparisons.append(compare_wavs(paths[0], candidate))
    except Exception as exc:
        results.add(check_id, phase, "FAIL", "WAV comparison failed", error=str(exc))
        return None
    format_ok = all(item["same_format"] for item in comparisons)
    observed_max = max(float(item["max_abs_diff"] or 0.0) for item in comparisons)
    within_limit = allowed_max_abs is None or observed_max <= allowed_max_abs
    ok = format_ok and within_limit
    results.add(
        check_id,
        phase,
        "PASS" if ok else "FAIL",
        "PCM renders are repeatable" if ok else "PCM render mismatch exceeds baseline",
        observed_max_abs=observed_max,
        allowed_max_abs=allowed_max_abs,
        comparisons=comparisons,
    )
    return observed_max if ok else None


def evaluate_dry_manifest(
    results: Results,
    config: dict[str, Any],
    config_dir: Path,
    dry_paths: list[Path],
) -> None:
    value = config.get("dry_harness_manifest")
    manifest_path = resolve_path(config_dir, value) if value else None
    if manifest_path is None or not manifest_path.exists():
        results.add("p0.1.run_manifest", "P0.1", "BLOCKED", "Dry Harness run manifest is missing")
        return
    try:
        manifest = load_json(manifest_path)
        rows = manifest.get("runs", [])
        hashes = [str(row.get("sha256", "")).casefold() for row in rows]
        expected_hashes = [sha256_file(path).casefold() for path in dry_paths if path.exists()]
        hashes_match = sorted(hashes) == sorted(expected_hashes)
        ok = (
            manifest.get("schema_version") == 1
            and manifest.get("fx_blocks_detected") is False
            and len(rows) >= 3
            and hashes_match
            and len(expected_hashes) == len(dry_paths) >= 3
        )
        results.add(
            "p0.1.run_manifest",
            "P0.1",
            "PASS" if ok else "FAIL",
            "Dry Harness manifest proves sequential no-FX renders",
            path=str(manifest_path),
            run_count=len(rows),
            hashes_match=hashes_match,
            fx_blocks_detected=manifest.get("fx_blocks_detected"),
        )
    except Exception as exc:
        results.add("p0.1.run_manifest", "P0.1", "FAIL", "invalid Dry Harness manifest", error=str(exc))


def validate_readback(
    path: Path,
    state_id: str,
    backend: str,
    expected_plugin: dict[str, Any],
    expected_source_sha256: str | None,
    require_render: bool = True,
) -> tuple[bool, dict[str, Any]]:
    if not path.exists():
        return False, {"error": "missing readback", "path": str(path)}
    try:
        data = load_json(path)
    except Exception as exc:
        return False, {"error": f"invalid readback JSON: {exc}", "path": str(path)}
    missing_fields = sorted(REQUIRED_READBACK_FIELDS - set(data))
    failures = []
    if missing_fields:
        failures.append(f"missing fields: {', '.join(missing_fields)}")
    if data.get("state_id") != state_id:
        failures.append("state_id mismatch")
    if str(data.get("backend", "")).casefold() != backend.casefold():
        failures.append("backend mismatch")
    if data.get("target_state_sha256") != data.get("loaded_state_sha256"):
        failures.append("loaded state hash differs from target")
    for key in ("source_sha256", "target_state_sha256", "loaded_state_sha256"):
        if not re.fullmatch(r"[0-9a-fA-F]{64}", str(data.get(key, ""))):
            failures.append(f"{key} is not a SHA-256 hex digest")
    if expected_source_sha256 and str(data.get("source_sha256", "")).casefold() != expected_source_sha256.casefold():
        failures.append("source_sha256 differs from configured source WAV")
    if data.get("readback_ok") is not True:
        failures.append("readback_ok is not true")
    if require_render and data.get("render_invoked") is not True:
        failures.append("render_invoked is not true")
    if not isinstance(data.get("element_chain"), list) or not data.get("element_chain"):
        failures.append("element_chain is empty or invalid")
    for key, expected in expected_plugin.items():
        if not compare_expected(data.get(key), expected):
            failures.append(f"{key} mismatch")
    return not failures, {"path": str(path), "failures": failures, "readback": data}


def state_artifact(
    config_dir: Path,
    states: dict[str, Any],
    state_id: str,
    backend: str,
) -> tuple[Path, Path] | None:
    item = states.get(state_id, {}).get(backend)
    if not isinstance(item, dict) or not item.get("wav") or not item.get("readback"):
        return None
    return resolve_path(config_dir, item["wav"]), resolve_path(config_dir, item["readback"])


def evaluate_state_backends(
    results: Results,
    config: dict[str, Any],
    config_dir: Path,
    dry_baseline: float | None,
    expected_source_sha256: str | None,
) -> None:
    states = config.get("states", {})
    expected_plugin = config.get("expected_plugin", {})
    state_ids = ("S0", "S1", "S2")

    l0_data: dict[str, tuple[Path, dict[str, Any]]] = {}
    l0_failures = []
    for state_id in state_ids:
        artifact = state_artifact(config_dir, states, state_id, "L0")
        if artifact is None:
            l0_failures.append(f"{state_id}: missing L0 artifact")
            continue
        wav_path, readback_path = artifact
        valid, detail = validate_readback(
            readback_path, state_id, "L0", expected_plugin, expected_source_sha256
        )
        if not wav_path.exists():
            valid = False
            detail.setdefault("failures", []).append("render WAV missing")
        if not valid:
            l0_failures.append(f"{state_id}: " + "; ".join(detail.get("failures", [])))
        else:
            l0_data[state_id] = (wav_path, detail["readback"])
    results.add(
        "p0.2.l0_oracle",
        "P0.2",
        "PASS" if len(l0_data) == 3 else "BLOCKED" if not l0_data else "FAIL",
        "L0 oracle evidence for S0/S1/S2",
        failures=l0_failures,
    )

    l1_failures = []
    l1_complete = dry_baseline is not None and len(l0_data) == 3
    for state_id in state_ids:
        artifact = state_artifact(config_dir, states, state_id, "L1")
        if artifact is None:
            l1_complete = False
            l1_failures.append(f"{state_id}: missing L1 artifact")
            continue
        wav_path, readback_path = artifact
        valid, detail = validate_readback(
            readback_path, state_id, "L1", expected_plugin, expected_source_sha256
        )
        if not wav_path.exists():
            valid = False
            detail.setdefault("failures", []).append("render WAV missing")
        if valid and state_id in l0_data and dry_baseline is not None:
            try:
                comparison = compare_wavs(l0_data[state_id][0], wav_path)
                if not comparison["same_format"] or float(comparison["max_abs_diff"] or 0.0) > dry_baseline:
                    valid = False
                    detail.setdefault("failures", []).append("render differs from L0 beyond Dry Harness baseline")
                if detail["readback"].get("element_chain") != l0_data[state_id][1].get("element_chain"):
                    valid = False
                    detail.setdefault("failures", []).append("ElementChain differs from L0")
            except Exception as exc:
                valid = False
                detail.setdefault("failures", []).append(f"comparison failed: {exc}")
        else:
            l1_complete = False
        if not valid:
            l1_failures.append(f"{state_id}: " + "; ".join(detail.get("failures", [])))
    results.add(
        "p0.3.l1_frozen_rpp",
        "P0.3",
        "PASS" if l1_complete and not l1_failures else "BLOCKED" if not l1_complete else "FAIL",
        "L1 frozen RPP matches L0 for S0/S1/S2",
        failures=l1_failures,
        note="L1-only can never produce full P0 PASS",
    )

    backend_qualification: dict[str, bool] = {}
    backend_statuses: dict[str, str] = {}
    selected_backend = str(config.get("selected_backend", "")).upper()
    for backend, phase in (("L2", "P0.4"), ("L3", "P0.5")):
        failures = []
        comparisons = []
        complete = dry_baseline is not None and len(l0_data) == 3
        for state_id in state_ids:
            artifact = state_artifact(config_dir, states, state_id, backend)
            if artifact is None:
                complete = False
                failures.append(f"{state_id}: missing {backend} artifact")
                continue
            wav_path, readback_path = artifact
            valid, detail = validate_readback(
                readback_path, state_id, backend, expected_plugin, expected_source_sha256
            )
            if not wav_path.exists():
                valid = False
                detail.setdefault("failures", []).append("render WAV missing")
            if valid and state_id in l0_data and dry_baseline is not None:
                try:
                    comparison = compare_wavs(l0_data[state_id][0], wav_path)
                    comparisons.append(comparison)
                    if not comparison["same_format"] or float(comparison["max_abs_diff"] or 0.0) > dry_baseline:
                        valid = False
                        detail.setdefault("failures", []).append("render differs from L0 beyond Dry Harness baseline")
                    if detail["readback"].get("element_chain") != l0_data[state_id][1].get("element_chain"):
                        valid = False
                        detail.setdefault("failures", []).append("ElementChain differs from L0")
                except Exception as exc:
                    valid = False
                    detail.setdefault("failures", []).append(f"comparison failed: {exc}")
            else:
                complete = False
            if not valid:
                failures.append(f"{state_id}: " + "; ".join(detail.get("failures", [])))
        qualified = complete and not failures
        backend_qualification[backend] = qualified
        if qualified:
            backend_status = "PASS"
        elif backend != selected_backend:
            backend_status = "SKIP"
        elif not complete:
            backend_status = "BLOCKED"
        else:
            backend_status = "FAIL"
        backend_statuses[backend] = backend_status
        results.add(
            f"{phase.lower()}.{backend.lower()}_state",
            phase,
            backend_status,
            f"{backend} matches L0 for S0/S1/S2",
            failures=failures,
            comparisons=comparisons,
            selected=backend == selected_backend,
        )

    l4 = config.get("l4_probe", {})
    l4_path = resolve_path(config_dir, l4["readback"]) if l4.get("readback") else None
    if l4_path is None or not l4_path.exists():
        results.add("p0.6.l4_parameter", "P0.6", "BLOCKED", "L4 published-parameter evidence is missing")
    else:
        try:
            l4_data = load_json(l4_path)
            ok = (
                l4_data.get("backend") == "L4"
                and l4_data.get("readback_ok") is True
                and bool(l4_data.get("changed_parameter"))
                and l4_data.get("before_value") != l4_data.get("after_value")
            )
            results.add(
                "p0.6.l4_parameter",
                "P0.6",
                "PASS" if ok else "FAIL",
                "one published Ozone parameter changed and read back",
                path=str(l4_path),
                evidence=l4_data,
            )
        except Exception as exc:
            results.add("p0.6.l4_parameter", "P0.6", "FAIL", "invalid L4 evidence", error=str(exc))

    if len(l0_data) < 2 or "S0" not in l0_data or "S2" not in l0_data:
        results.add("p0.7.s2", "P0.7", "BLOCKED", "S0/S2 L0 readback is incomplete")
    else:
        s0_chain = l0_data["S0"][1].get("element_chain")
        s2_chain = l0_data["S2"][1].get("element_chain")
        structural = s0_chain != s2_chain
        selected = str(config.get("selected_backend", "")).upper()
        selected_s2 = state_artifact(config_dir, states, "S2", selected) if selected else None
        selected_match = False
        if selected_s2 and selected in backend_qualification:
            valid, detail = validate_readback(
                selected_s2[1], "S2", selected, expected_plugin, expected_source_sha256
            )
            selected_match = valid and detail.get("readback", {}).get("element_chain") == s2_chain
        results.add(
            "p0.7.s2",
            "P0.7",
            "PASS" if structural and selected_match else "FAIL",
            "S2 discriminates structure and selected backend restores it",
            selected_backend=selected,
            s0_chain=s0_chain,
            s2_chain=s2_chain,
            selected_match=selected_match,
        )

    selected = str(config.get("selected_backend", "")).upper()
    if selected not in {"L2", "L3"}:
        results.add("p0.7.backend_selection", "P0.7", "FAIL", "selected_backend must be L2 or L3")
    elif not backend_qualification.get(selected, False):
        selected_status = backend_statuses.get(selected, "BLOCKED")
        results.add(
            "p0.7.backend_selection",
            "P0.7",
            "BLOCKED" if selected_status == "BLOCKED" else "FAIL",
            f"selected backend {selected} is not qualified",
        )
    else:
        results.add("p0.7.backend_selection", "P0.7", "PASS", f"selected backend {selected} is qualified")


def evaluate_negative_gates(results: Results, config: dict[str, Any], config_dir: Path) -> None:
    configured = config.get("negative_tests", [])
    by_name = {item.get("name"): item for item in configured if isinstance(item, dict)}
    missing = sorted(REQUIRED_NEGATIVE_TESTS - set(by_name))
    missing_evidence = []
    failures = []
    details = []
    for name in sorted(REQUIRED_NEGATIVE_TESTS):
        item = by_name.get(name)
        if item is None:
            continue
        result_path = resolve_path(config_dir, item.get("result", ""))
        if not result_path.exists():
            missing_evidence.append(f"{name}: result JSON missing")
            continue
        try:
            data = load_json(result_path)
        except Exception as exc:
            failures.append(f"{name}: invalid JSON: {exc}")
            continue
        output_dir = resolve_path(config_dir, item["output_dir"]) if item.get("output_dir") else None
        wavs = sorted(str(path) for path in output_dir.rglob("*.wav")) if output_dir and output_dir.exists() else []
        ok = (
            data.get("blocked") is True
            and data.get("render_invoked") is False
            and int(data.get("wav_created_count", -1)) == 0
            and not wavs
        )
        if not ok:
            failures.append(f"{name}: render gate did not stop with 0 WAV")
        details.append({"name": name, "result": data, "observed_wavs": wavs})
    status = "FAIL" if failures else "BLOCKED" if missing or missing_evidence else "PASS"
    results.add(
        "p0.7.negative_gates",
        "P0.7",
        status,
        "negative gates stop before render and create 0 WAV",
        missing_tests=missing,
        missing_evidence=missing_evidence,
        failures=failures,
        tests=details,
    )


def collect_referenced_files(config: dict[str, Any], config_dir: Path) -> list[Path]:
    paths: set[Path] = set()
    if config.get("source_wav"):
        paths.add(resolve_path(config_dir, config["source_wav"]))
    if config.get("dry_harness_manifest"):
        paths.add(resolve_path(config_dir, config["dry_harness_manifest"]))
    for value in config.get("dry_renders", []):
        paths.add(resolve_path(config_dir, value))
    for state in config.get("states", {}).values():
        if not isinstance(state, dict):
            continue
        for artifact in state.values():
            if isinstance(artifact, dict):
                for key in ("wav", "readback"):
                    if artifact.get(key):
                        paths.add(resolve_path(config_dir, artifact[key]))
    for value in config.get("backend_repeat_renders", []):
        paths.add(resolve_path(config_dir, value))
    l4 = config.get("l4_probe", {})
    if l4.get("readback"):
        paths.add(resolve_path(config_dir, l4["readback"]))
    for item in config.get("negative_tests", []):
        if isinstance(item, dict) and item.get("result"):
            paths.add(resolve_path(config_dir, item["result"]))
    return sorted(path for path in paths if path.exists() and path.is_file())


def write_evidence_manifest(config: dict[str, Any], config_path: Path, outdir: Path) -> Path:
    files = [config_path.resolve()] + collect_referenced_files(config, config_path.parent)
    rows = []
    for path in sorted(set(files)):
        try:
            display = path.relative_to(config_path.parent.resolve()).as_posix()
        except ValueError:
            display = str(path)
        rows.append({"path": display, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    payload = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "config": str(config_path),
        "files": rows,
    }
    manifest = outdir / "evidence_manifest.json"
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def evaluate_p0(
    config_path: Path,
    observed_environment: Path | None,
    outdir: Path,
    quiet: bool = False,
) -> Results:
    results = Results("p0")
    if not config_path.exists():
        results.add("p0.config", "P0", "BLOCKED", "P0 config is missing", path=str(config_path))
        results.write(outdir)
        return results
    try:
        config = load_json(config_path)
    except Exception as exc:
        results.add("p0.config", "P0", "FAIL", "P0 config is invalid", error=str(exc))
        results.write(outdir)
        return results
    if config.get("schema_version") != 1:
        results.add("p0.config", "P0", "FAIL", "unsupported config schema_version")
        results.write(outdir)
        return results
    results.add("p0.config", "P0", "PASS", "P0 config schema is valid", path=str(config_path))
    evaluate_environment(results, config, observed_environment)

    config_dir = config_path.parent.resolve()
    source_value = config.get("source_wav")
    source_path = resolve_path(config_dir, source_value) if source_value else None
    if source_path is None or not source_path.exists():
        expected_source_sha256 = None
        results.add("p0.source", "P0.0", "BLOCKED", "immutable source WAV is missing")
    else:
        expected_source_sha256 = sha256_file(source_path)
        results.add(
            "p0.source",
            "P0.0",
            "PASS",
            "immutable source WAV identified",
            path=str(source_path),
            sha256=expected_source_sha256,
        )
    dry_paths = [resolve_path(config_dir, value) for value in config.get("dry_renders", [])]
    dry_baseline = check_wav_group(results, "p0.1.dry_harness", "P0.1", dry_paths, 3)
    evaluate_dry_manifest(results, config, config_dir, dry_paths)
    evaluate_state_backends(
        results, config, config_dir, dry_baseline, expected_source_sha256
    )

    repeat_paths = [resolve_path(config_dir, value) for value in config.get("backend_repeat_renders", [])]
    check_wav_group(
        results,
        "p0.7.backend_repeats",
        "P0.7",
        repeat_paths,
        3,
        allowed_max_abs=dry_baseline,
    )
    evaluate_negative_gates(results, config, config_dir)

    outdir.mkdir(parents=True, exist_ok=True)
    manifest = write_evidence_manifest(config, config_path, outdir)
    results.add(
        "p0.evidence_manifest",
        "P0",
        "PASS",
        "evidence manifest written outside repository",
        path=str(manifest),
    )
    results.write(outdir, extra={"dry_baseline_max_abs": dry_baseline})
    if not quiet:
        print(f"Report: {outdir / 'autocheck.json'}")
    return results


def write_pcm_wav(path: Path, samples: Sequence[int], channels: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(channels)
        stream.setsampwidth(2)
        stream.setframerate(48000)
        frames = []
        for sample in samples:
            frames.extend([sample] * channels)
        stream.writeframes(struct.pack(f"<{len(frames)}h", *frames))


def run_self_test(quiet: bool = False) -> int:
    with tempfile.TemporaryDirectory(prefix="oz12-autocheck-") as temp:
        root = Path(temp)
        samples_by_state = {
            "S0": [0, 100, -100, 500, -500] * 100,
            "S1": [0, 200, -200, 700, -700] * 100,
            "S2": [0, 300, -300, 900, -900] * 100,
        }
        dry = []
        for index in range(3):
            path = root / "dry" / f"D0_{index + 1}.wav"
            write_pcm_wav(path, samples_by_state["S0"])
            dry.append(path.relative_to(root).as_posix())
        dry_manifest_path = root / "dry" / "dry_harness_runs.json"
        dry_manifest_path.write_text(json.dumps({
            "schema_version": 1,
            "fx_blocks_detected": False,
            "runs": [
                {"run": index + 1, "sha256": sha256_file(root / value)}
                for index, value in enumerate(dry)
            ],
        }), encoding="utf-8")

        states: dict[str, Any] = {}
        chains = {"S0": ["Equalizer", "Impact"], "S1": ["Equalizer", "Impact"], "S2": ["Impact", "Equalizer"]}
        source_path = root / "input" / "source.wav"
        write_pcm_wav(source_path, samples_by_state["S0"])
        source_hash = sha256_file(source_path)
        for state_id in ("S0", "S1", "S2"):
            states[state_id] = {}
            for backend in ("L0", "L1", "L2", "L3"):
                base = root / "states" / state_id / backend
                wav_path = base / "render.wav"
                readback_path = base / "readback.json"
                write_pcm_wav(wav_path, samples_by_state[state_id])
                state_hash = hashlib.sha256(f"{state_id}-state".encode()).hexdigest()
                readback = {
                    "schema_version": 1,
                    "state_id": state_id,
                    "backend": backend,
                    "source_sha256": source_hash,
                    "target_state_sha256": state_hash,
                    "loaded_state_sha256": state_hash,
                    "plugin_identity": "Ozone 12 VST3",
                    "plugin_version": "120002",
                    "plugin_build": "1331",
                    "element_chain": chains[state_id],
                    "readback_ok": True,
                    "render_invoked": True,
                }
                readback_path.write_text(json.dumps(readback), encoding="utf-8")
                states[state_id][backend] = {
                    "wav": wav_path.relative_to(root).as_posix(),
                    "readback": readback_path.relative_to(root).as_posix(),
                }

        l4_path = root / "l4" / "readback.json"
        l4_path.parent.mkdir(parents=True)
        l4_path.write_text(json.dumps({
            "backend": "L4", "readback_ok": True, "changed_parameter": "Bypass",
            "before_value": 0, "after_value": 1,
        }), encoding="utf-8")

        repeats = []
        for index in range(3):
            path = root / "repeats" / f"repeat_{index + 1}.wav"
            write_pcm_wav(path, samples_by_state["S0"])
            repeats.append(path.relative_to(root).as_posix())

        negatives = []
        for name in sorted(REQUIRED_NEGATIVE_TESTS):
            base = root / "negative" / name
            base.mkdir(parents=True)
            result_path = base / "result.json"
            result_path.write_text(json.dumps({
                "blocked": True, "render_invoked": False, "wav_created_count": 0,
            }), encoding="utf-8")
            negatives.append({
                "name": name,
                "result": result_path.relative_to(root).as_posix(),
                "output_dir": base.relative_to(root).as_posix(),
            })

        config = {
            "schema_version": 1,
            "expected_environment": {"python_version": "3.12"},
            "expected_plugin": {
                "plugin_identity": "Ozone 12 VST3",
                "plugin_version": "120002",
                "plugin_build": "1331",
            },
            "source_wav": source_path.relative_to(root).as_posix(),
            "dry_renders": dry,
            "dry_harness_manifest": dry_manifest_path.relative_to(root).as_posix(),
            "states": states,
            "selected_backend": "L2",
            "backend_repeat_renders": repeats,
            "l4_probe": {"readback": l4_path.relative_to(root).as_posix()},
            "negative_tests": negatives,
        }
        config_path = root / "p0_config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        environment_path = root / "environment_observed.json"
        environment_path.write_text(json.dumps({
            "python_version": "3.12", "required_binaries": {"python": True},
        }), encoding="utf-8")

        positive = evaluate_p0(config_path, environment_path, root / "positive", quiet=True)
        if positive.overall != "PASS":
            if not quiet:
                print("SELF-TEST FAIL: positive fixture did not PASS")
            return 2

        negative_result = root / negatives[0]["result"]
        data = load_json(negative_result)
        data["render_invoked"] = True
        negative_result.write_text(json.dumps(data), encoding="utf-8")
        negative = evaluate_p0(config_path, environment_path, root / "negative-report", quiet=True)
        gate = next(item for item in negative.items if item.check_id == "p0.7.negative_gates")
        if gate.status != "FAIL":
            if not quiet:
                print("SELF-TEST FAIL: unsafe negative fixture was not rejected")
            return 2
    if not quiet:
        print("SELF-TEST PASS")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    repo = sub.add_parser("repo", help="run every repository/CI check")
    repo.add_argument("--outdir", type=Path, default=ROOT / "reports" / "autocheck" / "repository")

    p0 = sub.add_parser("p0", help="evaluate complete P0 evidence")
    p0.add_argument("--config", type=Path, required=True)
    p0.add_argument("--observed-environment", type=Path)
    p0.add_argument("--outdir", type=Path, required=True)

    all_checks = sub.add_parser("all", help="run repository checks and P0 checks")
    all_checks.add_argument("--config", type=Path, required=True)
    all_checks.add_argument("--observed-environment", type=Path)
    all_checks.add_argument("--outdir", type=Path, required=True)

    self_test = sub.add_parser("self-test", help="run synthetic PASS/FAIL fixtures")
    self_test.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "self-test":
        return run_self_test(args.quiet)
    if args.command == "repo":
        results = Results("repository")
        run_repository_checks(results)
        results.write(args.outdir)
        print(f"Report: {args.outdir / 'autocheck.json'}")
        return results.exit_code
    if args.command == "p0":
        return evaluate_p0(args.config.resolve(), args.observed_environment, args.outdir.resolve()).exit_code
    if args.command == "all":
        repo_results = Results("repository")
        run_repository_checks(repo_results)
        repo_out = args.outdir.resolve() / "repository"
        repo_results.write(repo_out)
        p0_results = evaluate_p0(
            args.config.resolve(), args.observed_environment, args.outdir.resolve() / "p0"
        )
        overall = max((repo_results.overall, p0_results.overall), key=STATUS_RANK.__getitem__)
        summary = {
            "schema_version": 1,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall,
            "repository_status": repo_results.overall,
            "p0_status": p0_results.overall,
            "repository_report": str(repo_out / "autocheck.json"),
            "p0_report": str(args.outdir.resolve() / "p0" / "autocheck.json"),
        }
        args.outdir.mkdir(parents=True, exist_ok=True)
        (args.outdir / "autocheck_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Overall: {overall}")
        return EXIT_BY_STATUS[overall]
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
