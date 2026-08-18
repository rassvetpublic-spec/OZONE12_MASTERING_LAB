# ACTIVE / CURRENT

Дата фиксации: 2026-08-18.

## Активный проект

`OZONE12_MASTERING_LAB` — универсальное техническое ядро мастеринга: XML Ozone, анализ аудио, отчёты, decision rules и автоматизация.

Repository является process-only. Данные конкретных произведений и отдельных мастеринг-сессий хранятся вне него.

Отдельный контур проверки render-host environment, collector и dry-render determinism не является источником процессных XML/audio-решений этого repository.

## Активный универсальный источник

`OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1.3.zip`

SHA-256 исходного архива:

```text
f78e8dac9dc81fe60e110442281c4da988a128f4591e1cb515c64761e89e100e
```

Архив v1.2 и старые дубли не должны быть одновременно активными Sources.

## Главная цель

```text
готовый SUNO stereo WAV
→ Ozone 12 Advanced
→ native WAV 24-bit / 48 kHz
→ mono/codec validation
→ релиз
```

Критерии музыкального результата:

- слышимое улучшение без потери причинности;
- сохранение атаки, groove и macro dynamics;
- вокал не становится матовым или далёким;
- нет codec/SUNO glass;
- центр, бас и важные элементы выживают в mono;
- decoded MP3/AAC peaks проверяются измерением, а не прогнозом по WAV.

## Реализовано

- подтверждённая T/S XML-схема build 1331;
- безопасный stage-by-stage workflow;
- generic profiles/snippets/decision heuristics;
- XML patch и ElementChain validation;
- automatic mastering meter: drum attack, mono loss, decoded codec peaks;
- правила native final и codec-specific trim;
- process-only source boundary.

## Следующий активный этап

1. Провести real-world validation automatic meter на внешних сессионных данных.
2. Сопоставить numeric guards со слуховыми решениями.
3. Публиковать только обезличенные переносимые процедуры, формулы, warnings и hard rejects.
4. Расширять batch automation после стабилизации XML/audio analysis.

