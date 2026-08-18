#!/usr/bin/env python3
"""Automatic drum-attack, mono-loss and decoded-codec peak meter.

The meter compares one reference WAV with one candidate WAV. It writes:

* mastering_meter.json — complete machine-readable result;
* mastering_meter.csv — flat summary for decision logs;
* drum_attack_events.csv — event-aligned transient measurements;
* mastering_meter_report.md — concise human-readable report.

The drum detector is deliberately described as a proxy: it finds strong,
broad-band onsets in the full stereo master. It does not pretend to separate a
drum stem. Mono loss is measured as mid/mono energy retention relative to the
two stereo channels, overall and by band. Codec peaks are measured only after
an actual FFmpeg encode -> decode pass.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from scipy.io import wavfile
from scipy.ndimage import uniform_filter1d
from scipy.signal import butter, correlate, correlation_lags, find_peaks, resample_poly, sosfilt, welch


SCHEMA_VERSION = "1.0"
CODEC_SPECS: Dict[str, Dict[str, Any]] = {
    "mp3_320": {
        "extension": ".mp3",
        "label": "MP3 320 kbps",
        "encode_args": ["-c:a", "libmp3lame", "-b:a", "320k"],
    },
    "aac_256": {
        "extension": ".m4a",
        "label": "AAC 256 kbps",
        "encode_args": ["-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart"],
    },
    "aac_192": {
        "extension": ".m4a",
        "label": "AAC 192 kbps stress test",
        "encode_args": ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"],
    },
}
MONO_BANDS: List[Tuple[str, float, float]] = [
    ("low_20_120", 20.0, 120.0),
    ("low_mid_120_500", 120.0, 500.0),
    ("presence_500_4000", 500.0, 4000.0),
    ("high_4000_18000", 4000.0, 18000.0),
]
STATUS_RANK = {"NOT_APPLICABLE": 0, "MEASURED": 0, "PASS": 0, "WARN": 1, "FAIL": 2}


def db(value: float) -> float:
    """Amplitude/power-root value to dB, with a finite silence floor."""
    if not np.isfinite(value) or value <= 0.0:
        return -300.0
    return float(20.0 * math.log10(value))


def round_or_none(value: Any, digits: int = 3) -> Any:
    if value is None:
        return None
    if isinstance(value, (float, np.floating)):
        return round(float(value), digits) if np.isfinite(value) else None
    return value


def rms(audio: np.ndarray) -> float:
    if audio.size == 0:
        return 0.0
    x = np.asarray(audio, dtype=np.float64)
    return float(np.sqrt(np.mean(x * x)))


def rms_db(audio: np.ndarray) -> float:
    return db(rms(audio))


def peak_db(audio: np.ndarray) -> float:
    if audio.size == 0:
        return -300.0
    return db(float(np.max(np.abs(audio))))


def load_wav(path: Path) -> Tuple[int, np.ndarray, str]:
    """Load PCM/float WAV as samples x channels float32."""
    try:
        sample_rate, data = wavfile.read(str(path), mmap=True)
        backend = "scipy.io.wavfile:mmap"
    except (ValueError, OSError):
        sample_rate, data = wavfile.read(str(path), mmap=False)
        backend = "scipy.io.wavfile"
    data = np.asarray(data)
    if data.ndim == 1:
        data = data[:, None]
    if np.issubdtype(data.dtype, np.integer):
        info = np.iinfo(data.dtype)
        scale = float(max(abs(info.min), info.max))
        data = data.astype(np.float32) / scale
    else:
        data = data.astype(np.float32, copy=False)
    if not np.all(np.isfinite(data)):
        raise ValueError(f"Non-finite samples in {path}")
    return int(sample_rate), data, backend


def resample_audio(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if source_rate == target_rate:
        return audio
    divisor = math.gcd(source_rate, target_rate)
    up = target_rate // divisor
    down = source_rate // divisor
    return np.asarray(resample_poly(audio, up, down, axis=0), dtype=np.float32)


def mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return np.asarray(audio, dtype=np.float32)
    if audio.shape[1] == 1:
        return np.asarray(audio[:, 0], dtype=np.float32)
    return np.asarray(0.5 * (audio[:, 0] + audio[:, 1]), dtype=np.float32)


def alignment_envelope(audio: np.ndarray, sample_rate: int, target_rate: int = 1000) -> np.ndarray:
    x = np.abs(mono(audio)).astype(np.float64)
    divisor = math.gcd(sample_rate, target_rate)
    env = resample_poly(x, target_rate // divisor, sample_rate // divisor)
    smooth = max(1, int(round(0.020 * target_rate)))
    env = uniform_filter1d(env, size=smooth, mode="nearest")
    env -= float(np.mean(env))
    scale = float(np.std(env))
    if scale > 0.0:
        env /= scale
    return np.asarray(env, dtype=np.float32)


def estimate_alignment(
    reference: np.ndarray,
    candidate: np.ndarray,
    sample_rate: int,
    max_lag_seconds: float,
) -> Dict[str, Any]:
    analysis_rate = 1000
    ref_env = alignment_envelope(reference, sample_rate, analysis_rate)
    cand_env = alignment_envelope(candidate, sample_rate, analysis_rate)
    corr = correlate(cand_env, ref_env, mode="full", method="fft")
    lags = correlation_lags(cand_env.size, ref_env.size, mode="full")
    max_lag = int(round(max_lag_seconds * analysis_rate))
    valid = np.abs(lags) <= max_lag
    if not np.any(valid):
        lag_ds = 0
        confidence = 0.0
    else:
        valid_corr = corr[valid]
        valid_lags = lags[valid]
        index = int(np.argmax(valid_corr))
        lag_ds = int(valid_lags[index])
        denom = float(np.linalg.norm(ref_env) * np.linalg.norm(cand_env))
        confidence = float(valid_corr[index] / denom) if denom > 0 else 0.0
    lag_samples = int(round(lag_ds * sample_rate / analysis_rate))
    return {
        "candidate_lag_samples": lag_samples,
        "candidate_lag_ms": 1000.0 * lag_samples / sample_rate,
        "envelope_correlation": confidence,
        "analysis_rate_hz": analysis_rate,
        "max_lag_seconds": max_lag_seconds,
        "definition": "positive lag means candidate starts later than reference",
    }


def align_pair(reference: np.ndarray, candidate: np.ndarray, lag_samples: int) -> Tuple[np.ndarray, np.ndarray]:
    if lag_samples >= 0:
        ref_start, cand_start = 0, lag_samples
    else:
        ref_start, cand_start = -lag_samples, 0
    count = min(reference.shape[0] - ref_start, candidate.shape[0] - cand_start)
    if count <= 0:
        raise ValueError("No overlapping audio after alignment")
    channels = min(reference.shape[1], candidate.shape[1])
    return reference[ref_start:ref_start + count, :channels], candidate[cand_start:cand_start + count, :channels]


def active_rms(audio: np.ndarray, sample_rate: int) -> float:
    """RMS with a simple relative activity gate to avoid silence dominating match."""
    x = mono(audio).astype(np.float64)
    frame = max(1, int(round(0.400 * sample_rate)))
    hop = max(1, frame // 2)
    values: List[float] = []
    for start in range(0, max(1, x.size - frame + 1), hop):
        block = x[start:start + frame]
        if block.size:
            values.append(rms(block))
    if not values:
        return rms(x)
    arr = np.asarray(values)
    peak_frame = float(np.max(arr))
    threshold = peak_frame * (10.0 ** (-30.0 / 20.0))
    active = arr[arr >= threshold]
    if active.size == 0:
        return rms(x)
    return float(np.sqrt(np.mean(active * active)))


def level_match(reference: np.ndarray, candidate: np.ndarray, sample_rate: int) -> Tuple[np.ndarray, float]:
    ref_level = active_rms(reference, sample_rate)
    cand_level = active_rms(candidate, sample_rate)
    if cand_level <= 0.0 or ref_level <= 0.0:
        return candidate, 0.0
    gain = ref_level / cand_level
    return np.asarray(candidate * gain, dtype=np.float32), db(gain)


def detect_drum_attack_events(
    reference: np.ndarray,
    sample_rate: int,
    max_events: int,
) -> Tuple[List[int], Dict[str, Any]]:
    """Find strong broad-band onset events; this is a full-master drum proxy."""
    analysis_rate = min(4000, sample_rate)
    x = mono(reference).astype(np.float64)
    high = min(12000.0, sample_rate * 0.45)
    if high <= 40.0:
        raise ValueError("Sample rate is too low for onset analysis")
    sos = butter(3, [35.0, high], btype="bandpass", fs=sample_rate, output="sos")
    filtered = sosfilt(sos, x)
    divisor = math.gcd(sample_rate, analysis_rate)
    y = resample_poly(filtered, analysis_rate // divisor, sample_rate // divisor)
    energy = y * y
    fast_n = max(1, int(round(0.008 * analysis_rate)))
    slow_n = max(fast_n + 1, int(round(0.080 * analysis_rate)))
    rise_n = max(1, int(round(0.016 * analysis_rate)))
    fast = np.sqrt(np.maximum(uniform_filter1d(energy, size=fast_n, mode="nearest"), 1e-18))
    slow = np.sqrt(np.maximum(uniform_filter1d(energy, size=slow_n, mode="nearest"), 1e-18))
    fast_db = 20.0 * np.log10(fast + 1e-12)
    ratio = 20.0 * np.log10((fast + 1e-12) / (slow + 1e-12))
    earlier = np.roll(fast_db, rise_n)
    earlier[:rise_n] = fast_db[:rise_n]
    rise = np.maximum(0.0, fast_db - earlier)
    score = ratio + 0.35 * rise
    finite = np.isfinite(score) & np.isfinite(fast_db)
    if not np.any(finite):
        return [], {"events_detected": 0, "analysis_rate_hz": analysis_rate}
    activity_floor = max(float(np.percentile(fast_db[finite], 55.0)), float(np.max(fast_db[finite])) - 38.0)
    height = max(1.0, float(np.percentile(score[finite], 70.0)))
    peaks, properties = find_peaks(
        score,
        distance=max(1, int(round(0.085 * analysis_rate))),
        height=height,
        prominence=0.75,
    )
    peaks = peaks[fast_db[peaks] >= activity_floor]
    margin = int(round(0.180 * analysis_rate))
    peaks = peaks[(peaks >= margin) & (peaks < score.size - margin)]
    if peaks.size:
        ranked = sorted(peaks.tolist(), key=lambda i: (float(score[i]), float(fast_db[i])), reverse=True)
        selected = sorted(ranked[:max_events])
    else:
        selected = []
    event_samples = [max(0, int(round(i * sample_rate / analysis_rate - 0.004 * sample_rate))) for i in selected]
    diagnostics = {
        "events_detected": int(peaks.size),
        "events_used": len(event_samples),
        "analysis_rate_hz": analysis_rate,
        "detection_band_hz": [35.0, high],
        "minimum_spacing_ms": 85.0,
        "activity_floor_dbfs_proxy": activity_floor,
        "score_height_db": height,
        "selected_detector_scores_db": [float(score[i]) for i in selected],
        "proxy_note": "Strong broad-band full-master onsets; not drum-stem separation.",
    }
    return event_samples, diagnostics


def window_metrics(audio: np.ndarray, start: int, stop: int) -> Tuple[float, float]:
    block = audio[max(0, start):min(audio.shape[0], stop)]
    return peak_db(block), rms_db(block)


def percentile_or_none(values: Sequence[float], percentile: float) -> Optional[float]:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=np.float64), percentile))


def measure_drum_attack(
    reference: np.ndarray,
    candidate_matched: np.ndarray,
    sample_rate: int,
    event_samples: Sequence[int],
    detector: Dict[str, Any],
    warn_db: float,
    fail_db: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    pre_a = int(round(0.035 * sample_rate))
    pre_b = int(round(0.005 * sample_rate))
    attack_before = int(round(0.005 * sample_rate))
    attack_after = int(round(0.035 * sample_rate))
    sustain_a = int(round(0.045 * sample_rate))
    sustain_b = int(round(0.145 * sample_rate))
    rows: List[Dict[str, Any]] = []
    peak_deltas: List[float] = []
    rms_deltas: List[float] = []
    contrast_deltas: List[float] = []
    detector_scores = detector.get("selected_detector_scores_db", [])
    for number, event in enumerate(event_samples, start=1):
        if event - pre_a < 0 or event + sustain_b > reference.shape[0]:
            continue
        ref_pre_peak, ref_pre_rms = window_metrics(reference, event - pre_a, event - pre_b)
        cand_pre_peak, cand_pre_rms = window_metrics(candidate_matched, event - pre_a, event - pre_b)
        ref_attack_peak, ref_attack_rms = window_metrics(reference, event - attack_before, event + attack_after)
        cand_attack_peak, cand_attack_rms = window_metrics(candidate_matched, event - attack_before, event + attack_after)
        _, ref_sustain_rms = window_metrics(reference, event + sustain_a, event + sustain_b)
        _, cand_sustain_rms = window_metrics(candidate_matched, event + sustain_a, event + sustain_b)
        peak_delta = cand_attack_peak - ref_attack_peak
        attack_rms_delta = cand_attack_rms - ref_attack_rms
        contrast_delta = (cand_attack_peak - cand_sustain_rms) - (ref_attack_peak - ref_sustain_rms)
        peak_deltas.append(peak_delta)
        rms_deltas.append(attack_rms_delta)
        contrast_deltas.append(contrast_delta)
        rows.append({
            "event": number,
            "time_sec": event / sample_rate,
            "detector_score_db": detector_scores[number - 1] if number - 1 < len(detector_scores) else None,
            "reference_pre_rms_dbfs": ref_pre_rms,
            "candidate_pre_rms_dbfs_matched": cand_pre_rms,
            "reference_attack_peak_dbfs": ref_attack_peak,
            "candidate_attack_peak_dbfs_matched": cand_attack_peak,
            "attack_peak_delta_db": peak_delta,
            "reference_attack_rms_dbfs": ref_attack_rms,
            "candidate_attack_rms_dbfs_matched": cand_attack_rms,
            "attack_rms_delta_db": attack_rms_delta,
            "reference_attack_to_sustain_db": ref_attack_peak - ref_sustain_rms,
            "candidate_attack_to_sustain_db": cand_attack_peak - cand_sustain_rms,
            "attack_to_sustain_delta_db": contrast_delta,
            "reference_attack_to_pre_db": ref_attack_peak - ref_pre_rms,
            "candidate_attack_to_pre_db": cand_attack_peak - cand_pre_rms,
            "reference_pre_peak_dbfs": ref_pre_peak,
            "candidate_pre_peak_dbfs_matched": cand_pre_peak,
        })
    median_peak = percentile_or_none(peak_deltas, 50.0)
    median_rms = percentile_or_none(rms_deltas, 50.0)
    median_contrast = percentile_or_none(contrast_deltas, 50.0)
    guard_candidates = [value for value in (median_rms, median_contrast) if value is not None]
    guard_delta = min(guard_candidates) if guard_candidates else None
    if guard_delta is None:
        status = "FAIL"
        reason = "No reliable attack events were measured."
    elif guard_delta < fail_db:
        status = "FAIL"
        reason = "The matched attack guard is beyond the configured fail threshold."
    elif guard_delta < warn_db:
        status = "WARN"
        reason = "The matched attack guard is inside the review zone."
    else:
        status = "PASS"
        reason = "The matched attack guard is above the configured warning threshold."
    result: Dict[str, Any] = {
        "status": status,
        "reason": reason,
        "events_detected": detector.get("events_detected", 0),
        "events_used": len(rows),
        "attack_guard_delta_db": guard_delta,
        "attack_guard_definition": "minimum of median attack-RMS delta and median attack-to-sustain contrast delta",
        "median_attack_peak_delta_db": median_peak,
        "p10_attack_peak_delta_db": percentile_or_none(peak_deltas, 10.0),
        "p90_attack_peak_delta_db": percentile_or_none(peak_deltas, 90.0),
        "median_attack_rms_delta_db": median_rms,
        "median_attack_to_sustain_delta_db": median_contrast,
        "fraction_events_below_warn": float(np.mean(np.asarray(peak_deltas) < warn_db)) if peak_deltas else None,
        "fraction_events_below_fail": float(np.mean(np.asarray(peak_deltas) < fail_db)) if peak_deltas else None,
        "warning_threshold_db": warn_db,
        "fail_threshold_db": fail_db,
        "windows_ms": {"pre": [-35, -5], "attack": [-5, 35], "sustain": [45, 145]},
        "detector": {k: v for k, v in detector.items() if k != "selected_detector_scores_db"},
        "interpretation": "Negative delta means the candidate has less event attack after global active-RMS matching.",
        "human_guard": "A metric alert is evidence, not stem separation; audible punch/groove remains the stop criterion.",
    }
    return result, rows


def mono_retention_from_power(left_power: float, right_power: float, mono_power: float) -> Optional[float]:
    stereo_power = 0.5 * (left_power + right_power)
    if stereo_power <= 0.0:
        return None
    return 10.0 * math.log10(max(mono_power, 1e-30) / stereo_power)


def overall_mono_retention(audio: np.ndarray) -> Optional[float]:
    if audio.ndim < 2 or audio.shape[1] < 2:
        return None
    left = audio[:, 0].astype(np.float64)
    right = audio[:, 1].astype(np.float64)
    mid = 0.5 * (left + right)
    return mono_retention_from_power(float(np.mean(left * left)), float(np.mean(right * right)), float(np.mean(mid * mid)))


def correlation_lr(audio: np.ndarray) -> Optional[float]:
    if audio.ndim < 2 or audio.shape[1] < 2:
        return None
    left = audio[:, 0].astype(np.float64)
    right = audio[:, 1].astype(np.float64)
    denom = float(np.sqrt(np.sum(left * left) * np.sum(right * right)))
    return float(np.sum(left * right) / denom) if denom > 0.0 else None


def mono_retention_bands(audio: np.ndarray, sample_rate: int) -> Dict[str, Dict[str, Any]]:
    if audio.ndim < 2 or audio.shape[1] < 2:
        return {}
    left = audio[:, 0].astype(np.float64)
    right = audio[:, 1].astype(np.float64)
    mid = 0.5 * (left + right)
    nperseg = min(32768, max(4096, int(round(sample_rate * 0.68))))
    frequencies, left_psd = welch(left, fs=sample_rate, window="hann", nperseg=nperseg, noverlap=nperseg // 2, detrend=False)
    _, right_psd = welch(right, fs=sample_rate, window="hann", nperseg=nperseg, noverlap=nperseg // 2, detrend=False)
    _, mid_psd = welch(mid, fs=sample_rate, window="hann", nperseg=nperseg, noverlap=nperseg // 2, detrend=False)
    result: Dict[str, Dict[str, Any]] = {}
    powers: List[float] = []
    interim: List[Tuple[str, float, float, float, float, float]] = []
    nyquist = sample_rate * 0.5
    for name, low, high in MONO_BANDS:
        high_used = min(high, nyquist)
        mask = (frequencies >= low) & (frequencies < high_used)
        if not np.any(mask):
            continue
        left_power = float(np.trapezoid(left_psd[mask], frequencies[mask]))
        right_power = float(np.trapezoid(right_psd[mask], frequencies[mask]))
        mid_power = float(np.trapezoid(mid_psd[mask], frequencies[mask]))
        stereo_power = 0.5 * (left_power + right_power)
        powers.append(stereo_power)
        interim.append((name, low, high_used, left_power, right_power, mid_power))
    maximum_power = max(powers) if powers else 0.0
    for name, low, high, left_power, right_power, mid_power in interim:
        stereo_power = 0.5 * (left_power + right_power)
        reliable = bool(maximum_power > 0.0 and stereo_power >= maximum_power * 1e-4)
        result[name] = {
            "low_hz": low,
            "high_hz": high,
            "mono_retention_db": mono_retention_from_power(left_power, right_power, mid_power),
            "stereo_band_level_dbfs_proxy": 10.0 * math.log10(max(stereo_power, 1e-30)),
            "decision_reliable": reliable,
        }
    return result


def concatenate_event_windows(audio: np.ndarray, event_samples: Sequence[int], sample_rate: int) -> np.ndarray:
    before = int(round(0.025 * sample_rate))
    after = int(round(0.125 * sample_rate))
    blocks = [audio[event - before:event + after] for event in event_samples if event - before >= 0 and event + after <= audio.shape[0]]
    if not blocks:
        return np.empty((0, audio.shape[1]), dtype=audio.dtype)
    return np.concatenate(blocks, axis=0)


def classify_delta(delta: Optional[float], warn_db: float, fail_db: float) -> str:
    if delta is None:
        return "NOT_APPLICABLE"
    if delta < fail_db:
        return "FAIL"
    if delta < warn_db:
        return "WARN"
    return "PASS"


def measure_mono_loss(
    reference: np.ndarray,
    candidate_matched: np.ndarray,
    sample_rate: int,
    event_samples: Sequence[int],
    warn_db: float,
    fail_db: float,
) -> Dict[str, Any]:
    if reference.shape[1] < 2 or candidate_matched.shape[1] < 2:
        return {
            "status": "NOT_APPLICABLE",
            "reason": "Mono-loss analysis requires stereo reference and candidate WAV files.",
        }
    ref_overall = overall_mono_retention(reference)
    cand_overall = overall_mono_retention(candidate_matched)
    overall_delta = cand_overall - ref_overall if ref_overall is not None and cand_overall is not None else None
    ref_bands = mono_retention_bands(reference, sample_rate)
    cand_bands = mono_retention_bands(candidate_matched, sample_rate)
    bands: Dict[str, Dict[str, Any]] = {}
    decision_deltas: List[Tuple[str, float]] = []
    for name, _, _ in MONO_BANDS:
        if name not in ref_bands or name not in cand_bands:
            continue
        ref_value = ref_bands[name].get("mono_retention_db")
        cand_value = cand_bands[name].get("mono_retention_db")
        delta = cand_value - ref_value if ref_value is not None and cand_value is not None else None
        reliable = bool(ref_bands[name].get("decision_reliable") or cand_bands[name].get("decision_reliable"))
        status = classify_delta(delta, warn_db, fail_db) if reliable else "MEASURED"
        bands[name] = {
            "low_hz": ref_bands[name]["low_hz"],
            "high_hz": ref_bands[name]["high_hz"],
            "reference_mono_retention_db": ref_value,
            "candidate_mono_retention_db": cand_value,
            "candidate_minus_reference_db": delta,
            "decision_reliable": reliable,
            "status": status,
        }
        if reliable and delta is not None:
            decision_deltas.append((name, float(delta)))
    ref_events = concatenate_event_windows(reference, event_samples, sample_rate)
    cand_events = concatenate_event_windows(candidate_matched, event_samples, sample_rate)
    ref_event_retention = overall_mono_retention(ref_events) if ref_events.size else None
    cand_event_retention = overall_mono_retention(cand_events) if cand_events.size else None
    event_delta = cand_event_retention - ref_event_retention if ref_event_retention is not None and cand_event_retention is not None else None
    candidates: List[Tuple[str, float]] = []
    if overall_delta is not None:
        candidates.append(("overall", float(overall_delta)))
    candidates.extend(decision_deltas)
    if event_delta is not None:
        candidates.append(("drum_event_windows", float(event_delta)))
    worst_scope, worst_delta = min(candidates, key=lambda item: item[1]) if candidates else (None, None)
    status = classify_delta(worst_delta, warn_db, fail_db)
    reason = {
        "FAIL": "Additional mono cancellation exceeds the configured fail threshold.",
        "WARN": "Additional mono cancellation is inside the review zone.",
        "PASS": "No configured mono-loss threshold was crossed.",
        "NOT_APPLICABLE": "No comparable mono-retention value was available.",
    }.get(status, "Measured.")
    return {
        "status": status,
        "reason": reason,
        "definition": "10*log10(power((L+R)/2) / mean(power(L), power(R))); 0 dB is fully coherent center, more negative is less mono retention.",
        "overall": {
            "reference_mono_retention_db": ref_overall,
            "candidate_mono_retention_db": cand_overall,
            "candidate_minus_reference_db": overall_delta,
            "reference_lr_correlation": correlation_lr(reference),
            "candidate_lr_correlation": correlation_lr(candidate_matched),
        },
        "drum_event_windows": {
            "reference_mono_retention_db": ref_event_retention,
            "candidate_mono_retention_db": cand_event_retention,
            "candidate_minus_reference_db": event_delta,
            "events_used": len(event_samples),
        },
        "bands": bands,
        "worst_scope": worst_scope,
        "worst_candidate_minus_reference_db": worst_delta,
        "warning_threshold_db": warn_db,
        "fail_threshold_db": fail_db,
        "interpretation": "Negative candidate-minus-reference values mean extra loss on mono collapse.",
        "human_guard": "The meter cannot identify a specific guitar/vocal without stems; always audition the mono fold-down.",
    }


def run_command(command: Sequence[str], timeout: int = 600) -> Tuple[str, str]:
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()[-2000:]
        raise RuntimeError(f"Command failed ({process.returncode}): {' '.join(command)}\n{detail}")
    return process.stdout, process.stderr


def ffprobe_duration(path: Path) -> Optional[float]:
    out, _ = run_command([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], timeout=60)
    try:
        return float(out.strip())
    except ValueError:
        return None


def ffmpeg_true_peak(path: Path) -> Dict[str, Optional[float]]:
    _, err = run_command([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"
    ], timeout=600)
    import re

    peak_matches = re.findall(r"Peak:\s*([-+]?\d+(?:\.\d+)?)\s*dBFS", err)
    loudness_matches = re.findall(r"I:\s*([-+]?\d+(?:\.\d+)?)\s*LUFS", err)
    return {
        "true_peak_dbtp": float(peak_matches[-1]) if peak_matches else None,
        "integrated_lufs": float(loudness_matches[-1]) if loudness_matches else None,
    }


def encode_decode_codec(source: Path, codec_name: str, directory: Path) -> Tuple[Path, Path]:
    spec = CODEC_SPECS[codec_name]
    encoded = directory / f"{source.stem}.{codec_name}{spec['extension']}"
    decoded = directory / f"{source.stem}.{codec_name}.decoded.wav"
    encode = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
        "-map_metadata", "-1", "-vn", "-sn", "-dn", *spec["encode_args"], str(encoded),
    ]
    decode = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(encoded),
        "-map_metadata", "-1", "-vn", "-sn", "-dn", "-c:a", "pcm_f32le", str(decoded),
    ]
    run_command(encode)
    run_command(decode)
    return encoded, decoded


def measure_codecs(
    candidate_path: Path,
    source_duration: float,
    codecs: Sequence[str],
    outdir: Path,
    keep_files: bool,
    target_dbtp: Optional[float],
    safety_margin_db: float,
) -> Dict[str, Any]:
    if not codecs:
        return {"status": "NOT_APPLICABLE", "reason": "Codec audit was skipped.", "results": []}
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg and ffprobe are required for decoded codec peak audit")
    temporary: Optional[tempfile.TemporaryDirectory[str]] = None
    if keep_files:
        workdir = outdir / "codecs"
        workdir.mkdir(parents=True, exist_ok=True)
    else:
        temporary = tempfile.TemporaryDirectory(prefix="oz12_codec_")
        workdir = Path(temporary.name)
    results: List[Dict[str, Any]] = []
    try:
        for codec_name in codecs:
            encoded, decoded = encode_decode_codec(candidate_path, codec_name, workdir)
            peak_stats = ffmpeg_true_peak(decoded)
            _, decoded_audio, _ = load_wav(decoded)
            sample_peak = peak_db(decoded_audio)
            decoded_duration = ffprobe_duration(decoded)
            true_peak = peak_stats.get("true_peak_dbtp")
            if target_dbtp is None or true_peak is None:
                trim = None
                status = "MEASURED" if true_peak is not None else "FAIL"
            else:
                trim = max(0.0, true_peak - target_dbtp + safety_margin_db)
                status = "PASS" if trim <= 0.0 else "FAIL"
            results.append({
                "codec": codec_name,
                "label": CODEC_SPECS[codec_name]["label"],
                "status": status,
                "decoded_true_peak_dbtp": true_peak,
                "decoded_sample_peak_dbfs": sample_peak,
                "decoded_integrated_lufs": peak_stats.get("integrated_lufs"),
                "decoded_duration_sec": decoded_duration,
                "duration_delta_ms": (decoded_duration - source_duration) * 1000.0 if decoded_duration is not None else None,
                "target_dbtp": target_dbtp,
                "safety_margin_db": safety_margin_db if target_dbtp is not None else None,
                "recommended_source_trim_db": trim,
                "encoded_file": str(encoded) if keep_files else None,
                "decoded_file": str(decoded) if keep_files else None,
                "measurement": "FFmpeg ebur128 peak=true on explicit float decoded WAV",
            })
            del decoded_audio
    finally:
        if temporary is not None:
            temporary.cleanup()
    status = max((row["status"] for row in results), key=lambda item: STATUS_RANK.get(item, 0), default="NOT_APPLICABLE")
    return {
        "status": status,
        "target_dbtp": target_dbtp,
        "safety_margin_db": safety_margin_db if target_dbtp is not None else None,
        "keep_codec_files": keep_files,
        "results": results,
        "interpretation": "Each peak is measured after a real encode -> decode pass; codec-specific trim must be rechecked by another encode -> decode pass.",
    }


def source_metrics(path: Path, sample_rate: int, audio: np.ndarray, backend: str) -> Dict[str, Any]:
    return {
        "path": str(path),
        "sample_rate": sample_rate,
        "channels": int(audio.shape[1]),
        "duration_sec": audio.shape[0] / sample_rate,
        "load_backend": backend,
        "sample_peak_dbfs": peak_db(audio),
        "rms_dbfs": rms_db(audio),
    }


def worst_status(statuses: Iterable[str]) -> str:
    values = list(statuses)
    return max(values, key=lambda item: STATUS_RANK.get(item, 0), default="PASS")


def flatten_summary(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add(component: str, scope: str, metric: str, value: Any, unit: str, status: str, threshold: Any, note: str) -> None:
        rows.append({
            "component": component,
            "scope": scope,
            "metric": metric,
            "value": round_or_none(value),
            "unit": unit,
            "status": status,
            "threshold": threshold,
            "note": note,
        })

    attack = result["drum_attack"]
    add("drum_attack", "events", "attack_guard_delta", attack.get("attack_guard_delta_db"), "dB", attack["status"], f"warn<{attack['warning_threshold_db']}; fail<{attack['fail_threshold_db']}", attack.get("attack_guard_definition", "candidate minus reference after level match"))
    add("drum_attack", "events", "median_attack_peak_delta", attack.get("median_attack_peak_delta_db"), "dB", attack["status"], "informational", "candidate minus reference after level match")
    add("drum_attack", "events", "median_attack_rms_delta", attack.get("median_attack_rms_delta_db"), "dB", attack["status"], "informational", "candidate minus reference")
    add("drum_attack", "events", "median_attack_to_sustain_delta", attack.get("median_attack_to_sustain_delta_db"), "dB", attack["status"], "informational", "front-edge contrast delta")
    mono_loss = result["mono_loss"]
    overall = mono_loss.get("overall", {})
    add("mono_loss", "overall", "candidate_minus_reference", overall.get("candidate_minus_reference_db"), "dB", classify_delta(overall.get("candidate_minus_reference_db"), mono_loss.get("warning_threshold_db", -1.0), mono_loss.get("fail_threshold_db", -3.0)), "relative guard", "negative means extra mono loss")
    events = mono_loss.get("drum_event_windows", {})
    add("mono_loss", "drum_event_windows", "candidate_minus_reference", events.get("candidate_minus_reference_db"), "dB", classify_delta(events.get("candidate_minus_reference_db"), mono_loss.get("warning_threshold_db", -1.0), mono_loss.get("fail_threshold_db", -3.0)), "relative guard", "mono retention around detected attacks")
    for name, band in mono_loss.get("bands", {}).items():
        add("mono_loss", name, "candidate_minus_reference", band.get("candidate_minus_reference_db"), "dB", band.get("status", "MEASURED"), "relative guard", "negative means extra mono loss")
    for codec in result["decoded_codec_peaks"].get("results", []):
        add("decoded_codec_peak", codec["codec"], "decoded_true_peak", codec.get("decoded_true_peak_dbtp"), "dBTP", codec["status"], codec.get("target_dbtp"), "explicit encode -> decode")
        add("decoded_codec_peak", codec["codec"], "recommended_source_trim", codec.get("recommended_source_trim_db"), "dB", codec["status"], codec.get("safety_margin_db"), "re-encode and remeasure after trim")
    return rows


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: round_or_none(value, 6) for key, value in row.items()})


def md_value(value: Any, digits: int = 3) -> str:
    value = round_or_none(value, digits)
    return "n/a" if value is None else str(value)


def write_markdown(path: Path, result: Dict[str, Any]) -> None:
    attack = result["drum_attack"]
    mono_loss = result["mono_loss"]
    codecs = result["decoded_codec_peaks"]
    lines = [
        "# Automatic mastering meter\n",
        f"**Overall:** `{result['overall_status']}`  ",
        f"Reference: `{Path(result['reference']['path']).name}`  ",
        f"Candidate: `{Path(result['candidate']['path']).name}`  ",
        f"Alignment: {md_value(result['alignment']['candidate_lag_ms'])} ms; active-RMS match gain: {md_value(result['level_match_gain_db'])} dB\n",
        "## Drum attack\n",
        f"Status: `{attack['status']}`; events used: {attack['events_used']}.\n",
        "| Metric | Value |\n|---|---:|",
        f"| Attack guard delta | {md_value(attack.get('attack_guard_delta_db'))} dB |",
        f"| Median attack peak delta | {md_value(attack.get('median_attack_peak_delta_db'))} dB |",
        f"| P10 / P90 attack peak delta | {md_value(attack.get('p10_attack_peak_delta_db'))} / {md_value(attack.get('p90_attack_peak_delta_db'))} dB |",
        f"| Median attack RMS delta | {md_value(attack.get('median_attack_rms_delta_db'))} dB |",
        f"| Median attack-to-sustain delta | {md_value(attack.get('median_attack_to_sustain_delta_db'))} dB |\n",
        "> This is a strong broad-band onset proxy on the full master, not drum-stem separation. Audible punch/groove remains decisive.\n",
        "## Mono loss\n",
        f"Status: `{mono_loss['status']}`; worst scope: `{mono_loss.get('worst_scope')}`; worst candidate-minus-reference: {md_value(mono_loss.get('worst_candidate_minus_reference_db'))} dB.\n",
        "| Scope | Ref retention | Candidate retention | Delta | Status |\n|---|---:|---:|---:|---|",
    ]
    overall = mono_loss.get("overall", {})
    lines.append(f"| Overall | {md_value(overall.get('reference_mono_retention_db'))} | {md_value(overall.get('candidate_mono_retention_db'))} | {md_value(overall.get('candidate_minus_reference_db'))} | {classify_delta(overall.get('candidate_minus_reference_db'), mono_loss.get('warning_threshold_db', -1.0), mono_loss.get('fail_threshold_db', -3.0))} |")
    event_mono = mono_loss.get("drum_event_windows", {})
    lines.append(f"| Drum-event windows | {md_value(event_mono.get('reference_mono_retention_db'))} | {md_value(event_mono.get('candidate_mono_retention_db'))} | {md_value(event_mono.get('candidate_minus_reference_db'))} | {classify_delta(event_mono.get('candidate_minus_reference_db'), mono_loss.get('warning_threshold_db', -1.0), mono_loss.get('fail_threshold_db', -3.0))} |")
    for name, band in mono_loss.get("bands", {}).items():
        lines.append(f"| {name} | {md_value(band.get('reference_mono_retention_db'))} | {md_value(band.get('candidate_mono_retention_db'))} | {md_value(band.get('candidate_minus_reference_db'))} | {band.get('status')} |")
    lines.extend([
        "\n> Negative delta means additional mono loss relative to the reference. A specific disappearing guitar/vocal still requires mono audition or stems.\n",
        "## Decoded codec peaks\n",
        f"Status: `{codecs['status']}`.\n",
        "| Codec | Decoded TP | Sample peak | Duration delta | Recommended source trim | Status |\n|---|---:|---:|---:|---:|---|",
    ])
    for codec in codecs.get("results", []):
        lines.append(
            f"| {codec['label']} | {md_value(codec.get('decoded_true_peak_dbtp'))} dBTP | {md_value(codec.get('decoded_sample_peak_dbfs'))} dBFS | {md_value(codec.get('duration_delta_ms'))} ms | {md_value(codec.get('recommended_source_trim_db'))} dB | {codec['status']} |"
        )
    if not codecs.get("results"):
        lines.append("| skipped | n/a | n/a | n/a | n/a | NOT_APPLICABLE |")
    lines.extend([
        "\n## Decision guards\n",
        "- A `FAIL` is an automatic technical alert, not permission to identify a particular instrument from a stereo master.",
        "- For a drum-forward master, audible loss of punch/groove overrides a loudness target.",
        "- For width, mono audition is mandatory even when the numeric result passes.",
        "- If codec trim is applied, encode/decode and measure again.\n",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def analyze(
    reference_path: Path,
    candidate_path: Path,
    outdir: Path,
    codecs: Sequence[str],
    keep_codec_files: bool,
    max_events: int,
    max_lag_seconds: float,
    attack_warn_db: float,
    attack_fail_db: float,
    mono_warn_db: float,
    mono_fail_db: float,
    decoded_peak_target_dbtp: Optional[float],
    safety_margin_db: float,
) -> Dict[str, Any]:
    if not reference_path.exists() or not candidate_path.exists():
        missing = [str(path) for path in (reference_path, candidate_path) if not path.exists()]
        raise FileNotFoundError("Missing input: " + ", ".join(missing))
    if attack_fail_db > attack_warn_db:
        raise ValueError("attack fail threshold must be <= warning threshold")
    if mono_fail_db > mono_warn_db:
        raise ValueError("mono fail threshold must be <= warning threshold")
    outdir.mkdir(parents=True, exist_ok=True)
    ref_rate, reference, ref_backend = load_wav(reference_path)
    cand_rate, candidate, cand_backend = load_wav(candidate_path)
    original_candidate_metrics = source_metrics(candidate_path, cand_rate, candidate, cand_backend)
    if cand_rate != ref_rate:
        candidate = resample_audio(candidate, cand_rate, ref_rate)
    channels = min(reference.shape[1], candidate.shape[1])
    reference = reference[:, :channels]
    candidate = candidate[:, :channels]
    alignment = estimate_alignment(reference, candidate, ref_rate, max_lag_seconds)
    reference_aligned, candidate_aligned = align_pair(reference, candidate, int(alignment["candidate_lag_samples"]))
    candidate_matched, match_gain_db = level_match(reference_aligned, candidate_aligned, ref_rate)
    event_samples, detector = detect_drum_attack_events(reference_aligned, ref_rate, max_events)
    attack, event_rows = measure_drum_attack(
        reference_aligned, candidate_matched, ref_rate, event_samples, detector, attack_warn_db, attack_fail_db
    )
    mono_loss = measure_mono_loss(
        reference_aligned, candidate_matched, ref_rate, event_samples, mono_warn_db, mono_fail_db
    )
    codec_result = measure_codecs(
        candidate_path,
        float(original_candidate_metrics["duration_sec"]),
        codecs,
        outdir,
        keep_codec_files,
        decoded_peak_target_dbtp,
        safety_margin_db,
    )
    overall_status = worst_status([attack["status"], mono_loss["status"], codec_result["status"]])
    result: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "reference": source_metrics(reference_path, ref_rate, reference, ref_backend),
        "candidate": original_candidate_metrics,
        "analysis": {
            "analysis_sample_rate": ref_rate,
            "aligned_duration_sec": reference_aligned.shape[0] / ref_rate,
            "channels_compared": channels,
            "candidate_resampled_for_comparison": cand_rate != ref_rate,
        },
        "alignment": alignment,
        "level_match_gain_db": match_gain_db,
        "drum_attack": attack,
        "mono_loss": mono_loss,
        "decoded_codec_peaks": codec_result,
    }
    result = json.loads(json.dumps(result, default=lambda value: float(value) if isinstance(value, np.generic) else value))
    (outdir / "mastering_meter.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(
        outdir / "mastering_meter.csv",
        flatten_summary(result),
        ["component", "scope", "metric", "value", "unit", "status", "threshold", "note"],
    )
    event_fields = [
        "event", "time_sec", "detector_score_db", "reference_pre_rms_dbfs", "candidate_pre_rms_dbfs_matched",
        "reference_attack_peak_dbfs", "candidate_attack_peak_dbfs_matched", "attack_peak_delta_db",
        "reference_attack_rms_dbfs", "candidate_attack_rms_dbfs_matched", "attack_rms_delta_db",
        "reference_attack_to_sustain_db", "candidate_attack_to_sustain_db", "attack_to_sustain_delta_db",
        "reference_attack_to_pre_db", "candidate_attack_to_pre_db", "reference_pre_peak_dbfs",
        "candidate_pre_peak_dbfs_matched",
    ]
    write_csv(outdir / "drum_attack_events.csv", event_rows, event_fields)
    write_markdown(outdir / "mastering_meter_report.md", result)
    return result


def synth_drum(sample_rate: int, length: int, start: int, attack_scale: float) -> np.ndarray:
    count = min(length - start, int(round(0.180 * sample_rate)))
    if count <= 0:
        return np.zeros(length, dtype=np.float32)
    t = np.arange(count, dtype=np.float64) / sample_rate
    kick = np.sin(2.0 * np.pi * (70.0 - 25.0 * np.minimum(t / 0.18, 1.0)) * t) * np.exp(-t * 20.0)
    snare = np.sin(2.0 * np.pi * 190.0 * t) * np.exp(-t * 32.0)
    click = np.sin(2.0 * np.pi * 4200.0 * t) * np.exp(-t * 110.0)
    hit = 0.55 * kick + 0.24 * snare + 0.16 * click
    attack_count = min(count, int(round(0.030 * sample_rate)))
    hit[:attack_count] *= attack_scale
    out = np.zeros(length, dtype=np.float32)
    out[start:start + count] = hit.astype(np.float32)
    return out


def run_self_test() -> int:
    sample_rate = 48000
    duration = 5.0
    length = int(sample_rate * duration)
    t = np.arange(length, dtype=np.float64) / sample_rate
    centered_bed = 0.025 * np.sin(2.0 * np.pi * 220.0 * t)
    reference_mono = centered_bed.copy()
    candidate_mono = centered_bed.copy()
    for when in [0.50, 1.05, 1.60, 2.15, 2.70, 3.25, 3.80, 4.35]:
        start = int(round(when * sample_rate))
        reference_mono += synth_drum(sample_rate, length, start, 1.0)
        candidate_mono += synth_drum(sample_rate, length, start, 0.50)
    side_tone = 0.085 * np.sin(2.0 * np.pi * 6200.0 * t)
    reference = np.column_stack([reference_mono, reference_mono]).astype(np.float32)
    candidate = np.column_stack([candidate_mono + side_tone, candidate_mono - side_tone]).astype(np.float32)
    peak = max(float(np.max(np.abs(reference))), float(np.max(np.abs(candidate))))
    reference *= np.float32(0.85 / max(peak, 1e-9))
    candidate *= np.float32(0.85 / max(peak, 1e-9))
    with tempfile.TemporaryDirectory(prefix="oz12_meter_selftest_") as temp:
        directory = Path(temp)
        ref_path = directory / "reference.wav"
        cand_path = directory / "candidate.wav"
        outdir = directory / "report"
        wavfile.write(str(ref_path), sample_rate, reference)
        wavfile.write(str(cand_path), sample_rate, candidate)
        result = analyze(
            ref_path, cand_path, outdir, list(CODEC_SPECS), False, 32, 0.25,
            -0.5, -1.0, -1.0, -3.0, -1.0, 0.1,
        )
        attack_delta = result["drum_attack"].get("attack_guard_delta_db")
        mono_delta = result["mono_loss"].get("worst_candidate_minus_reference_db")
        codecs = result["decoded_codec_peaks"].get("results", [])
        assert attack_delta is not None and attack_delta < -1.0, result["drum_attack"]
        assert mono_delta is not None and mono_delta < -3.0, result["mono_loss"]
        assert len(codecs) == 3 and all(row.get("decoded_true_peak_dbtp") is not None for row in codecs), codecs
        for name in ["mastering_meter.json", "mastering_meter.csv", "drum_attack_events.csv", "mastering_meter_report.md"]:
            assert (outdir / name).is_file(), name
        print("SELF-TEST PASS")
        print(json.dumps({
            "overall_status": result["overall_status"],
            "attack_delta_db": round_or_none(attack_delta),
            "worst_mono_delta_db": round_or_none(mono_delta),
            "decoded_true_peaks_dbtp": {row["codec"]: row["decoded_true_peak_dbtp"] for row in codecs},
        }, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reference", type=Path, help="Reference/base WAV")
    parser.add_argument("--candidate", type=Path, help="Candidate/final WAV")
    parser.add_argument("--outdir", type=Path, help="Directory for JSON/CSV/Markdown reports")
    parser.add_argument("--max-events", type=int, default=128, help="Maximum strongest onset events to compare")
    parser.add_argument("--max-lag-seconds", type=float, default=2.0, help="Maximum automatic alignment lag")
    parser.add_argument("--attack-warn-db", type=float, default=-0.5)
    parser.add_argument("--attack-fail-db", type=float, default=-1.0)
    parser.add_argument("--mono-warn-db", type=float, default=-1.0, help="Additional mono-loss delta vs reference")
    parser.add_argument("--mono-fail-db", type=float, default=-3.0, help="Additional mono-loss delta vs reference")
    parser.add_argument("--decoded-peak-target-dbtp", type=float, default=None, help="Optional delivery target; omitted means measure-only")
    parser.add_argument("--safety-margin-db", type=float, default=0.1)
    parser.add_argument("--codecs", nargs="+", choices=sorted(CODEC_SPECS), default=list(CODEC_SPECS), help="Codec variants to encode/decode")
    parser.add_argument("--skip-codecs", action="store_true", help="Skip encode/decode audit for a fast stage check")
    parser.add_argument("--keep-codec-files", action="store_true", help="Keep encoded and decoded audit files under OUTDIR/codecs")
    parser.add_argument("--strict", action="store_true", help="Return exit code 3 when overall status is FAIL")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic synthetic regression test")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.self_test:
        return run_self_test()
    if args.reference is None or args.candidate is None or args.outdir is None:
        parser.error("--reference, --candidate and --outdir are required unless --self-test is used")
    codecs: Sequence[str] = [] if args.skip_codecs else args.codecs
    result = analyze(
        args.reference,
        args.candidate,
        args.outdir,
        codecs,
        args.keep_codec_files,
        args.max_events,
        args.max_lag_seconds,
        args.attack_warn_db,
        args.attack_fail_db,
        args.mono_warn_db,
        args.mono_fail_db,
        args.decoded_peak_target_dbtp,
        args.safety_margin_db,
    )
    print(f"OK: {args.outdir}")
    print(f"overall_status={result['overall_status']}")
    print(f"drum_attack={result['drum_attack']['status']} guard_delta_db={round_or_none(result['drum_attack'].get('attack_guard_delta_db'))}")
    print(f"mono_loss={result['mono_loss']['status']} worst_delta_db={round_or_none(result['mono_loss'].get('worst_candidate_minus_reference_db'))}")
    codec_values = {row["codec"]: row.get("decoded_true_peak_dbtp") for row in result["decoded_codec_peaks"].get("results", [])}
    print("decoded_codec_peaks_dbtp=" + json.dumps(codec_values, sort_keys=True))
    if args.strict and result["overall_status"] == "FAIL":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
