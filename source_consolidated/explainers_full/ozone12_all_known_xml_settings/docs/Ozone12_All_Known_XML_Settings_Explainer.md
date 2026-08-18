# Ozone 12 Advanced XML — подробный объяснитель понятных параметров

Проект: `OZONE12_MASTERING_LAB`  
Статус: рабочая карта параметров, подтверждённая на текущих XML-пресетах проекта.

## 0. Ограничения

Это не официальный полный SDK iZotope. Это практическая карта XML-параметров, которые уже встречались в рабочих пресетах и которыми мы управляли при мастеринг-вилках.

Правило безопасности:

```text
Понятные параметры можно менять.
Непонятные enum/ExtraBytes — не трогать без GUI-подтверждения или шаблона, сохранённого из Ozone.
```

---

## 1. Активная цепь: ElementChain

Главное правило Ozone XML:

```text
НЕ определять активную цепь по Enabled="1".
Активная видимая цепь задаётся Global / ExtraBytes ElementID="ElementChain".
```

Проверенная структура `ElementChain`:

```text
[00][uint32 little-endian длина имени][UTF-8 имя модуля]
[00][uint32 little-endian длина имени][UTF-8 имя модуля]
...
```

В начале **нет отдельного count-prefix**. Добавление счётчика ломало пресеты и давало пустую цепь.

Безопасная полная цепь для готового SUNO stereo WAV:

```text
Master Rebalance → Equalizer → Impact → Clarity → Stabilizer → Stereo Imager → Dynamic EQ → Maximizer
```

Иногда auto-цепь Ozone ставит `Stereo Imager` раньше `Clarity/Stabilizer`. Это может звучать шире, но рискованнее: сначала расширяется ещё не стабилизированный верх/резкость.

---

## 2. Формат чисел в XML

В текущих XML Ozone часто использует десятичную запятую:

```xml
Value="-2,00001144"
```

Скрипты должны сохранять такой формат. Не превращать весь файл в другой формат без необходимости.

---

## 3. Global / ExtraBytes

### `ElementChain`

```xml
<ExtraBytes ElementID="ElementChain" Data="...base64..." />
```

Роль: видимый порядок модулей в верхней цепи Ozone.

Что можно:
- читать;
- декодировать;
- валидировать;
- пересобирать только если точно знаешь структуру и есть проверка в Ozone.

Что нельзя:
- добавлять count-prefix;
- удалять модули вручную без шаблона, если нет опыта с данным XML;
- считать `Enabled=1` заменой ElementChain.

---

## 4. Master Rebalance

Роль: мягко сдвинуть баланс готового stereo mix по вокалу/басу/ударным.

Понятные параметры:

| ParamID | Смысл | Как менять | Риск |
|---|---|---:|---|
| `SourceGain` | Gain выбранного источника, dB | обычно `-1.0…+1.0` | AI/separation артефакты, вокал/ударные могут поплыть |
| `SourceType` | enum выбранного источника | только через GUI/шаблон | enum не подтверждать наугад |
| `Auto Gain Enable` | автокомпенсация | обычно `1` | при выключении меняется громкость сравнения |

Пример:

```xml
<Param ElementID="Master Rebalance" ParamID="SourceType" Value="0" />
<Param ElementID="Master Rebalance" ParamID="SourceGain" Value="0,50000000" />
<Param ElementID="Master Rebalance" ParamID="Auto Gain Enable" Value="1" />
```

Примечание: `SourceType` нужно сверять по скриншоту/GUI. В разных пресетах наблюдались `0` и `2`.

---

## 5. Equalizer

Роль: статический тональный баланс до динамики/ширины.

Паттерн параметров:

```xml
<Param ElementID="Equalizer" ParamID="Band 4 Frequency" Value="3200,00000000" />
<Param ElementID="Equalizer" ParamID="Band 4 Gain" Value="-0,40000000" />
<Param ElementID="Equalizer" ParamID="Band 4 Q" Value="1,50000000" />
<Param ElementID="Equalizer" ParamID="Band 4 Enable" Value="1" />
```

Понятные поля:

