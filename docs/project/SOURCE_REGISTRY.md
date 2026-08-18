# Source Registry

## Приоритет

1. Project Instructions.
2. `docs/project/ACTIVE_CURRENT.md`.
3. `docs/project/ARCHITECTURE_v1.md` for runtime/P0 decisions.
4. `docs/00_READ_FIRST_SOURCE_OF_TRUTH.md` for mastering process/source rules.
5. Universal Core v1.3.
6. Generic profiles, tables, validation и tools.
7. Архивные sources — context/reference, но не current authority.

## Активные источники

| Source | Роль | Статус |
|---|---|---|
| `docs/project/ACTIVE_CURRENT.md` | текущее состояние и следующий gate | ACTIVE |
| `docs/project/ARCHITECTURE_v1.md` | runtime architecture и mandatory P0 Gate | ACTIVE / APPROVED |
| `docs/project/PROCESS_ONLY_POLICY.md` | граница допустимого знания | ACTIVE |
| unpacked repository tree | редактируемая process-only версия | ACTIVE |
| `dist/OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1_3.zip` | frozen process package для ChatGPT Project Sources | ACTIVE / FROZEN v1.3 |

## Разделение process и runtime evidence

В repository допускаются:

- универсальная runtime architecture;
- generic P0/Dry Harness/L0–L4/S2/Render Gate protocols;
- environment schema и version-lock requirements;
- детерминированные synthetic fixtures и reusable validators;
- обезличенные acceptance criteria и failure procedures.

В repository не включаются:

- названия, тексты и исполнители произведений;
- source/final WAV, MP3, AAC;
- per-session filenames/hashes и winner XML;
- точные per-session settings, metrics и subjective notes;
- machine-specific RPP, logs, paths, dumps, license/credential data;
- raw P0 evidence конкретной рабочей станции;
- старый Universal Core v1.2 как конкурирующий source.

Рабочие и P0 evidence могут использоваться локально. В repository публикуется только универсальный protocol, schema, status или обезличенный переносимый вывод.

## Frozen package rule

Universal Core v1.3 имеет зафиксированный hash и не перезаписывается architecture-only изменениями. `ARCHITECTURE_v1.md` является текущей repository authority и не объявляется содержимым frozen v1.3 ZIP.

Для включения architecture/P0 knowledge в ChatGPT Project Sources необходимо:

1. выпустить новую версию Sources package;
2. сохранить предыдущий archive;
3. подготовить migration notes;
4. обновить hash/manifests;
5. только затем объявить новый package ACTIVE.

## Правило обновления current authority

Перед изменением активного source:

1. проверить `ACTIVE_CURRENT` и source priority;
2. сохранить предыдущую версию;
3. сравнить содержимое и migration impact;
4. перенести только универсальные знания;
5. выполнить process-only review;
6. обновить manifests/hashes и пройти CI;
7. явно отметить статус `ACTIVE`, `FROZEN`, `SUPERSEDED` или `REFERENCE`.

