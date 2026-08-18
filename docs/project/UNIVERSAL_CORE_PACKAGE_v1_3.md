# OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1.3

Назначение: единый универсальный источник правил, XML-схем и проверок для проекта **OZONE12_MASTERING_LAB** без привязки к конкретному треку.

Этот ZIP предназначен для активных Sources проекта. После добавления ZIP **v1.3** архив v1.2 нужно убрать из активных Sources, чтобы не было конкурирующих правил. Для текущего трека отдельно прикладываются актуальные source WAV, optional MP3 reference, lyrics/style, current base XML и рендеры.

## Приоритет

```text
Главный источник универсальных правил: OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1.3.zip.
Старые ZIP/MD/CSV/отчёты и трековые файлы использовать только как архивные references.
Если старый файл конфликтует с Universal Core v1.3 — приоритет у Universal Core v1.3.
Для конкретного трека использовать только актуальные source audio, lyrics/style, выбранный base/winner XML и текущий чат.
```

## Что подтверждено для XML

Для `PresetVer=6 / PluginVer=120002 / PluginBuild=1331` подтверждена T/S-схема Equalizer, Clarity, Stabilizer, Stereo Imager и Dynamic EQ. Impact и Maximizer не получают выдуманную Main/Aux T/S-карту. `ElementChain`, а не `Enabled=1`, определяет активную цепь.

## Что нового в v1.3

1. Source gate: мастеринг строится из WAV. MP3 используется только как reference или результат codec audit.
2. Добавлен optional pre-stage `Master Rebalance`; он входит в активный DSP только через `ElementChain`, не имеет T/S-ветки и не получает универсальных gain/default значений.
3. Если безопасная настройка почти не слышна, разрешён one-module boundary probe. После обнаружения слышимой границы настройка отступает к музыкальному winner.
4. Выбранный пользователем GUI-saved XML становится новой базой. Последующие стадии обязаны сохранять ранее принятые модули byte-equivalent, если они не объявлены активными.
5. Добавлен профиль `drum_forward_commercial`: атака ударных сохраняется сильнее sustain; низ Dynamic EQ не должен незаметно давить kick/bass.
6. Для Imager введён hard reject: если важный инструмент заметно исчезает в mono, стерео-кандидат отклоняется независимо от wow-эффекта и `Prevent Antiphase`.
7. Maximizer: `Gain` управляет фактической громкостью, `Target Loudness` остаётся target/display. При активации модуля inherited Soft Clip/Low Level Boost нужно явно проверить и по умолчанию нейтрализовать.
8. Прописан stop-сигнал для громкости: если matched transient attack заметно теряется, музыкальная цель важнее запланированного LUFS.
9. Нативный DAW/Ozone 24-bit export является финальным authority. Пост-конвертированный control WAV не заменяет его; при наличии float render используется sample/null comparison.
10. True Peak финального WAV не гарантирует такой же decoded peak у MP3/AAC. Для прямой lossy-доставки trim рассчитывается отдельно по измеренному декодированному файлу.
11. Добавлены machine-readable decision heuristics и обобщённый отчёт о проверенных стадиях без названий песен и частных winner-значений.
12. Добавлен automatic mastering meter: event-aligned drum-attack guard, relative mono-loss overall/by-band и реальные MP3/AAC encode→decode peaks с JSON/CSV/Markdown output.

## Структура

```text
docs/                  главные универсальные правила проекта
skills/                reusable XML/T-S skill и stage/finalization logic
tables/                карты параметров и decision heuristics
profiles/              optional профили целей мастеринга
prompts/               стартовые и рабочие промпты
templates/             шаблоны stage/decision/codec-audit
checklists/            короткие чеклисты
tools/                 Python/PowerShell helpers анализа, automatic meter и XML patching
source_consolidated/   архивные источники; ниже docs/skills по приоритету
snippets/              generic XML-фрагменты, не track defaults
migration/             правила замены активного source package
validation/            аудит v1.3
```

## Цепь

Стандарт:

```text
Equalizer → Impact → Clarity → Stabilizer → Stereo Imager → Dynamic EQ → Maximizer
```

Если требуется stem-level correction готового stereo source:

```text
Master Rebalance → Equalizer → Impact → Clarity → Stabilizer → Stereo Imager → Dynamic EQ → Maximizer
```

Порядок и присутствие каждого модуля проверяются декодированием `ElementChain`.

## Automatic mastering meter

Быстрый stage-check:

```bash
python tools/stage_toolkit/oz12_mastering_meter.py \
  --reference "BASE.wav" \
  --candidate "CANDIDATE.wav" \
  --outdir "reports/mastering_meter" \
  --skip-codecs
```

Для финала убрать `--skip-codecs`; по умолчанию будут реально encoded/decoded MP3 320, AAC 256 и AAC 192. Delivery ceiling задаётся явно через `--decoded-peak-target-dbtp`; без него decoded peaks измеряются в режиме `MEASURED`. Полный протокол: `docs/15_AUTOMATIC_MASTERING_METER.md`.
