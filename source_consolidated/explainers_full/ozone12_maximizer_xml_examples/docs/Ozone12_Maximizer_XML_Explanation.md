# Ozone 12 Advanced — Maximizer в XML: что менять и почему

Проект: **OZONE12_MASTERING_LAB**  
Назначение: объяснить, какими XML-параметрами управлять Maximizer в iZotope Ozone 12 Advanced, чтобы другой чат/Codex не ломал пресет и не получал «неуправляемый» лимитер.

---

## 1. Главное правило

Maximizer управляется блоком:

```xml
<Maximizer Enabled="1">
    ...
</Maximizer>
```

Но одного `Enabled="1"` недостаточно. Модуль реально должен входить в активную цепочку `ElementChain` и обычно должен быть **последним** модулем в цепи.

Проверять надо два места:

1. Есть ли блок `<Maximizer Enabled="1">`.
2. Есть ли `Maximizer` в `Global / ExtraBytes ElementID="ElementChain"`.

Если Maximizer есть в XML, но отсутствует в `ElementChain`, Ozone может не показывать его в верхней цепи и он не будет работать как ожидается.

---

## 2. Проверенный блок Maximizer из рабочих пресетов

Типовой рабочий блок:

```xml
<Maximizer Enabled="1">
    <Param ElementID="Maximizer" ParamID="Mode" Value="3" />
    <Param ElementID="Maximizer" ParamID="Margin" Value="-2,00001144" />
    <Param ElementID="Maximizer" ParamID="LowLevelBoostWetAmount" Value="1,10000000" />
    <Param ElementID="Maximizer" ParamID="Prevent Intersample Clipping" Value="1" />
    <Param ElementID="Maximizer" ParamID="Character" Value="2,20000000" />
    <Param ElementID="Maximizer" ParamID="EnableLowLevelBoost" Value="1" />
    <Param ElementID="Maximizer" ParamID="Gain" Value="2,60000000" />
    <Param ElementID="Maximizer" ParamID="Stereo Link" Value="60,00000000" />
    <Param ElementID="Maximizer" ParamID="Stereo Transient Link Amount" Value="60,00000000" />
    <Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-11,80000000" />
    <Param ElementID="Maximizer" ParamID="Soft Clip Amount" Value="0,00000000" />
    <Param ElementID="Maximizer" ParamID="Soft Clip Enable" Value="0" />
    <ExtraBytes ElementID="Maximizer" Data="" />
</Maximizer>
```

Важно: в проверенных XML Ozone пишет десятичные числа с **запятой**, например `2,60000000`, а не `2.60000000`. При патче лучше сохранять стиль исходного XML.

---

## 3. Главные параметры

| XML ParamID | Что это в интерфейсе / смысл | Что менять |
|---|---|---|
| `Gain` | входной gain Maximizer / основной подъём громкости | **Главный параметр громкости**. Если итог тихий — поднимать его, а не Clip Gain дорожки. |
| `Margin` | Output / Ceiling | Потолок выхода. Для streaming safe обычно `-2,00000000`; для громкой версии `-1,50000000`; для CD/очень громкого теста можно `-1,00000000`, но осторожно. |
| `Prevent Intersample Clipping` | True Peak / inter-sample clipping protection | `1` = True Peak On. Для площадок держать включённым. |
| `Target Loudness [dB]` | Target LUFS / целевая громкость | Это **не главный регулятор звука**. Само по себе изменение Target может почти ничего не изменить, если `Gain` не изменён. |
| `Mode` | режим IRC / алгоритм Maximizer | В наших рабочих пресетах `3` использовался как safe modern streaming-режим. Enum лучше подтверждать визуально в Ozone. |
| `Character` | Character | Управляет характером лимитинга. Меньше/средне — обычно чище для поп/стриминга. |
| `EnableLowLevelBoost` | Upward Compress enable | `1` включает низкоуровневое/восходящее уплотнение, если в GUI оно есть. |
| `LowLevelBoostWetAmount` | Upward Compress amount | Умеренно: `0,80000000`…`1,10000000`. Большие значения могут сделать мастер плотным, но менее естественным. |
| `Stereo Link` | Stereo Link / Stereo Independence связка каналов | 60–70 — безопасный диапазон, но подпись в GUI зависит от версии/режима. Проверять визуально. |
| `Stereo Transient Link Amount` | Transient Link / связка транзиентов | 60–70 — безопасно. Ниже может дать шире/свободнее, выше — стабильнее центр. |
| `Soft Clip Enable` | Soft Clip enable | `0` = выключено. В проекте по умолчанию не включать. |
| `Soft Clip Amount` | Soft Clip amount | Если Soft Clip выключен, держать `0,00000000`. |

