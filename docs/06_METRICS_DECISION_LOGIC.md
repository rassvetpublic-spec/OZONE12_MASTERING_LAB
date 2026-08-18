# 06. Metrics and Decision Logic

## Минимальные метрики

```text
LUFS-I and short-term
LRA
sample peak and true peak
RMS and crest
event-aligned transient attack
L/R correlation
Side/Mid overall and by relevant band
sample-aligned mono/mid stability
normalized spectral delta
sample identity / rms_diff / max_abs_diff
duration, encoder padding and silent tail
```

## Decision order

1. Hard technical rejects: invalid XML, clipping, broken ElementChain, obvious mono cancellation, wrong export format.
2. Musical intent: vocal/drums/groove/tone/width.
3. Loudness-matched preference.
4. Metrics as evidence and risk detector.
5. Codec behaviour for final delivery.

Слуховое замечание пользователя важнее technical winner; rejected musical candidate может остаться backup, но не final.

## Audibility gate

Если stage почти не отличается:

```text
проверить active chain и DSP ParamID
включить Delta/Gain Match
сделать один-module boundary probe
подтвердить направление эффекта
отступить к минимально достаточному winner
```

Не усиливать одновременно несколько модулей: это разрушает причинность.

## Drum transient guard

В drum-forward мастере сравнивать одинаковые события после loudness match. Потеря median attack порядка `0.5–1.0 dB` — предупреждение; слышимая потеря punch/groove — stop независимо от LUFS. Одновременно сохранять macro LRA и short-time crest.

`oz12_mastering_meter.py` автоматически time-aligns reference/candidate, делает analysis-only active-RMS match и измеряет одинаковые strong onset events. Primary guard — худшее из median attack-RMS delta и median attack-to-sustain delta. Raw peak остаётся диагностикой: steady side/high content может поднять peak, не сохранив drum front edge.

## Stereo guard

Wide candidate принимается только если важные элементы остаются в mono и не наблюдается опасного band-specific Side/Mid/correlation shift. `Prevent Antiphase` — не результат аудита.

Automatic mono guard сравнивает candidate с reference overall, вокруг drum events и в полосах `20–120`, `120–500`, `500–4000`, `4000–18000 Hz`. Negative candidate-minus-reference mono-retention delta означает дополнительную потерю. Numeric PASS не отменяет обязательного mono listening: без stems измеритель не может назвать исчезающую гитару или vocal.

## Reproducible meter

```bash
python tools/stage_toolkit/oz12_mastering_meter.py \
  --reference "BASE.wav" \
  --candidate "CANDIDATE.wav" \
  --outdir "reports/meter" \
  --skip-codecs
```

Пороговые defaults являются configurable review heuristics. Поля и формулы: `docs/15_AUTOMATIC_MASTERING_METER.md` и `tables/OZONE12_MASTERING_METER_FIELDS_v1_3.csv`.

## Auto reference

Auto можно использовать как reference по громкости, открытости и ширине, но его active chain и risk settings должны быть прочитаны. Auto не является автоматически ни winner, ни безопасным preset.
