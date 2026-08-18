# Ozone 12 XML: Stabilizer и Stereo Imager Transient/Sustain

Проект: `OZONE12_MASTERING_LAB`  
Назначение: объяснить, какими XML-параметрами управлялись **Stabilizer** и режим **Transient/Sustain**.

## 0. Главная поправка

В Ozone 12 Advanced режим **Transient/Sustain** относится не к `Stabilizer`, а к модулю:

```text
Stereo Imager
```

`Stabilizer` в наших XML-пресетах управлялся отдельными параметрами:

```text
ElementID="Stabilizer"
ParamID="Amount"
ParamID="Target"
ParamID="Auto Gain Enable"
```

А ширина Transient/Sustain управлялась параметрами:

```text
ElementID="Stereo Imager"
ParamID="Band N Width Percent"        # Transient
ParamID="Aux: Band N Width Percent"   # Sustain
```

Если в другом чате пытаются управлять **Transient/Sustain через Stabilizer**, ничего ожидаемого не получится: это другой модуль.

---

# 1. Активная цепь: сначала проверить `ElementChain`

Перед правкой нельзя ориентироваться только на:

```xml
Enabled="1"
```

Модуль может быть сохранён в XML и иметь `Enabled="1"`, но не быть в видимой цепи Ozone. Активную цепочку надо проверять по:

```text
Global / ExtraBytes ElementID="ElementChain"
```

Для FULL-пресета модуль должен быть виден в верхней цепочке Ozone. Если `Stereo Imager` или `Stabilizer` отсутствует в `ElementChain`, правка их параметров может не влиять на звук.

---

# 2. Stereo Imager: включение режима Transient/Sustain

В проверенных XML с режимом Transient/Sustain встречались такие параметры:

```xml
<Param ElementID="Stereo Imager" ParamID="Processing Mode" Value="1" />
<Param ElementID="Stereo Imager" ParamID="Transient/Sustain Selection" Value="1" />
```

Рабочая интерпретация по нашим пресетам:

| ParamID | Смысл |
|---|---|
| `Processing Mode` | режим обработки Imager; `1` использовался для Transient/Sustain |
| `Transient/Sustain Selection` | выбранная вкладка/представление T/S в UI; в наших T/S-пресетах стояло `1` |

Важно: если в XML есть width-параметры, но `Processing Mode` не переведён в T/S-режим, UI может отображать/использовать не то, что ожидается.

---

# 3. Stereo Imager: Transient vs Sustain

В наших XML принцип такой:

## 3.1 Transient — обычные `Band N Width Percent`

```xml
<Param ElementID="Stereo Imager" ParamID="Band 1 Width Percent" Value="-20,00000000" />
<Param ElementID="Stereo Imager" ParamID="Band 2 Width Percent" Value="0,00000000" />
<Param ElementID="Stereo Imager" ParamID="Band 3 Width Percent" Value="8,00000000" />
<Param ElementID="Stereo Imager" ParamID="Band 4 Width Percent" Value="5,00000000" />
```

Это ширина **транзиентов**: атаки kick/snare, щелчки, согласные, клики, резкие начала звука.

## 3.2 Sustain — `Aux: Band N Width Percent`

```xml
<Param ElementID="Stereo Imager" ParamID="Aux: Band 1 Width Percent" Value="-5,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Band 2 Width Percent" Value="22,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Band 3 Width Percent" Value="72,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Band 4 Width Percent" Value="52,00000000" />
```

Это ширина **сустейна**: хор, пад, орган, оркестр, реверберации, хвосты, атмосферный слой.

---

# 4. Recover Sides в Transient/Sustain

В T/S-режиме есть две группы Recover Sides:

## 4.1 Transient Recover Sides

```xml
<Param ElementID="Stereo Imager" ParamID="Recover Sides Enabled" Value="1" />
<Param ElementID="Stereo Imager" ParamID="Recover Sides Gain Offset (dB)" Value="0,00000000" />
```

Для борьбы с цоканьем/кликами Transient Recover Sides лучше держать около нуля.

## 4.2 Sustain Recover Sides

```xml
<Param ElementID="Stereo Imager" ParamID="Aux: Recover Sides Enabled" Value="1" />
<Param ElementID="Stereo Imager" ParamID="Aux: Recover Sides Gain Offset (dB)" Value="1,20000000" />
```

Sustain Recover Sides можно поднимать умеренно, чтобы расширить хор/пады/хвосты. В нашем workflow без отдельного теста не поднимать выше `+1.2 dB`.

---

# 5. Stereoize: отдельный опасный параметр

Для готового stereo SUNO WAV по умолчанию:

```xml
<Param ElementID="Stereo Imager" ParamID="Enable Stereoizer" Value="0" />
```

Если в XML нет `Enable Stereoizer`, но есть:

```xml
<Param ElementID="Stereo Imager" ParamID="Stereoizer Mode" Value="1" />
```

это не обязательно значит, что Stereoize включён. Надёжнее явно иметь `Enable Stereoizer = 0` или проверить GUI.

---

# 6. Stereo Imager: частоты кроссоверов

```xml
<Param ElementID="Stereo Imager" ParamID="Crossover Cutoff 1" Value="165,00000000" />
<Param ElementID="Stereo Imager" ParamID="Crossover Cutoff 2" Value="3000,00000000" />
<Param ElementID="Stereo Imager" ParamID="Crossover Cutoff 3" Value="12000,00000000" />
```

Практическая логика:

