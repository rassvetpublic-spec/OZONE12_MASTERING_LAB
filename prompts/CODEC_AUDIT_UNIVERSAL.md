Сделай codec audit нативного финального WAV-кандидата.
Создай/проверь MP3 320, AAC 256 и AAC 192 stress-test; декодируй каждый файл.
После time/level alignment сравни LUFS, decoded true peak, correlation, mono, Side/Mid, normalized band deltas 8–12/12–18 kHz, clip count, duration, leading/trailing padding и tail.
True Peak WAV не считать гарантией decoded peak. Для direct lossy delivery рассчитать codec-specific attenuation и перепроверить повторным encode/decode.
Выдай PASS/CONDITIONAL/REJECT и назови musical/technical reject-признаки.
Если доступен Universal Core v1.3, запусти `tools/stage_toolkit/oz12_mastering_meter.py` и приложи `mastering_meter.json`, `mastering_meter.csv`, `drum_attack_events.csv`, `mastering_meter_report.md`; target dBTP не выдумывай, используй только declared delivery target.
