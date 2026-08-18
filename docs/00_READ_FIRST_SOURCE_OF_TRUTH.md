# 00. Read First / Source of Truth

## Главный принцип

Готовый stereo **WAV** → **iZotope Ozone 12 Advanced** → нативный WAV 24-bit / 48 kHz.

DAW используется как render-host. Дополнительная обработка до/после Ozone допустима только по прямой задаче и должна быть перечислена. MP3 не является mastering source, если доступен WAV; это reference или codec-audit output.

## Приоритет источников

1. Project Instructions текущего проекта.
2. `OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1.3.zip` как универсальное ядро.
3. Актуальные файлы текущего трека: source WAV, optional MP3, lyrics/style, current base/winner XML, текущие рендеры.
4. Текущий чат, если он уточняет текущий трек.
5. Старые sources/references/чаты — только справка.
6. Память и File Library — не source of truth для XML/аудио.

## Подтверждённая Ozone XML версия

Основная T/S-карта подтверждена для:

```text
PresetVer = 6
PluginVer = 120002
PluginBuild = 1331
```

Если версия/build совпадает — повторный calibration probe для известных полей не нужен. Если отличается — перепроверять только неизвестные и enum-зависимые поля.

## Base/winner rule

Если пользователь изменил настройки в GUI, сохранил XML и выбрал этот результат, данный GUI-saved XML становится текущей базой. Сгенерированный ранее кандидат не имеет приоритета над явно выбранным winner.

## Если конфликт

Остановиться и назвать:

```text
какие источники конфликтуют
какое правило/параметр конфликтует
какой риск для звука/XML
что нужно выбрать или проверить
```

Нельзя молча выбирать старый файл, если Universal Core v1.3 говорит иначе.

## Source gate перед stage

```text
Base audio = source WAV
Base XML = current source/auto/GUI winner XML
PluginVer/Build = root attributes
Active chain = ElementChain decoded
Active module = one module
Changed only = active module or declared control pass
```
