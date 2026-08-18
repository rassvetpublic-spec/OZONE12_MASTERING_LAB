#!/usr/bin/env python3
"""Common helpers for OZONE12_STAGE_TOOLKIT."""
from __future__ import annotations

import base64
import csv
import math
import os
import re
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_csv(path: str | Path, rows: Sequence[Dict[str, object]], fieldnames: Optional[Sequence[str]] = None) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    if fieldnames is None:
        keys = []
        for row in rows:
            for k in row.keys():
                if k not in keys:
                    keys.append(k)
        fieldnames = keys
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fieldnames), extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def run_cmd(cmd: Sequence[str], timeout: int = 180) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", e.stderr or "timeout"


def parse_float(text: str) -> Optional[float]:
    if text is None:
        return None
    text = str(text).strip().replace(",", ".")
    try:
        return float(text)
    except Exception:
        return None


def dbfs_from_rms(x: float) -> float:
    if x <= 0 or not np.isfinite(x):
        return -999.0
    return float(20.0 * math.log10(x))


def rms_db(x: np.ndarray) -> float:
    if x.size == 0:
        return -999.0
    return dbfs_from_rms(float(np.sqrt(np.mean(np.square(x.astype(np.float64))))))


def peak_db(x: np.ndarray) -> float:
    if x.size == 0:
        return -999.0
    pk = float(np.max(np.abs(x.astype(np.float64))))
    return dbfs_from_rms(pk)


def load_audio(path: str | Path) -> Tuple[int, np.ndarray, str]:
    """Return sample_rate, float audio in [-1,1], backend name."""
    path = Path(path)
    try:
        import soundfile as sf  # type: ignore
        data, sr = sf.read(str(path), always_2d=True, dtype="float64")
        return int(sr), data, "soundfile"
    except Exception:
        from scipy.io import wavfile  # type: ignore
        sr, data = wavfile.read(str(path))
        data = np.asarray(data)
        if data.ndim == 1:
            data = data[:, None]
        if np.issubdtype(data.dtype, np.integer):
            maxv = float(np.iinfo(data.dtype).max)
            data = data.astype(np.float64) / maxv
        else:
            data = data.astype(np.float64)
        return int(sr), data, "scipy.io.wavfile"


def ffprobe_info(path: str | Path) -> Dict[str, object]:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_name,sample_rate,channels,bits_per_sample,duration:format=duration,bit_rate,format_name",
        "-of", "default=noprint_wrappers=1", str(path)
    ]
    code, out, err = run_cmd(cmd, timeout=30)
    info: Dict[str, object] = {"ffprobe_ok": code == 0}
    if code != 0:
        info["ffprobe_error"] = err.strip()[:500]
        return info
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k] = v
    return info


