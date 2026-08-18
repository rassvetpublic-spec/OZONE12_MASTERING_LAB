# Идея нового проекта: ежедневный мастеринг SUNO WAV через Ozone 12 Advanced

## Короткий вывод

Для ежедневной работы можно упростить процесс: **использовать iZotope Ozone 12 Advanced как единственный мастеринг-процессор**, а DAW оставить только как хост для загрузки плагина и экспорта WAV.

То есть рабочая идея не «Ableton + Waves + куча ручных плагинов», а:

```text
готовый SUNO stereo WAV → Ozone 12 Advanced → WAV 24-bit / 48 kHz для площадок
```

## Важное ограничение

Полностью обойтись одним Ozone 12 Advanced **без хоста, скорее всего, нельзя**, потому что standalone-приложение Ozone было прекращено начиная с Ozone 10; для Ozone 11 и выше standalone-версии нет. Поэтому Ozone 12 Advanced используется как плагин внутри хоста: Ableton Live, REAPER, Cubase и т.п.

Практически это значит:

```text
Ozone 12 Advanced = весь звук/мастеринг
Ableton/Reaper = только контейнер, импорт WAV, экспорт WAV
```

## Почему это хорошая идея

1. Меньше переменных.
2. Проще сравнивать версии.
3. Легче автоматизировать через XML-пресеты.
4. Не нужно каждый раз собирать цепочку из разных плагинов.
5. Уменьшается риск случайно изменить звук до/после Ozone.
6. Codex может генерировать XML-вилки и анализировать WAV-рендеры без понимания всей DAW-сессии.

## Базовый принцип проекта

Новый проект должен быть не «сведение в DAW», а **мастеринг-лаборатория Ozone XML + WAV analysis**.

Основной цикл:

```text
1. Положить исходный SUNO WAV.
2. Положить текст/стиль как творческое ТЗ.
3. Положить базовый Ozone XML.
4. Codex генерирует вилки XML.
5. Пользователь рендерит WAV через Ozone в хосте.
6. Codex анализирует WAV.
7. Codex делает отчёт и предлагает следующий XML.
8. Финальный кандидат утверждается на слух.
```

## Что оставить в Ozone

Для готового stereo WAV основная цепочка:

```text
1. Master Rebalance
2. Equalizer
3. Impact
4. Clarity
5. Stabilizer
6. Stereo Imager
7. Dynamic EQ
8. Maximizer
```

Порядок модулей важен. Не считать все XML-блоки `Enabled=1` активной цепью. Активной цепью считать `ElementChain`.

## Что не использовать по умолчанию

Без отдельного теста не включать:

```text
Stereoize
Soft Clip
Recover Sides выше +1.2 dB
очень громкие цели типа −8.5 LUFS
Waves-плагины до или после Ozone
дополнительный лимитер после Ozone
Normalize при экспорте
```

## Целевой профиль для тёмного rock / gothic / industrial streaming master

```yaml
profile: dark_gothic_industrial_streaming
input: stereo_suno_wav
processor: izotope_ozone_12_advanced_only
host: ableton_live_or_reaper_render_host
sample_rate: 48000
release_bit_depth: 24
archive_bit_depth: 32_float_optional
integrated_lufs_target: [-12.3, -11.5]
true_peak_target_db: -2.0
normalize_export: false
mp3_export_for_release: false
soft_clip: false
stereoize_default: false
recover_sides_max_db: 1.2
main_priorities:
  - preserve_low_female_vocal
  - preserve_choir_and_center
  - reduce_clicks_and_harshness_6_12khz
  - keep_dark_character
  - widen_sustain_more_than_transients
  - avoid_phase_smear
```

## Что должен автоматизировать Codex

Codex не обязан управлять Ableton на первом этапе. Важнее автоматизировать:

1. Проверку исходников.
2. Разбор Ozone XML.
3. Декодирование активного `ElementChain`.
4. Генерацию XML-вилок.
5. Анализ WAV-рендеров.
6. Сравнение метрик.
7. Markdown/CSV отчёт.
8. Выбор технического кандидата.

## Папочная структура нового проекта

```text
OZONE12_MASTERING_LAB/
├─ input/
│  ├─ source.wav
│  ├─ lyrics.txt
│  ├─ style.txt
│  └─ base_ozone.xml
├─ presets/
│  ├─ 01_base.xml
│  ├─ 02_wide.xml
│  ├─ 03_impact.xml
│  └─ 04_final_candidate.xml
├─ renders/
│  ├─ 01_base.wav
│  ├─ 02_wide.wav
│  └─ 04_final_candidate.wav
├─ reports/
│  ├─ source_registry.md
│  ├─ metrics.csv
│  ├─ comparison.md
│  └─ decision.md
├─ config/
│  ├─ profile_dark_gothic_streaming.yaml
│  └─ fork_rules.yaml
└─ tools/
   ├─ Prepare-Run.ps1
   ├─ New-OzoneForks.ps1
   ├─ Analyze-Renders.ps1
   └─ Make-DecisionReport.ps1
```

## Ежедневный рабочий процесс

```text
1. Новый WAV от SUNO положить в input/source.wav.
2. Стиль и слова положить в input/style.txt и input/lyrics.txt.
3. Базовый XML положить в input/base_ozone.xml.
4. Запустить Prepare-Run.ps1.
5. Запустить New-OzoneForks.ps1.
6. Вручную загрузить XML-вилки в Ozone внутри Ableton/Reaper.
7. Отрендерить WAV 24-bit / 48 kHz.
8. Положить рендеры в renders/.
9. Запустить Analyze-Renders.ps1.
10. Открыть reports/decision.md.
11. Утвердить финальный XML/WAV.
```

## Роль Ableton или REAPER

Если остаёмся в Ableton:

```text
Ableton = импорт WAV, Ozone на Main, экспорт WAV.
```

Если хотим больше автоматизации рендера, стоит рассмотреть REAPER как технический batch-render host:

```text
REAPER = технический хост для пакетных рендеров
Ozone = единственный мастеринг-процессор
Codex = генерация XML + анализ + отчёты
```

Но творческая логика остаётся той же: **мастеринг делает Ozone, не DAW**.

## Решение для старта

Начинать новый проект надо с версии:

```text
Ozone-only mastering lab, manual render phase
```

Не автоматизировать GUI Ableton первым шагом. Сначала сделать стабильные инструменты:

```text
XML fork generator
WAV analyzer
comparison report
final decision report
```

После этого уже можно подключать автоматический рендер через REAPER или GUI-автоматизацию.

## Источники

- iZotope Support: Ozone Standalone Application Discontinued — standalone Ozone прекращён начиная с Ozone 10; Ozone 11 и выше standalone не имеют.
- iZotope Ozone 12 Advanced product page — Ozone 12 Advanced описан как all-in-one suite для мастеринга.
- iZotope Support: большинство iZotope-продуктов работают как плагины внутри host application / DAW.
