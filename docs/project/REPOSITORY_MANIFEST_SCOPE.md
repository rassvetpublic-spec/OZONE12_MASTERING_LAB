# Manifest scope

`MANIFEST.csv`, `MANIFEST_SHA256.csv` и `validation/FILE_AUDIT.csv` фиксируют текущее process-only GitHub-дерево проекта и включают:

- `docs/project/`;
- `dist/`;
- repository-level CI/configuration.

Контрольные файлы manifests не включают сами себя, чтобы избежать рекурсивного хэша.

Исходный побайтовый Universal Core v1.3 сохранён неизменным в:

```text
dist/OZONE12_MASTERING_LAB_UNIVERSAL_CORE_v1_3.zip
```

Его внутренние manifests являются authority для исходного package snapshot.

