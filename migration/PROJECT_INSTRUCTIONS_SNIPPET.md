Главный источник универсальных правил проекта: OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1.3.zip.
Старые ZIP/MD/CSV, explainers и трековые sources использовать только как архивные references.
Если старый файл конфликтует с Universal Core v1.3 — приоритет у Universal Core v1.3.
Master source = актуальный WAV; MP3 = reference/codec output.
Для текущего трека учитывать только current source audio, lyrics/style, selected base/winner XML и текущие renders/reports.
DAW используется как render-host; финальный 24-bit WAV выводится нативно из DAW/Ozone.
Активную цепь читать через ElementChain, не через Enabled=1.
Стандартный порядок: Equalizer → Impact → Clarity → Stabilizer → Stereo Imager → Dynamic EQ → Maximizer.
Master Rebalance допустим только optional pre-stage и с track-specific GUI-verified values.
Для PresetVer=6 / PluginVer=120002 / PluginBuild=1331 использовать T/S XML-карту v1.3 без повторной calibration известных ParamID.
Calibration-only и exact prior-track winners никогда не использовать как defaults.
Mono instrument loss, invalid XML, decoded overs и слышимая потеря drum attack — reject/stop conditions.
