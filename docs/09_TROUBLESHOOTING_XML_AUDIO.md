# 09. Troubleshooting XML / Audio

## XML изменился, звук почти нет

1. Параметр относится к активному модулю в decoded `ElementChain`?
2. Это DSP field, а не UI/selector/target/display?
3. Gain Match/Auto Gain/learn/cache не маскирует разницу?
4. Рендер сделан из source WAV с нужным XML?
5. Сделан Delta и loudness-matched A/B?
6. Если направление всё ещё не слышно — one-module boundary probe, не одновременное усиление всей цепи.

## Maximizer не управляется

```text
Target Loudness меняют вместо Gain
Maximizer не в ElementChain
не тот Mode
inherited Soft Clip/Low Level Boost
не тот Margin/True Peak
Normalize On
```

## Imager даёт wow, но ломает mono

Если голос/гитара/важный элемент исчезает или резко проваливается в mono — reject. Ослабить upper Sustain width/Recover Sides, отключить Stereoize, стабилизировать low/center/transient bands. Проверить sample-aligned mono/mid и band correlation. `Prevent Antiphase` не является доказательством.

## Dynamic EQ темнит или съедает ударные

Ослабить Sustain high-band threshold/gain, убрать broad high cut. В drum-forward profile проверить, не активированы ли low bands по kick/bass. DynEQ должен ловить long glass после Imager, а не отнимать front edge.

## Manual XML выбран

Если пользователь выбрал GUI-saved вариант, назначить его новой базой. Не пересобирать старые модули из прежнего generated XML.

## Invalid preset

Вернуться к XML, который точно загружался. Сделать минимальный patch, проверить parse, duplicate ParamID, `ElementChain`, float format и unknown blocks.
