# Troubleshooting Ozone 12 XML patching

## 1. Параметр изменился в XML, но в Ozone не видно эффекта

Проверить:

1. Модуль есть в `ElementChain`?
2. Имя пресета уникальное?
3. Нет ли кэша Ozone Preset Manager?
4. Не включён ли `Gain Match`?
5. Рендер идёт через `Main/Master`?
6. Параметр не GUI-only?
7. Для Dynamic EQ: срабатывает ли Threshold?
8. Для Imager T/S: `Processing Mode=1`?

## 2. Цепь пустая

Вероятно сломан `ElementChain`. Не добавлять count-prefix. Структура: `00 + uint32 little-endian length + UTF-8 module name`, повтор.

## 3. DIAG/FULL

Для DIAG использовать шаблоны, сохранённые в Ozone. Не пытаться надёжно выключать лишние модули через Bypass.

## 4. Проверка после импорта XML

Перед рендером открыть Ozone и визуально проверить верхнюю цепь.
