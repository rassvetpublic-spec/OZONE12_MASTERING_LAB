# Ozone 12 Stabilizer / Stereo Imager T-S XML examples

Главное:

- `Transient/Sustain` — это режим `Stereo Imager`, не `Stabilizer`.
- `Stabilizer` управляется в основном `Amount`, `Target`, `Auto Gain Enable`.
- В Imager:
  - `Band N Width Percent` = Transient width.
  - `Aux: Band N Width Percent` = Sustain width.
  - `Recover Sides Gain Offset (dB)` = Transient recover sides.
  - `Aux: Recover Sides Gain Offset (dB)` = Sustain recover sides.
- Активную цепь проверять через `ElementChain`, не через `Enabled=1`.

## Примеры команд

```powershell
# Imager Transient/Sustain strong
.\scripts\Set-OzoneImagerTS.ps1 -InputXml .\input\base.xml -OutputXml .\presets\wide_strong.xml -Preset strong

# Stabilizer safe amount, target оставить как был
.\scripts\Set-OzoneStabilizer.ps1 -InputXml .\input\base.xml -OutputXml .\presets\stab_safe.xml -Amount 14

# Stabilizer с Target только если enum подтверждён в GUI
.\scripts\Set-OzoneStabilizer.ps1 -InputXml .\input\base.xml -OutputXml .\presets\stab_open_target10.xml -Amount 20 -Target 10
```

После импорта XML обязательно проверить Ozone UI.
