# 14. Validated Stage and Finalization Lessons

Этот документ фиксирует переносимые выводы последовательного XML→render→A/B→mono→codec workflow. Он не содержит названий треков и не превращает частные настройки в defaults.

## 1. Audibility and causality

- Correct XML mapping не гарантирует слышимого результата.
- Если candidate почти не отличается, сначала проверить active chain/ParamID/render, затем сделать extreme one-module probe.
- После подтверждения направления отступить к минимально достаточному значению.
- Одновременное усиление нескольких модулей запрещено: оно скрывает причинность.

## 2. Current winner is the base

- GUI-saved manual winner выше предыдущего generated candidate для текущего трека.
- Каждый следующий patch должен сохранять предыдущие accepted module blocks и unknown data.
- Diff scope — часть доказательства, а не формальность.

## 3. Drum-forward mastering

- Если groove держится на живых ударных, Transient branch является защищаемым ресурсом.
- Sustain можно обрабатывать заметнее в EQ/Clarity/Stabilizer/DynEQ.
- Impact оценивается по punch/groove, не по величине ручки.
- DynEQ low bands не включаются без явной kick/bass проблемы.
- Limiter target уступает атаке и macro dynamics.

## 4. Width with mono survival

- Headphone wow строится преимущественно на upper Sustain.
- Low/center/primary transients держатся стабильными.
- Исчезновение важного элемента в mono — hard reject.
- `Prevent Antiphase`, correlation или один vectorscope по отдельности недостаточны; нужны mono listening и band/sample-aligned checks.

## 5. Maximizer activation

- Inactive Auto params не влияют на DSP, но становятся опасны при добавлении модуля в chain.
- При активации явно проверить Mode, Gain, Margin, True Peak, Soft Clip, Low Level Boost и linking.
- `Target Loudness` не заменяет `Gain`.
- Примерная потеря matched event attack `0.5–1.0 dB` — warning zone; слуховой loss of punch — stop.

## 6. Native final and codec delivery

- Финальный 24-bit файл выводится нативно из DAW/Ozone.
- При наличии accepted float render final проверяется null/sample comparison; dither residual должен выглядеть как unbiased low-level noise.
- Post-conversion control полезен для диагностики, но не подменяет native final.
- WAV true peak не гарантирует decoded MP3/AAC true peak.
- Для direct lossy delivery применяется codec-specific measured trim, затем повторный encode/decode audit.
- Проверять не только spectrum и peak, но также duration/padding, mono, Side/Mid и ударную атаку.

## 7. Universalization gate

В core попадает только schema, procedure, formula, warning или hard reject. Exact winner settings и exact per-track outcomes остаются в track log.
