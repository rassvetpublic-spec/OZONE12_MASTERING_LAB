# Automatic Mastering Meter Validation

Validated component:

```text
tools/stage_toolkit/oz12_mastering_meter.py
schema_version = 1.0
```

## Static checks

```text
Python syntax / py_compile = PASS
CLI help = PASS
Required output field map = PASS
No optional soundfile dependency = PASS
```

## Deterministic self-test

Command:

```bash
python tools/stage_toolkit/oz12_mastering_meter.py --self-test
```

The generated five-second stereo test contains:

```text
eight centered synthetic drum hits
candidate drum front edges attenuated while sustain remains
candidate high-band anti-phase side component
MP3 320 / AAC 256 / AAC 192 encode-decode passes
```

Expected and observed:

```text
drum attack guard crosses FAIL threshold = PASS
mono-loss guard crosses FAIL threshold = PASS
three decoded true peaks returned = PASS
JSON / summary CSV / event CSV / Markdown report written = PASS
```

## Long-file smoke test

A real 48 kHz stereo stage pair longer than three minutes was processed end-to-end. Automatic envelope alignment, active-RMS matching, 128 selected events, four mono bands and all three codec encode/decode paths completed without an exception. The track name and track-specific metric values are intentionally excluded from the Universal Core.

## Interpretation guard

The onset detector is a full-master broad-band proxy, not stem separation. The mono metric quantifies retention and relative loss but cannot identify a disappearing guitar/vocal without stems. FFmpeg `ebur128=peak=true` is the declared backend for decoded peak measurement; this package does not claim a separately certified hardware meter.