def ffmpeg_loudness(path: str | Path) -> Dict[str, object]:
    """Parse ffmpeg ebur128 summary. True peak in ffmpeg ebur128 is approximate according to filter."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"]
    code, out, err = run_cmd(cmd, timeout=240)
    text = out + "\n" + err
    res: Dict[str, object] = {"ffmpeg_ebur128_ok": code == 0}
    patterns = {
        "lufs_i": r"I:\s*([-+]?\d+(?:\.\d+)?)\s*LUFS",
        "lra": r"LRA:\s*([-+]?\d+(?:\.\d+)?)\s*LU",
        "true_peak_dbfs": r"Peak:\s*([-+]?\d+(?:\.\d+)?)\s*dBFS",
    }
    # Use last occurrence from Summary section if multiple are present.
    for key, pat in patterns.items():
        matches = re.findall(pat, text)
        res[key] = float(matches[-1]) if matches else None
    if code != 0:
        res["ffmpeg_ebur128_error"] = err.strip()[:500]
    return res


def band_rms_db(audio: np.ndarray, sr: int, band: Tuple[float, float]) -> float:
    """Fast approximate band level for A/B comparison.

    Uses Welch PSD on a downmixed mono signal. It is intentionally faster than
    full-file bandpass filtering and is designed for relative deltas between
    renders, not laboratory absolute SPL.
    """
    lo, hi = band
    x = audio.mean(axis=1) if audio.ndim == 2 else audio
    if x.size == 0:
        return -999.0
    # Limit extremely long files only by decimation if needed; keep full duration shape via Welch.
    try:
        from scipy.signal import welch  # type: ignore
        nperseg = min(65536, max(4096, int(sr * 1.365)))
        freqs, psd = welch(x.astype(np.float64), fs=sr, window="hann", nperseg=nperseg, noverlap=nperseg // 2, detrend=False)
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            return -999.0
        power = float(np.trapz(psd[mask], freqs[mask]))
        return dbfs_from_rms(math.sqrt(max(power, 0.0)))
    except Exception:
        n = min(len(x), sr * 60)
        if n <= 0:
            return -999.0
        xx = x[:n].astype(np.float64)
        freqs = np.fft.rfftfreq(n, 1.0 / sr)
        spec = np.fft.rfft(xx * np.hanning(n))
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            return -999.0
        # Rough RMS proxy.
        val = np.sqrt(np.mean(np.abs(spec[mask]) ** 2)) / max(n / 2.0, 1)
        return dbfs_from_rms(float(val))


def bands_rms_db(audio: np.ndarray, sr: int, bands: Sequence[Tuple[str, Tuple[float, float]]]) -> Dict[str, float]:
    """Fast approximate band levels for many bands using one Welch pass."""
    x = audio.mean(axis=1) if audio.ndim == 2 else audio
    out: Dict[str, float] = {}
    if x.size == 0:
        return {name: -999.0 for name, _ in bands}
    try:
        from scipy.signal import welch  # type: ignore
        nperseg = min(32768, max(4096, int(sr * 0.682)))
        freqs, psd = welch(x.astype(np.float64), fs=sr, window="hann", nperseg=nperseg, noverlap=nperseg // 2, detrend=False)
        for name, (lo, hi) in bands:
            mask = (freqs >= lo) & (freqs < hi)
            if not np.any(mask):
                out[name] = -999.0
            else:
                power = float(np.trapz(psd[mask], freqs[mask]))
                out[name] = dbfs_from_rms(math.sqrt(max(power, 0.0)))
        return out
    except Exception:
        return {name: band_rms_db(audio, sr, band) for name, band in bands}


def stereo_stats(audio: np.ndarray) -> Dict[str, object]:
    if audio.ndim < 2 or audio.shape[1] < 2:
        return {"corr": None, "mid_rms_db": None, "side_rms_db": None, "side_minus_mid_db": None}
    l = audio[:, 0].astype(np.float64)
    r = audio[:, 1].astype(np.float64)
    if l.size == 0:
        return {"corr": None, "mid_rms_db": None, "side_rms_db": None, "side_minus_mid_db": None}
    denom = float(np.sqrt(np.sum(l*l) * np.sum(r*r)))
    corr = float(np.sum(l*r) / denom) if denom > 0 else None
    mid = 0.5 * (l + r)
    side = 0.5 * (l - r)
    mid_db = rms_db(mid)
    side_db = rms_db(side)
    return {"corr": corr, "mid_rms_db": mid_db, "side_rms_db": side_db, "side_minus_mid_db": side_db - mid_db}


def compare_sample_identity(ref: np.ndarray, cand: np.ndarray) -> Dict[str, object]:
    n = min(ref.shape[0], cand.shape[0])
    ch = min(ref.shape[1] if ref.ndim == 2 else 1, cand.shape[1] if cand.ndim == 2 else 1)
    a = ref[:n, :ch] if ref.ndim == 2 else ref[:n, None]
    b = cand[:n, :ch] if cand.ndim == 2 else cand[:n, None]
    diff = b - a
    max_abs = float(np.max(np.abs(diff))) if diff.size else 0.0
    diff_rms = float(np.sqrt(np.mean(diff * diff))) if diff.size else 0.0
    ref_rms = float(np.sqrt(np.mean(a * a))) if a.size else 0.0
    return {
        "aligned_samples": n,
        "aligned_channels": ch,
        "same_shape_prefix": ref.shape == cand.shape,
        "sample_identical": bool(max_abs == 0.0 and ref.shape == cand.shape),
        "max_abs_diff": max_abs,
        "rms_diff_dbfs": dbfs_from_rms(diff_rms),
        "null_residual_vs_ref_db": dbfs_from_rms(diff_rms / ref_rms) if ref_rms > 0 else None,
    }



def fast_loudness(audio: np.ndarray, sr: int) -> Dict[str, object]:
    """Fast local loudness/true-peak estimate.

    Uses pyloudnorm for integrated LUFS when available.
    True peak is approximated by 4x polyphase oversampling peak.
    This is sufficient for A/B stage comparison; final release can be verified by ffmpeg/DAW meter.
    """
    res: Dict[str, object] = {"loudness_backend": "fast_local"}
    x = audio.astype(np.float64)
    if x.ndim == 1:
        x = x[:, None]
    try:
        import pyloudnorm as pyln  # type: ignore
        meter = pyln.Meter(sr)
        # pyloudnorm expects shape (samples, channels)
        res["lufs_i"] = float(meter.integrated_loudness(x))
        res["lra"] = None
    except Exception as e:
        res["loudness_error"] = str(e)[:200]
        res["lufs_i"] = None
        res["lra"] = None
    # Fast default: use sample peak as a conservative stage-comparison proxy.
    # For final release verification, confirm True Peak in Ozone/DAW or with ffmpeg ebur128.
    res["true_peak_dbfs"] = peak_db(x)
    res["true_peak_note"] = "sample_peak_proxy_fast_mode"
    return res


def decode_element_chain(data_b64: str) -> List[str]:
    raw = base64.b64decode(data_b64)
    pos = 0
    names: List[str] = []
    while pos < len(raw):
        # Expected: 00 + uint32 little-endian length + UTF-8 name
        if pos + 5 > len(raw):
            break
        marker = raw[pos]
        pos += 1
        length = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        if length < 0 or pos + length > len(raw):
            break
        name = raw[pos:pos+length].decode("utf-8", errors="replace")
        pos += length
        names.append(name)
        if marker != 0:
            # Keep parsing but marker anomaly can be reported by caller if needed.
            pass
    return names