| Полоса | Диапазон | Что делать |
|---|---:|---|
| Band 1 | до ~160 Hz | низ держать уже / почти mono |
| Band 2 | ~160 Hz–3 kHz | осторожно, вокал/тело микса |
| Band 3 | ~3–12 kHz | основная зона ширины хора/атмосферы |
| Band 4 | выше ~12 kHz | осторожно, там воздух и цифровая пыль |

---

# 7. Module Amount

```xml
<Param ElementID="Stereo Imager" ParamID="Module Amount" Value="60,00000000" />
```

`Module Amount` — общий масштаб влияния Imager. Если ширина почти не меняется, но Band Width прописаны, проверить:

1. `Module Amount` не слишком низкий;
2. `Processing Mode = 1`;
3. `Stereo Imager` реально в `ElementChain`;
4. нет `Gain Match`, `Bypass`, `Reference`, `Codec` при рендере.

---

# 8. Stabilizer: реальные XML-параметры

В наших пресетах реально менялись эти параметры:

```xml
<Param ElementID="Stabilizer" ParamID="Amount" Value="20,00000000" />
<Param ElementID="Stabilizer" ParamID="Target" Value="10" />
<Param ElementID="Stabilizer" ParamID="Auto Gain Enable" Value="1" />
```

## 8.1 Amount

```xml
<Param ElementID="Stabilizer" ParamID="Amount" Value="14,00000000" />
```

Общая сила Stabilizer.

Примерные рабочие диапазоны:

| Задача | Amount |
|---|---:|
| Dark / less processed | `8–12` |
| Safe streaming | `14–18` |
| Open / polished | `20–24` |

## 8.2 Target

```xml
<Param ElementID="Stabilizer" ParamID="Target" Value="10" />
```

`Target` — профиль/целевая кривая Stabilizer. Значения enum не считать универсально подтверждёнными без проверки GUI. В наших XML встречались, например:

```text
Target = 10
Target = 27
```

В одном проекте `Target = 10` визуально соответствовал одному профилю, в другом `Target = 27` использовался как сохранённый профиль. Поэтому:

```text
Target менять только если есть проверенный XML-шаблон или скрин GUI.
```

Если нужно управлять предсказуемо — менять `Amount`, а `Target` оставить как в рабочем исходном XML.

## 8.3 Auto Gain Enable

```xml
<Param ElementID="Stabilizer" ParamID="Auto Gain Enable" Value="1" />
```

Обычно оставлять `1`, чтобы модуль не менял громкость непредсказуемо. Но итог всё равно проверять по WAV-рендеру.

---

# 9. Типовые ошибки, почему “не получается управлять”

## Ошибка 1. Перепутан модуль

Пытаются менять `Stabilizer`, ожидая изменения Transient/Sustain. Правильно: Transient/Sustain находится в `Stereo Imager`.

## Ошибка 2. Меняют Sustain-параметры, но режим Imager не T/S

Нужно проверить:

```xml
<Param ElementID="Stereo Imager" ParamID="Processing Mode" Value="1" />
```

## Ошибка 3. Меняют `Aux:` не понимая, что это Sustain

`Aux: Band N Width Percent` — это Sustain, а не дополнительная обычная полоса.

## Ошибка 4. Модуль не в ElementChain

Если `Stereo Imager` / `Stabilizer` отсутствует в `ElementChain`, изменение параметров может не проявиться.

## Ошибка 5. Ozone Preset Manager подтягивает кэш старого пресета

Использовать уникальные имена версий:

```text
*_V1.xml
*_V2.xml
*_V3.xml
```

## Ошибка 6. Включён Gain Match

При сравнении/рендере `Gain Match` может скрыть изменение громкости/восприятия. Перед рендером:

```text
Gain Match Off
Reference Off
Codec Off
Bypass Off
```

---

# 10. Проверенный пример Wide Strong

```xml
<Param ElementID="Stereo Imager" ParamID="Processing Mode" Value="1" />
<Param ElementID="Stereo Imager" ParamID="Transient/Sustain Selection" Value="1" />
<Param ElementID="Stereo Imager" ParamID="Module Amount" Value="58,00000000" />

<!-- Transient -->
<Param ElementID="Stereo Imager" ParamID="Band 1 Width Percent" Value="-20,00000000" />
<Param ElementID="Stereo Imager" ParamID="Band 2 Width Percent" Value="0,00000000" />
<Param ElementID="Stereo Imager" ParamID="Band 3 Width Percent" Value="8,00000000" />
<Param ElementID="Stereo Imager" ParamID="Band 4 Width Percent" Value="5,00000000" />
<Param ElementID="Stereo Imager" ParamID="Recover Sides Gain Offset (dB)" Value="0,00000000" />

<!-- Sustain -->
<Param ElementID="Stereo Imager" ParamID="Aux: Band 1 Width Percent" Value="-5,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Band 2 Width Percent" Value="22,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Band 3 Width Percent" Value="72,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Band 4 Width Percent" Value="52,00000000" />
<Param ElementID="Stereo Imager" ParamID="Aux: Recover Sides Gain Offset (dB)" Value="1,20000000" />
```

---

# 11. Мини-чеклист после импорта XML

1. Открыть Ozone.
2. Проверить, что `Stereo Imager` и/или `Stabilizer` видны в верхней цепи.
3. Проверить, что Imager в режиме `Transient/Sustain`, если правились T/S параметры.
4. Проверить, что `Stereoize` выключен.
5. Проверить Recover Sides: Transient около `0`, Sustain не выше `+1.2 dB` без спец-теста.
6. Проверить Stabilizer Amount и Target глазами.
7. Перед рендером: `Gain Match Off`, `Reference Off`, `Codec Off`, `Normalize Off`.
8. После рендера проверять WAV-метрики: LUFS, True Peak, correlation, Side/Mid, mono.
