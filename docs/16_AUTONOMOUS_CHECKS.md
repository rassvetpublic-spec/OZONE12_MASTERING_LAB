# Autonomous Checks

## Назначение

`tools/autocheck` предоставляет единую автономную проверку repository и полного P0 Gate.

```text
repository tree + external P0 evidence
→ deterministic checks
→ PASS / FAIL / BLOCKED
→ JSON + Markdown + evidence manifest
→ meaningful process exit code
```

Проверяющий контур не генерирует ложное evidence и не объявляет отсутствующее доказательство успешным. Интерактивный L0 Oracle, запуск Master Assistant и state-loading backend выполняются отдельно до их квалификации. После появления render/readback artifacts их проверка полностью автономна.

## Точки входа

Windows, весь контур:

```powershell
pwsh -File tools/autocheck/Invoke-Ozone12Checks.ps1 `
  -Mode All `
  -P0Config "D:\OZONE12_P0\p0_config.json" `
  -OutDir "D:\OZONE12_P0\reports"
```

Только repository/CI:

```powershell
pwsh -File tools/autocheck/Invoke-Ozone12Checks.ps1 -Mode Repository
```

Cross-platform Python:

```bash
python tools/autocheck/oz12_autocheck.py repo --outdir reports/autocheck/repository
python tools/autocheck/oz12_autocheck.py self-test
```

Создание external P0 workspace:

```powershell
pwsh -File tools/autocheck/New-P0Workspace.ps1 `
  -Root "D:\OZONE12_P0" `
  -SelectedBackend L2
```

Команда не перезаписывает существующий `p0_config.json` без явного `-Force`.

Автономные три D0 render для P0.1:

```powershell
pwsh -File tools/autocheck/Invoke-DryHarness.ps1 `
  -ProjectPath "D:\OZONE12_P0\D0_template.rpp" `
  -ConfiguredRenderPath "D:\OZONE12_P0\reaper_output\D0.wav" `
  -OutDir "D:\OZONE12_P0\p0_1_dry"
```

`.rpp` должен заранее содержать canonical render settings и точный output path из `ConfiguredRenderPath`. Runner отклоняет RPP с FX blocks, выполняет renders последовательно через REAPER `-renderproject`, не перезаписывает существующие outputs и пишет `dry_harness_runs.json` с SHA-256.

## Repository checks

Один запуск `repo` проверяет:

- Python 3.12;
- целостность и frozen SHA-256 Universal Core v1.3;
- компиляцию всех Python tools;
- process-only scope;
- актуальность трёх repository manifests;
- synthetic self-test automatic mastering meter;
- synthetic positive/negative self-test самого P0 evaluator;
- наличие `ffmpeg` и `ffprobe`.

GitHub Actions вызывает этот же entry point, поэтому локальная и CI-логика не расходятся.

## P0 evidence contract

Все пути в `p0_config.json` относительны каталога config, если не заданы абсолютными. `source_wav` указывает immutable source; его SHA-256 автоматически сверяется со всеми readback. WAV должны быть PCM с одинаковыми sample rate, channel count, sample width и frame count.

Readback для L0/L1/L2/L3:

```json
{
  "schema_version": 1,
  "state_id": "S0",
  "backend": "L2",
  "source_sha256": "64-hex",
  "target_state_sha256": "64-hex",
  "loaded_state_sha256": "64-hex",
  "plugin_identity": "Ozone 12 VST3",
  "plugin_version": "120002",
  "plugin_build": "1331",
  "element_chain": ["Equalizer", "Impact"],
  "readback_ok": true,
  "render_invoked": true
}
```

Readback обязан быть создан до render call. `target_state_sha256` и `loaded_state_sha256` должны совпадать.

L4 evidence:

```json
{
  "backend": "L4",
  "readback_ok": true,
  "changed_parameter": "published parameter identifier",
  "before_value": 0,
  "after_value": 1
}
```

Negative Render Gate result:

```json
{
  "blocked": true,
  "render_invoked": false,
  "wav_created_count": 0
}
```

Для `wrong_target_hash`, `api_failure` и `readback_mismatch` evaluator дополнительно рекурсивно проверяет output directory: там не должно быть ни одного WAV.

## Автоматические P0 решения

| Gate | Автономная проверка |
|---|---|
| P0.0 | environment snapshot против expected config; версии Python/NumPy/SciPy/FFmpeg; наличие REAPER/Ozone; hashes анализаторов |
| P0.1 | минимум три D0 PCM render; format equality; фактический maximum sample delta |
| P0.2 | L0 readback/render для S0/S1/S2 |
| P0.3 | L1 readback/ElementChain/render против L0 в пределах Dry baseline |
| P0.4/P0.5 | выбранный L2 или L3 против L0 для S0/S1/S2 |
| P0.6 | одно подтверждённое изменение published parameter |
| P0.7 S2 | структура S2 отличается от S0 и восстановлена выбранным backend |
| P0.7 repeats | минимум три self-repeat render выбранного backend |
| P0.7 negatives | три forced failures; render не вызван; создано 0 WAV |

Невыбранный L2/L3 backend может иметь статус `SKIP`; полный PASS требует выбранного и квалифицированного L2 или L3.

## Exit codes

```text
0 = все обязательные проверки PASS
2 = обнаружен FAIL
3 = BLOCKED: обязательного evidence или prerequisite нет
```

`BLOCKED` является stop-condition для automation.

## Outputs

```text
autocheck.json
autocheck.md
autocheck_summary.json      Mode All
environment_observed.json  PowerShell wrapper
evidence_manifest.json     P0 referenced inputs + SHA-256
```

Reports и raw P0 evidence остаются во внешнем workspace и не коммитятся в process-only repository.
