# 12. No Track-Specific Data Policy

В Universal Core нельзя включать как default/rule:

```text
названия конкретных песен
финальные WAV/MP3 конкретных песен
точные gains/width/thresholds одного winner
частные LUFS, Side/Mid или codec trims одного трека
конкретные stage XML как обязательный preset
```

Можно включать:

```text
подтверждённую XML schema
обобщённые failures and hard rejects
workflow, formula and audit method
generic profile without fixed track values
эвристику с явной пометкой warning, а не absolute threshold
anonymized validation evidence outside active defaults
```

Перед добавлением опыта спросить: повторится ли правило на другом материале и описывает ли оно процедуру/риск, а не вкус одного трека?

`source_consolidated/` — архивный reference ниже active `docs/`, `skills/`, `tables/`.
