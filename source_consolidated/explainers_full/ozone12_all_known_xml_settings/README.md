# Ozone 12 Advanced XML — all-known-settings pack

Назначение: один пакет с рабочей картой понятных XML-параметров Ozone 12 Advanced для проекта `OZONE12_MASTERING_LAB`.

Статус: **рабочая инженерная карта**, а не официальный полный SDK iZotope. Всё, что подтверждено на текущих XML-пресетах, размечено как понятное. Всё, что найдено, но не подтверждено семантически, оставлено как `OBSERVED_UNKNOWN` и не должно меняться вслепую.

## Содержимое

```text
docs/Ozone12_All_Known_XML_Settings_Explainer.md   главный объяснитель
tables/ozone12_observed_param_map.csv              наблюдаемая карта ParamID по текущим XML
tables/module_quick_map.csv                        короткая карта модулей
snippets/*.xml                                     готовые XML-фрагменты по модулям
profiles/*.yaml                                    безопасные профили мастеринга
scripts/*.py                                       Python-утилиты разбора/патча/ElementChain
scripts/powershell/*.ps1                           PowerShell-обёртки
examples/*.md                                      примеры workflow и troubleshooting
```

## Главное

1. Активная цепь — только `Global / ExtraBytes ElementID="ElementChain"`.
2. `Enabled="1"` не означает, что модуль виден/активен в цепи.
3. Порядок модулей влияет на звук.
4. Для FULL-пресетов безопаснее патчить полный XML-шаблон, сохранённый из Ozone.
5. Для DIAG-пресетов безопаснее использовать шаблоны, вручную сохранённые из Ozone.
