# Hikma Questions

Community-driven multilingual QCM repository. Questions are organized by topic and compiled into a JSON bundle consumed by the quiz app.

## Structure

```text
indexes/
├── catalog.yaml        — schema version, supported languages
├── ar.yaml             — Arabic question index
├── en.yaml             — English question index
└── fr.yaml             — French question index

questions/
├── general/
│   └── qcm-0001/
│       ├── metadata.yaml
│       ├── en.md
│       ├── ar.md
│       └── fr.md
└── din-fitra/
    └── qcm-din-fitra-0031/
        ├── metadata.yaml
        └── ar.md

scripts/
├── build.py            — generates dist/questions.json
└── validate.py         — validates question structure

dist/
└── questions.json      — compiled bundle (auto-generated, do not edit manually)
```

## Conventions

- Each question lives in `questions/{topic}/{id}/`.
- Language files (`{lang}.md`) are placed directly in the question folder — no subdirectory.
- There is **no required source language**: a question can exist in any subset of languages. Declare available languages in `metadata.yaml → languages`.
- `metadata.yaml` is **required** for every question.

## Question format (`{lang}.md`)

```markdown
# Question

Question text here.

## Choices

- Choice A
- Choice B
- Choice C
- Choice D

## Answer

3

## Explanation

Explanation of the correct answer.
```

> `Answer` is a **1-based index** (1 = first choice). The build script converts it to 0-based in the JSON output.

## `metadata.yaml` format

```yaml
id: qcm-0001
topic: general              # matches the parent folder name
difficulty: easy            # easy | medium | hard
tags:
  - geography
languages:
  - en
  - ar
  - fr
source: null                # optional: book, hadith, or other reference
created_at: 2026-01-01      # ISO 8601 date
version: 1                  # increment when question content changes
```

## Build

```bash
python3 scripts/build.py
```

Generates `dist/questions.json`. The pre-commit hook runs this automatically on every commit.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