| ParamID pattern | Смысл |
|---|---|
| `Band N Frequency` | частота полосы |
| `Band N Gain` | усиление/срез dB |
| `Band N Q` | ширина полосы |
| `Band N Enable` | включение полосы |
| `Band N Shape` | форма фильтра, enum; не менять вслепую |
| `Band N Visible` | видимость в GUI, обычно не аудио-критично |
| `Gain Scaling Amount` | масштаб всей EQ-кривой |

Безопасная логика:

```text
30 Hz     мягкий low cut / sub control
180–500   mud / boxiness
1.5–4 kHz vocal presence / harshness
6–12 kHz  clicks / harshness / AI sparkle
12–18 kHz air, осторожно
```

Не лечить всё статическим EQ. Для всплесков использовать `Dynamic EQ`.

---

## 6. Impact

Роль: микродинамика, плотность, транзиенты/sustain по полосам.

Понятные параметры:

| ParamID | Смысл | Безопасно |
|---|---|---:|
| `GlobalAmount` | общий amount | `18…40` |
| `Envelope` | интенсивность/форма envelope | `45…65` |
| `Aux: Envelope` | связанный envelope-параметр | держать равным `Envelope`, если есть |
| `Band N Amount` | amount полосы | low/mid умеренно, top осторожно |
| `Crossover Cutoff 1/2/3` | частоты раздела полос | менять только осознанно |
| `Auto Gain Enable` | автокомпенсация | обычно `1` |

Пример soft impact:

```xml
<Param ElementID="Impact" ParamID="GlobalAmount" Value="23,00000000" />
<Param ElementID="Impact" ParamID="Envelope" Value="50,00000000" />
<Param ElementID="Impact" ParamID="Aux: Envelope" Value="50,00000000" />
<Param ElementID="Impact" ParamID="Band 1 Amount" Value="-8,00000000" />
<Param ElementID="Impact" ParamID="Band 2 Amount" Value="17,00000000" />
<Param ElementID="Impact" ParamID="Band 3 Amount" Value="19,00000000" />
<Param ElementID="Impact" ParamID="Band 4 Amount" Value="3,00000000" />
```

Риски:
- высокий `Band 4 Amount` может вернуть цоканье;
- высокий `GlobalAmount` + высокий Maximizer Gain может дать pumping;
- слишком сильный soft-вариант может сделать припев вялым.

---

## 7. Clarity

Роль: полировка/разборчивость без грубого EQ.

Параметры:

| ParamID | Смысл | Безопасно |
|---|---|---:|
| `Amount` | сила Clarity | `10…28` |
| `Tilt` | тональная направленность | dark: `-1.6…-0.8`, pop/open: `-0.3…+0.1` |
| `Auto Gain Enable` | автокомпенсация | `1` |

Пример:

```xml
<Param ElementID="Clarity" ParamID="Amount" Value="24,00000000" />
<Param ElementID="Clarity" ParamID="Tilt" Value="0,05000000" />
<Param ElementID="Clarity" ParamID="Auto Gain Enable" Value="1" />
```

Риски:
- слишком много = стерильно/глянцево;
- положительный Tilt может вернуть sibilance/AI sparkle;
- не дублировать то же, что уже давит Dynamic EQ.

---

## 8. Stabilizer

Роль: стабилизация тонального баланса.

Параметры:

| ParamID | Смысл | Безопасно |
|---|---|---:|
| `Amount` | сила обработки | `8…24` |
| `Target` | профиль/target curve enum | менять только через GUI/проверенный XML |
| `Auto Gain Enable` | автокомпенсация | `1` |

Пример:

```xml
<Param ElementID="Stabilizer" ParamID="Amount" Value="20,00000000" />
<Param ElementID="Stabilizer" ParamID="Target" Value="10" />
<Param ElementID="Stabilizer" ParamID="Auto Gain Enable" Value="1" />
```

Важно:

```text
Transient/Sustain — НЕ Stabilizer.
Transient/Sustain находится в Stereo Imager.
```

Если в другом чате правят `ElementID="Stabilizer"` и ждут управления T/S-шириной — это ошибка.

---

## 9. Stereo Imager и Transient/Sustain

Роль: ширина без потери центра.

