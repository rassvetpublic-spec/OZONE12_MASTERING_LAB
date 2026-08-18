# Roadmap

## R0 — Repository foundation

- [x] Выделить отдельный private GitHub repository.
- [x] Перенести Universal Core v1.3 как редактируемые исходники.
- [x] Зафиксировать process-only scope и validation workflow.
- [x] Review и merge initial import PR.
- [x] Зафиксировать runtime architecture v1 и обязательный P0 Gate.

## R1 — Mandatory P0 backend qualification

- [x] P0.0 Environment Lock: Windows/REAPER/Ozone/Python/render baseline.
- [x] Реализовать autonomous P0 evaluator, evidence contract и negative self-test.
- [x] Реализовать единый PowerShell entry point и external workspace initializer.
- [x] Реализовать safe P0.1 command-line render runner без FX.
- [ ] P0.1 Dry Harness: минимум три D0 renders без Ozone.
- [ ] P0.2 L0 manual GUI/XML Oracle for S0/S1/S2.
- [ ] P0.3 L1 Frozen RPP.
- [ ] P0.4 L2 full VST3 state from `.vstpreset`.
- [ ] P0.5 L3 full Base64 `vst_chunk` read/write.
- [ ] P0.6 L4 one published parameter control.
- [ ] P0.7 selected-backend repeatability, S2 and negative Render Gate.

R1 exit criteria:

```text
Dry Harness baseline established
AND L2 or L3 qualified against L0 on S0/S1/S2
AND three selected-backend self-repeats pass
AND wrong hash / API false / readback mismatch create 0 WAV
```

Без R1 exit PASS production web-controlled render и automatic stage runner не реализуются.

## R2 — Local runtime foundation

- [ ] External local session schema; immutable inputs and winners.
- [ ] SQLite state/jobs/checkpoints.
- [ ] Environment health/status page.
- [ ] Crash recovery, idempotent jobs and resume from previous winner.
- [ ] Manual localhost web UI.

## R3 — REAPER render and guided stages

- [ ] Exclusive REAPER worker and mandatory pre-render readback.
- [ ] Quick/full render with declared range, pre-roll and tail.
- [ ] Safe/Probe/Refine candidate generation.
- [ ] Stage-by-stage cumulative chain from immutable source WAV.
- [ ] Synchronized gain-matched A/B and mono controls.
- [ ] Existing XML/audio/meter reports integrated into UI.

## R4 — Real-world validation

- [ ] Validate automatic meter on external reference/candidate pairs.
- [ ] Compare pre-Maximizer → native final.
- [ ] MP3 320 / AAC 256 / AAC 192 encode→decode audit.
- [ ] Calibrate warning/fail heuristics against loudness-matched listening.
- [ ] Promote only anonymized transferable procedures/warnings/hard rejects.

Session audio, titles, exact XML, metrics and subjective notes remain outside repository.

## R5 — ChatGPT/OpenAI review

- [ ] Manual `CHATGPT_REVIEW_PACK` and validated decision import.
- [ ] Synthetic/non-sensitive OpenAI audio sandbox.
- [ ] Verify availability, cost, limits, privacy/retention and failure handling.
- [ ] Structured decision schema with local hard-gate veto.

## R6 — Autopilot

- [ ] Automatic multi-stage execution after P0 and real-world validation.
- [ ] Mandatory stop on state mismatch, hard reject or low confidence.
- [ ] One-click technical final candidate with human release approval.
- [ ] Optional Master Assistant UI automation only after separate deterministic qualification.

## R7 — Universal knowledge curation

- [ ] Extract only reusable schema/procedure/formula/warning/hard reject.
- [ ] Remove session identifiers and per-session numbers before publication.
- [ ] Never promote a single winner into a universal default.
- [ ] Version frozen Sources package separately from live repository architecture.
