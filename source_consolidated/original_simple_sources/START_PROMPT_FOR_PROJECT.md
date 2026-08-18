# Стартовый промпт для следующего анализа

```text
Работай в рамках OZONE12_MASTERING_LAB.
Сначала найди и используй источник OZONE12_STAGE_TOOLKIT_v1 / ozone12_stage_toolkit.
Если нужно анализировать новые WAV-рендеры, используй логику tools/oz12_analyze_stage.py: metrics.csv, sample_identity.csv, band_deltas.csv, mid_side_deltas.csv, decision_draft.md.
Если нужно проверять Ozone XML, используй логику tools/oz12_xml_audit.py: ElementChain, xml_chain.csv, xml_param_diffs.csv, xml_audit.md.
Не работай по Enabled=1; активная цепь только через Global/ExtraBytes ElementID="ElementChain".
Для Dirty Vibe текущая пересборка идёт от Bass C и safe-order: EQ → Impact → Clarity → Stabilizer → Stereo Imager → Dynamic EQ → Maximizer.
Maximizer менять через Gain, не только Target Loudness.
Stabilizer проверять через Transient/Sustain и TameTransients.
Дай краткий отчёт, файлы CSV/MD и решение: WINNER/FALLBACK/NEXT_STAGE_BASE.
```