### 9.1 Ключевой режим

```xml
<Param ElementID="Stereo Imager" ParamID="Processing Mode" Value="1" />
```

В наших рабочих пресетах `Processing Mode=1` соответствует режиму `Transient/Sustain`. Если режим не включён, `Aux:` параметры могут не влиять как sustain-ветка.

### 9.2 Transient vs Sustain

| XML | Что это |
|---|---|
| `Band N Width Percent` | Transient / normal branch |
| `Aux: Band N Width Percent` | Sustain branch |
| `Recover Sides Gain Offset (dB)` | transient/normal recover sides |
| `Aux: Recover Sides Gain Offset (dB)` | sustain recover sides |

Пример широкой, но безопасной T/S-логики:

```xml
<Param ElementID="Stereo Imager" ParamID="Processing Mode" Value="1" />
<Param ElementID="Stereo Imager" ParamID="Enable Stereoizer" Value="0" />

<!-- Transient: атаки держим собраннее -->
<Param ElementID="Stereo Imager" ParamID="Band 1 Width Percent" Value="-20,00000000" />
<Param ElementID="Stereo Imager" ParamID="Band 2 Width Percent" Value="0,00000000" />
<Param ElementID="Stereo Imager" ParamID="Band 3 Width Percent" Value="8,00000000" />
<Param ElementID="Stereo Imager" ParamID="Band 4 Width Percent" Value="5,00000000" />
<Param ElementID="Stereo Imager" ParamID="Recover Sides Gain Offset (dB)" Value="0,00000000" />

<!-- Sustain: хор/синты/хвосты шире -->
<Param ElementID="Stereo Imager" ParamID="Aux: Band 1 Width Percent" Value="-5,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Band 2 Width Percent" Value="22,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Band 3 Width Percent" Value="72,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Band 4 Width Percent" Value="52,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Recover Sides Gain Offset (dB)" Value="1,20000000" />
```

### 9.3 Crossovers

```xml
<Param ElementID="Stereo Imager" ParamID="Crossover Cutoff 1" Value="165,00000000" />
<Param ElementID="Stereo Imager" ParamID="Crossover Cutoff 2" Value="3000,00000000" />
<Param ElementID="Stereo Imager" ParamID="Crossover Cutoff 3" Value="12000,00000000" />
```

Логика:
- до 120–180 Hz держать низ стабильно/уже;
- vocal center не расширять агрессивно;
- sustain шире transient;
- `Stereoize` по умолчанию `0`;
- `Recover Sides` обычно не выше `+1.2 dB`.

---

## 10. Dynamic EQ

Роль: финальный динамический контроль мути/сибилянтов/цоканья перед Maximizer.

Паттерн:

```xml
<Param ElementID="Dynamic EQ" ParamID="Band 5 Frequency" Value="7200,00000000" />
<Param ElementID="Dynamic EQ" ParamID="Band 5 Gain" Value="-1,40000000" />
<Param ElementID="Dynamic EQ" ParamID="Band 5 Q" Value="4,50000000" />
<Param ElementID="Dynamic EQ" ParamID="Band 5 Threshold" Value="-26,00000000" />
<Param ElementID="Dynamic EQ" ParamID="Band 5 Enable" Value="1" />
```

Понятные поля:

| ParamID pattern | Смысл |
|---|---|
| `Band N Frequency` | частота обработки |
| `Band N Gain` | величина среза/усиления |
| `Band N Q` | ширина полосы |
| `Band N Threshold` | порог срабатывания |
| `Band N Enable` | включение полосы |
| `Band N Shape` | форма фильтра, enum; осторожно |
| `Band N Visible` | GUI visibility |

Рабочие зоны:

```text
200–500 Hz   муть/гулкость
2–4 kHz      вокальная агрессия
5–8 kHz      сибилянты/щелчки
8–12 kHz     AI sparkle / harshness
12–16 kHz    воздух без стекла
```

Важно: если меняешь только `Gain`, но `Threshold` не даёт полосе срабатывать, на рендере может почти не быть разницы.

---

## 11. Maximizer

Роль: финальная громкость, потолок, True Peak.

Ключевые параметры:

