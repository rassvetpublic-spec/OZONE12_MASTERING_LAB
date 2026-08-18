# ACTIVE / CURRENT

Дата фиксации: 2026-08-18.

## Активный проект

`OZONE12_MASTERING_LAB` — локальная Windows-first mastering system и универсальное техническое ядро: Ozone XML/full state, REAPER render-host, audio analysis, decision rules, web UI и automation.

Repository остаётся process-only. Здесь допустимы универсальная runtime architecture и P0 qualification protocol. Данные конкретных произведений, machine-specific evidence и отдельные mastering sessions хранятся вне repository.

## Активная архитектура

`docs/project/ARCHITECTURE_v1.md` — **ACTIVE / APPROVED**.

Главное архитектурное решение:

```text
local web UI on localhost
→ Python orchestrator + SQLite
→ exclusive REAPER 7 render worker
→ Ozone 12 as the only DSP
→ quick/full renders + state readback + metrics
→ optional ChatGPT/OpenAI review
```

Автоматический stage runner и web-controlled render запрещено разрабатывать как production path до полного P0 PASS.

## P0 status

Подтверждённый environment baseline:

```text
P0.0 = COMPLETE
Windows 11 x64
PowerShell 7.6.3
Python 3.12 x64
REAPER 7.78 x64
Ozone 12.0.2 build 1331 VST3 x64
native final = stereo PCM WAV 24-bit / 48 kHz
Normalize = Off
intermediate dither = Off
```

Не завершено:

```text
P0.1 Dry Harness
P0.2 L0 Oracle
P0.3 L1 Frozen RPP
P0.4 L2 .vstpreset
P0.5 L3 vst_chunk
P0.6 L4 published parameter
P0.7 backend qualification, negative Render Gate and S2
```

Полный PASS требует квалифицированного L2 или L3, совпадения с L0 на S0/S1/S2 в пределах Dry Harness baseline и negative-gate PASS с 0 WAV.

## Активный universal process source

`OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1.3.zip`

SHA-256 frozen archive:

```text
f78e8dac9dc81fe60e110442281c4da988a128f4591e1cb515c64761e89e100e
```

Frozen v1.3 archive не перезаписывается этой архитектурной фиксацией. Актуальная architecture/P0 authority находится в repository tree; включение её в Sources package требует новой версии package.

## Главная цель

```text
готовый SUNO stereo WAV + style/intent
→ Ozone Auto reference
→ cumulative Safe/Probe/Refine stages
→ native WAV 24-bit / 48 kHz
→ mono/codec validation
→ human-approved release
```

Стандартная цепь:

```text
Master Rebalance — optional
→ Equalizer
→ Impact
→ Clarity
→ Stabilizer
→ Stereo Imager
→ Dynamic EQ
→ Maximizer
```

## Реализовано

- private process-only repository foundation;
- Universal Core v1.3 и подтверждённая T/S XML-схема build 1331;
- safe stage-by-stage workflow и generic profiles/heuristics;
- XML patch, ElementChain validation и stage toolkit;
- automatic mastering meter: drum attack, mono loss, decoded codec peaks;
- architecture v1 и mandatory P0 Gate.
- autonomous repository/P0 checker с JSON/Markdown reports, evidence manifest и fail-closed `PASS/FAIL/BLOCKED` status;
- PowerShell entry point и external P0 workspace initializer.
- safe P0.1 runner для трёх последовательных D0 command-line renders без FX.

Автономный checker не означает, что P0 пройден: фактические REAPER/Ozone render/readback artifacts ещё должны быть получены на зафиксированной Windows workstation.

## Следующий активный этап

1. Выполнить P0.1: минимум три D0 dry renders без Ozone.
2. Зафиксировать фактический determinism baseline до назначения equality tolerances.
3. Выполнить L0–L4, S2 и negative Render Gate qualification.
4. Только после полного P0 PASS начинать production web/runtime automation.