---

## 4. Что я реально менял в наших пресетах

### Доченька — safe streaming / no clicks

```xml
<Param ElementID="Maximizer" ParamID="Gain" Value="2,60000000" />
<Param ElementID="Maximizer" ParamID="Margin" Value="-1,50000000" />
<Param ElementID="Maximizer" ParamID="Prevent Intersample Clipping" Value="1" />
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-12,00000000" />
```

### Доченька — финальный streaming wide

```xml
<Param ElementID="Maximizer" ParamID="Gain" Value="3,21384764" />
<Param ElementID="Maximizer" ParamID="Margin" Value="-2,00001144" />
<Param ElementID="Maximizer" ParamID="Prevent Intersample Clipping" Value="1" />
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-12,00000000" />
```

### За хутором — стартовый safe pop

```xml
<Param ElementID="Maximizer" ParamID="Gain" Value="1,20000000" />
<Param ElementID="Maximizer" ParamID="Margin" Value="-2,00001144" />
<Param ElementID="Maximizer" ParamID="LowLevelBoostWetAmount" Value="0,80000000" />
<Param ElementID="Maximizer" ParamID="Character" Value="2,50000000" />
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-12,50000000" />
<Param ElementID="Maximizer" ParamID="Soft Clip Enable" Value="0" />
<Param ElementID="Maximizer" ParamID="Soft Clip Amount" Value="0,00000000" />
```

### За хутором — WOW streaming

```xml
<Param ElementID="Maximizer" ParamID="Gain" Value="2,60000000" />
<Param ElementID="Maximizer" ParamID="Margin" Value="-2,00001144" />
<Param ElementID="Maximizer" ParamID="LowLevelBoostWetAmount" Value="1,10000000" />
<Param ElementID="Maximizer" ParamID="Character" Value="2,20000000" />
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-11,80000000" />
<Param ElementID="Maximizer" ParamID="Stereo Link" Value="60,00000000" />
<Param ElementID="Maximizer" ParamID="Stereo Transient Link Amount" Value="60,00000000" />
<Param ElementID="Maximizer" ParamID="Soft Clip Enable" Value="0" />
<Param ElementID="Maximizer" ParamID="Soft Clip Amount" Value="0,00000000" />
```

---

## 5. Почему в другом чате может «не управляться» Maximizer

### Причина 1. Меняют только `Target Loudness [dB]`

Это частая ошибка. Target — это цель/подсказка для Ozone, но фактическую громкость в XML обычно делает `Gain`.

Правильно:

```xml
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-12,00000000" />
<Param ElementID="Maximizer" ParamID="Gain" Value="3,00000000" />
```

Неправильно:

```xml
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-10,00000000" />
```

Если поменяли только Target, звук может почти не измениться.

### Причина 2. Включён Gain Match в Ozone

Если Gain Match включён, рендер может выйти почти с исходной громкостью, даже если `Gain` поднят. Перед экспортом:

```text
Gain Match: Off
Reference: Off
Codec: Off
Bypass: Off
```

### Причина 3. Maximizer не в `ElementChain`

`Enabled="1"` не гарантирует видимость и работу модуля. Проверять надо `ElementChain`.

### Причина 4. Maximizer не последний

Для финального мастера Maximizer должен быть последним. Если после него стоит Dynamic EQ / Imager / Clarity, итоговый true peak и loudness уже не контролируются Maximizer.

### Причина 5. Пресет закэшировался в Ozone Preset Manager

Использовать уникальное имя/суффикс версии. При подозрении:

```text
1. Удалить старый пресет из Preset Manager.
2. Закрыть Ozone.
3. Открыть Ozone заново.
4. Импортировать XML с новым именем/Comments.
```

