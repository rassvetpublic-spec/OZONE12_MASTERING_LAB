# Process-only knowledge policy

## Назначение

Repository хранит универсальные знания о процессе мастеринга, а не историю отдельных произведений или сессий.

## Допустимо

- XML schema, ParamID и enum mappings;
- порядок модулей и workflow;
- Transient/Sustain capabilities;
- formulas, metrics и alignment methods;
- decision heuristics, warnings и hard rejects;
- generic profiles и synthetic examples;
- codec, mono, export и validation procedures;
- инструменты, templates и checklists;
- обезличенные выводы, подтверждённые более чем одной ситуацией или явно ограниченные как review heuristic.

## Не допускается

- названия произведений, тексты и имена исполнителей;
- audio filenames, hashes и media-файлы;
- per-session XML/winner names;
- точные настройки и метрики отдельной сессии;
- субъективные заметки, позволяющие идентифицировать исходный материал;
- перенос единичного результата как universal default.

## Promotion gate

Перед добавлением практического вывода:

1. удалить все идентификаторы сессии;
2. отделить наблюдение от гипотезы;
3. сформулировать schema, procedure, formula, warning или hard reject;
4. указать применимость и ограничения;
5. проверить отсутствие per-session filenames/numbers;
6. обновить manifests и пройти CI.

Данные текущей сессии остаются во внешнем рабочем пространстве и не коммитятся.

Структурная граница проверяется `tools/validate_process_only_scope.py` и GitHub Actions.
