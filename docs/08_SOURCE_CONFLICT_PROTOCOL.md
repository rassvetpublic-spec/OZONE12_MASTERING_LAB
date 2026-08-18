# 08. Source Conflict Protocol

## Registry first

Для нового или продолженного трека создать `source_registry.md`:

```text
file | role | status | what read | risk | can base decisions on it
```

Минимум: source WAV, optional MP3 reference, current base/winner Ozone XML, creative task/style, previous accepted render/report при продолжении.

## Missing input

Не выдумывать:

```text
нет source WAV → MP3 можно анализировать, но он не становится lossless mastering source
нет base XML → нельзя гарантировать безопасный patch существующей цепи
нет current winner → выбрать его явно или вернуться к последнему принятому XML
нет render → нельзя утверждать, что XML-параметр дал ожидаемый DSP-результат
```

## Conflict priority

Если старый explainer/archive конфликтует с Universal Core v1.3, active `docs/`, `skills/`, `tables/` v1.3 выше. Архив остаётся evidence/reference.

Если пользователь сохранил ручной GUI XML и явно выбрал его, он выше прежнего сгенерированного кандидата для этого трека. Это не делает его universal preset.

## Track boundary

Конкретные WAV/XML, exact gains, winners, LUFS и codec trims относятся только к своему треку. В Universal Core переносятся только схема, процедура, reject-признак или обобщённая эвристика.
