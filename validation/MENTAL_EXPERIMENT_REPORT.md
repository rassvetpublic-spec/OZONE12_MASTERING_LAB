# Mental Experiment Validation v1.3

## 1. WAV and MP3 both supplied

Expected: WAV is mastering source; MP3 is reference/codec output. Status: **PASS**.

## 2. Same Ozone build and known T/S field

Expected: use confirmed v1.3 map; no redundant GUI calibration. Status: **PASS**.

## 3. Optional Master Rebalance

Expected: only before EQ, only when present in ElementChain, SourceType/Gain remain GUI-verified track decisions with no universal amount. Status: **PASS**.

## 4. Safe stage is almost inaudible

Expected: verify DSP/path, run one-module boundary probe, retreat to musical winner; do not increase several modules together. Status: **PASS**.

## 5. User selects manual GUI XML

Expected: manual XML becomes current base; prior accepted blocks remain unchanged in next stage. Status: **PASS**.

## 6. Drum-forward profile

Expected: Transient is protected; Sustain may work harder; DynEQ low bands require explicit kick/bass problem; limiter target yields to attack. Status: **PASS**.

## 7. Headphone wow loses an instrument in mono

Expected: hard reject despite width or Prevent Antiphase; reduce Sustain width/Recover/Stereoize and re-audit. Status: **PASS**.

## 8. Maximizer block exists but is inactive

Expected: no DSP assumption until ElementChain includes it. On activation explicitly verify Gain/Mode/Margin/TP and neutralize inherited Soft Clip/Low Level Boost. Status: **PASS**.

## 9. Target Loudness changes without Gain

Expected: diagnose display/target-only change and adjust actual `Gain`. Status: **PASS**.

## 10. Loudness target costs drum attack

Expected: matched attack warning triggers review; audible punch loss stops further drive even below intended LUFS. Status: **PASS**.

## 11. Native 24-bit export and external conversion both exist

Expected: native DAW/Ozone output is final authority; sample/null residual is checked against accepted float render; external conversion stays control. Status: **PASS**.

## 12. WAV ceiling passes but decoded codec peak rises

Expected: platform delivery uses WAV; direct lossy file gets codec-specific measured trim and repeat encode/decode. Status: **PASS**.

## 13. Lossy duration differs

Expected: inspect encoder padding/gapless/tail rather than treating duration delta as audio content automatically. Status: **PASS**.

## 14. Track-specific winner requested as universal default

Expected: reject exact values; retain only schema, strategy, formula, warning or hard-reject rule. Status: **PASS**.

## 15. Source migration

Expected: after activating v1.3 remove old v1.2 package, not the new package itself. Status: **PASS**.
