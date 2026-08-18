# OZONE12_MASTERING_LAB

Универсальная база знаний и инструментарий для воспроизводимого мастеринга готовых stereo WAV:

```text
SUNO WAV → iZotope Ozone 12 Advanced → native WAV 24-bit / 48 kHz
```

DAW используется только как render-host. Первый автоматизируемый контур: XML-пресеты Ozone, WAV-анализ и JSON/CSV/Markdown-отчёты — без GUI-автоматизации DAW.

## Scope

Репозиторий хранит только знания о процессе:

- XML schema и ParamID mapping;
- порядок модулей и stage-by-stage workflow;
- Transient/Sustain protocol;
- измерения, формулы и decision heuristics;
- generic profiles/snippets;
- mono/codec/export validation;
- инструменты и воспроизводимые проверки.

Названия произведений, тексты, audio-файлы, per-session winners, точные сессионные метрики и track-specific XML в repository не включаются.

`tools/validate_process_only_scope.py` автоматически отклоняет session directories и audio-файлы.

## Source of truth

Приоритет:

1. `docs/project/ACTIVE_CURRENT.md`;
2. `docs/00_READ_FIRST_SOURCE_OF_TRUTH.md`;
3. Universal Core v1.3;
4. generic profiles, tables и validation;
5. архивные материалы — только как references.

Данные рабочей мастеринг-сессии передаются отдельно и не коммитятся в этот repository.

Universal Core подтверждает XML-карту для:

```text
PresetVer=6
PluginVer=120002
PluginBuild=1331
```

Активная цепь определяется только декодированным `Global/ExtraBytes ElementID="ElementChain"`, а не одним `Enabled=1`.

## Рабочая цепь

```text
Master Rebalance — optional, только при доказанной необходимости
→ Equalizer
→ Impact
→ Clarity
→ Stabilizer
→ Stereo Imager
→ Dynamic EQ
→ Maximizer
```

Каждая стадия рендерится из исходного WAV с накопленным XML. Выбранный GUI-saved winner становится новой базой только внутри рабочей сессии. Maximizer всегда последний.

## Репозиторий

- `docs/` — универсальные правила и текущее состояние процесса;
- `tables/` — machine-readable XML/decision maps;
- `profiles/` — generic target profiles;
- `tools/` — XML patching, stage analysis и automatic mastering meter;
- `snippets/` — универсальные XML-примеры, не defaults;
- `dist/` — собранный архив для ChatGPT Project Sources;
- `validation/` — аудит и проверки Universal Core.

## Automatic mastering meter

`tools/stage_toolkit/oz12_mastering_meter.py` измеряет:

- event-aligned drum-attack;
- relative mono-loss overall/by-band;
- decoded peaks после реального MP3/AAC encode → decode;
- и создаёт JSON, CSV и Markdown-отчёты.

Быстрая проверка стадии:

```bash
python tools/stage_toolkit/oz12_mastering_meter.py \
  --reference "BASE.wav" \
  --candidate "CANDIDATE.wav" \
  --outdir "reports/mastering_meter" \
  --skip-codecs
```

Метрики являются guards, а не заменой слухового выбора.

Зависимости анализа:

```bash
python -m pip install -r requirements-analysis.txt
```

Для codec audit дополнительно требуется `ffmpeg`/`ffprobe`.

## Текущий статус

- Universal Core: `v1.3`;
- процессные XML/T-S знания build 1331 консолидированы;
- automatic meter реализован и проходит synthetic self-test;
- следующий этап — real-world validation с публикацией только обезличенных переносимых выводов.

См. `docs/project/ACTIVE_CURRENT.md`, `docs/project/PROCESS_ONLY_POLICY.md` и `docs/project/ROADMAP.md`.
