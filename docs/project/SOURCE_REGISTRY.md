# Source Registry

## Приоритет

1. Project Instructions.
2. `docs/project/ACTIVE_CURRENT.md`.
3. `docs/00_READ_FIRST_SOURCE_OF_TRUTH.md`.
4. Universal Core v1.3.
5. Generic profiles, tables, validation и tools.
6. Архивные sources — context/reference, но не current authority.

## Активные источники

| Source | Роль | Статус |
|---|---|---|
| `dist/OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1_3.zip` | пакет для ChatGPT Project Sources | ACTIVE |
| unpacked repository tree | редактируемая process-only версия | ACTIVE |
| `docs/project/PROCESS_ONLY_POLICY.md` | граница допустимого знания | ACTIVE |

## Не включается в repository

- названия и тексты произведений;
- исполнители и иные идентификаторы;
- source/final WAV, MP3, AAC;
- per-session filenames и hashes;
- winner XML и точные stage settings;
- per-session LUFS, peaks, correlation и subjective notes;
- P0/environment-lock материалы другого рабочего контура;
- старый Universal Core v1.2 как конкурирующий source.

Рабочие сессионные данные могут использоваться для анализа вне repository. В source-of-truth переносится только обезличенный универсальный вывод.

## Правило обновления

Перед заменой активного source:

1. сохранить предыдущую версию;
2. сравнить содержимое и migration notes;
3. перенести только универсальные знания;
4. выполнить process-only review;
5. обновить manifests/hashes;
6. только затем объявить новую версию ACTIVE.