| ParamID | Смысл | Безопасно |
|---|---|---:|
| `Gain` | главный подъём громкости | `1.0…3.5 dB` streaming, выше — loud probe |
| `Margin` | Output/Ceiling | `-2.0 dBTP` safe, `-1.5` louder, `-1.0` risky |
| `Prevent Intersample Clipping` | True Peak | `1` |
| `Target Loudness [dB]` | цель/подсказка LUFS | `-12.5…-11.5` |
| `Mode` | режим IRC enum | observed `3`; сверять GUI |
| `Character` | характер/скорость | `2.0…3.0` |
| `EnableLowLevelBoost` | Upward Compress enable | `0/1` |
| `LowLevelBoostWetAmount` | Upward Compress amount | `0.5…1.3` |
| `Stereo Link` | link/independence | `50…70` |
| `Stereo Transient Link Amount` | transient link | `50…70` |
| `Soft Clip Enable` | Soft Clip | `0` default |
| `Soft Clip Amount` | Soft Clip amount | `0` default |

Пример safe streaming:

```xml
<Param ElementID="Maximizer" ParamID="Gain" Value="2,60000000" />
<Param ElementID="Maximizer" ParamID="Margin" Value="-2,00001144" />
<Param ElementID="Maximizer" ParamID="Prevent Intersample Clipping" Value="1" />
<Param ElementID="Maximizer" ParamID="Target Loudness [dB]" Value="-12,00000000" />
<Param ElementID="Maximizer" ParamID="Character" Value="2,50000000" />
<Param ElementID="Maximizer" ParamID="Soft Clip Enable" Value="0" />
<Param ElementID="Maximizer" ParamID="Soft Clip Amount" Value="0,00000000" />
```

Самая частая ошибка:

```text
Меняют Target Loudness, но не меняют Gain.
```

Тогда выход может почти не измениться. Итоговый LUFS всегда проверять по отрендеренному WAV.

---

## 12. Less-confirmed / non-default modules

В текущих XML также встречались:

```text
Bass Control
Low End Focus
Spectral Shaper
Stem EQ
Unlimiter
Dynamics
Exciter
Post Equalizer
```

Но для текущего OZONE12_MASTERING_LAB они не являются базовой активной цепью. Если они `Enabled="1"`, но отсутствуют в `ElementChain`, не считать их активными.

Правило:

```text
Не патчить эти модули как часть мастеринг-цепи, пока они не подтверждены в ElementChain и GUI.
```

---

## 13. Проверка перед рендером

```text
1. Имя пресета уникальное.
2. Ozone показывает нужную цепь сверху.
3. Цепь не пустая.
4. Maximizer последний.
5. Gain Match Off.
6. Reference Off.
7. Codec Off.
8. Normalize в DAW Off.
9. Нет FX до/после Ozone.
10. WAV 24-bit / 48 kHz.
```

---

## 14. Диагностика “не работает”

| Симптом | Вероятная причина |
|---|---|
| Меняю Maximizer Target, LUFS не меняется | не изменён `Gain`, включён Gain Match, рендер не через Main |
| Меняю T/S через Stabilizer | T/S находится в Stereo Imager, не Stabilizer |
| Меняю Aux Band Width, но ширина не меняется | Imager не в Processing Mode=1 / не в ElementChain |
| Пресет загружается пустым | сломан ElementChain / добавлен лишний count-prefix |
| Ozone показывает старые настройки | кэш Preset Manager, имя пресета не уникальное |
| FULL/DIAG ведёт себя странно | нельзя надёжно “выключать” через Bypass; нужен Ozone-сохранённый шаблон |

---

## 15. Приоритет параметров для вилок

Самые полезные для ежедневных вилок:

1. `Stereo Imager`: T/S width + Recover Sides.
2. `Impact`: GlobalAmount, Envelope, Band amounts.
3. `Dynamic EQ`: Frequency/Gain/Q/Threshold проблемных полос.
4. `Clarity` + `Stabilizer`: Amount/Tilt/Amount.
5. `Maximizer`: Gain/Margin/True Peak.

Не делать все вилки сразу. Менять один блок за прогон, иначе нельзя понять, что сработало.
