# Ozone 12 Maximizer XML examples

Содержимое архива:

- `docs/Ozone12_Maximizer_XML_Explanation.md` — подробное объяснение параметров.
- `snippets/*.xml` — готовые блоки Maximizer для ручного сравнения/копирования.
- `table/maximizer_param_map.csv` — таблица ParamID → смысл.
- `scripts/patch_ozone_maximizer.py` — безопасный текстовый патчер `<Maximizer>`.
- `scripts/Set-OzoneMaximizer.ps1` — PowerShell-обёртка для Windows / PowerShell 7.
- `example_full_xml/*.xml` — примеры полных XML, созданных из уже рабочих пресетов.

## Быстрый запуск

```powershell
python .\scripts\patch_ozone_maximizer.py .\input.xml .\output_streaming_safe.xml --profile streaming-safe
python .\scripts\patch_ozone_maximizer.py .\input.xml .\output_wow.xml --profile wow-pop
```

или:

```powershell
.\scripts\Set-OzoneMaximizer.ps1 -InputXml .\input.xml -OutputXml .\out.xml -Profile wow-pop
```

## Критический чеклист

1. Не менять только `Target Loudness [dB]`; фактический уровень в основном задаёт `Gain`.
2. `Margin` = ceiling/output.
3. `Prevent Intersample Clipping = 1` = True Peak On.
4. `Soft Clip Enable = 0`, если это не отдельный эксперимент.
5. Maximizer должен быть в `ElementChain` и последним.
6. Перед рендером Ozone: `Gain Match Off`, `Reference Off`, `Codec Off`, `Bypass Off`.
7. В DAW: `Normalize Off`, `Rendered Track = Main/Master`.
