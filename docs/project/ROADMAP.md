# Roadmap

## P1 — Repository foundation

- [x] Выделить отдельный приватный GitHub repository.
- [x] Перенести Universal Core v1.3 как редактируемые исходники.
- [x] Сохранить Sources ZIP в `dist/`.
- [x] Зафиксировать process-only scope.
- [ ] Review и merge initial import PR.

## P2 — Real-world validation

- [ ] Прогнать automatic meter на внешних reference/candidate парах.
- [ ] Проверить pre-Maximizer → native final comparison.
- [ ] Выполнить MP3 320 / AAC 256 / AAC 192 encode→decode audit.
- [ ] Сопоставить numeric guards со слуховым решением.
- [ ] Калибровать review thresholds без превращения эвристик в физические законы.

Исходные audio, titles, session XML и точные результаты остаются вне repository.

## P3 — Universal knowledge curation

- [ ] Извлекать из практических сессий только переносимые schema/procedure/formula/warning/hard reject.
- [ ] Удалять идентификаторы произведений, имена файлов и per-session numbers до публикации.
- [ ] Не превращать единичный winner в universal default.
- [ ] Обновлять generic profile только после повторяемого подтверждения.
- [ ] Фиксировать provenance универсализированного правила.

## P4 — Standard production workflow

- [ ] Source gate: исходный WAV + current base XML + current task вне repository.
- [ ] Baseline audio/XML audit.
- [ ] Stage-by-stage: EQ → Impact → Clarity → Stabilizer → Imager → Dynamic EQ → Maximizer.
- [ ] Optional Master Rebalance — только при доказанной необходимости.
- [ ] Native 24-bit/48 kHz final + mono/codec audit + external session manifest.

## P5 — Automation expansion

- [ ] Пакетное создание XML-вилок и stage packs.
- [ ] Автоматическое формирование обезличенного decision report.
- [ ] Batch render через REAPER как render-host после стабилизации XML/audio analysis.
- [ ] GUI-автоматизацию рассматривать только после доказанной необходимости.