### Причина 6. Ableton/Reaper экспортирует не Main/Master или включён Normalize

Проверить:

```text
Rendered Track: Main/Master
Normalize: Off
MP3 Export: Off для релизного WAV
дополнительный limiter после Ozone: нет
```

---

## 6. Готовые профили Maximizer

### Streaming safe

```xml
<Param ElementID="Maximizer" ParamID="Mode" Value="3" />
<Param ElementID="Maximizer" ParamID="Margin" Value="-2,00001144" />
<Param ElementID="Maximizer" ParamID="Prevent Intersample Clipping" Value="1" />
<Param ElementID="Maximizer" ParamID="Character" Value="2,50000000" />
<Param ElementID="Maximizer" ParamID="EnableLowLevelBoost" Value="1" />
<Param ElementID="Maximizer" ParamID="LowLevelBoostWetAmount" Value="0,80000000" />
<Param ElementID="Maximizer" ParamID="Gain" Value="2,50000000" />
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-12,00000000" />
<Param ElementID="Maximizer" ParamID="Soft Clip Enable" Value="0" />
<Param ElementID="Maximizer" ParamID="Soft Clip Amount" Value="0,00000000" />
```

### WOW pop / modern streaming

```xml
<Param ElementID="Maximizer" ParamID="Mode" Value="3" />
<Param ElementID="Maximizer" ParamID="Margin" Value="-2,00001144" />
<Param ElementID="Maximizer" ParamID="Prevent Intersample Clipping" Value="1" />
<Param ElementID="Maximizer" ParamID="Character" Value="2,20000000" />
<Param ElementID="Maximizer" ParamID="EnableLowLevelBoost" Value="1" />
<Param ElementID="Maximizer" ParamID="LowLevelBoostWetAmount" Value="1,10000000" />
<Param ElementID="Maximizer" ParamID="Gain" Value="2,60000000" />
<Param ElementID="Maximizer" ParamID="Stereo Link" Value="60,00000000" />
<Param ElementID="Maximizer" ParamID="Stereo Transient Link Amount" Value="60,00000000" />
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-11,80000000" />
<Param ElementID="Maximizer" ParamID="Soft Clip Enable" Value="0" />
<Param ElementID="Maximizer" ParamID="Soft Clip Amount" Value="0,00000000" />
```

### MP3/codec-safe

```xml
<Param ElementID="Maximizer" ParamID="Mode" Value="3" />
<Param ElementID="Maximizer" ParamID="Margin" Value="-2,50000000" />
<Param ElementID="Maximizer" ParamID="Prevent Intersample Clipping" Value="1" />
<Param ElementID="Maximizer" ParamID="Character" Value="2,50000000" />
<Param ElementID="Maximizer" ParamID="Gain" Value="1,80000000" />
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-12,50000000" />
<Param ElementID="Maximizer" ParamID="Soft Clip Enable" Value="0" />
<Param ElementID="Maximizer" ParamID="Soft Clip Amount" Value="0,00000000" />
```

### Loud probe, не основной финал

```xml
<Param ElementID="Maximizer" ParamID="Mode" Value="3" />
<Param ElementID="Maximizer" ParamID="Margin" Value="-1,50000000" />
<Param ElementID="Maximizer" ParamID="Prevent Intersample Clipping" Value="1" />
<Param ElementID="Maximizer" ParamID="Gain" Value="4,00000000" />
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-11,00000000" />
<Param ElementID="Maximizer" ParamID="Soft Clip Enable" Value="0" />
<Param ElementID="Maximizer" ParamID="Soft Clip Amount" Value="0,00000000" />
```

---

## 7. Мини-чеклист после патча XML

1. Имя/Comments пресета уникальные.
2. Maximizer виден в верхней цепи Ozone.
3. Maximizer стоит последним.
4. `Gain` реально изменён.
5. `Margin` соответствует цели: `-2.0` для streaming safe.
6. `Prevent Intersample Clipping = 1`.
7. `Soft Clip Enable = 0`, если не делается отдельный эксперимент.
8. В Ozone выключены Gain Match / Reference / Codec.
9. В DAW рендерится Main/Master, Normalize Off.
10. После рендера проверить LUFS / True Peak фактического WAV, а не верить только XML.
