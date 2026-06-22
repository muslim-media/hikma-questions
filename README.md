# Hikma Questions

Community-driven multilingual QCM repository.

## Structure

```text
indexes/
├── catalog.yaml
├── en.yaml
├── fr.yaml
└── ar.yaml

questions/
├── qcm-0001/
│   ├── metadata.yaml
│   ├── en.md
│   └── translations/
│       ├── fr.md
│       └── ar.md
│
└── qcm-0002/
    ├── metadata.yaml
    ├── en.md
    └── translations/
        ├── fr.md
        └── ar.md
```

## Conventions

- `en.md` is the source language.
- `translations/` contains translated versions.
- `indexes/catalog.yaml` stores global metadata.
- `indexes/<lang>.yaml` lists available questions for each language.
