# Contributing to Hikma Questions

## Adding a new question

### 1. Choose a topic and ID

Topics are folder names under `questions/`. Use an existing topic or create a new one.

ID format: `{topic-prefix}-{4-digit-number}` — e.g., `qcm-0003`, `qcm-din-fitra-0034`.

### 2. Create the question folder

```
questions/{topic}/{id}/
```

### 3. Write `metadata.yaml`

```yaml
id: qcm-0003
topic: general
difficulty: easy            # easy | medium | hard
tags:
  - your-tag
languages:
  - en                      # list every language you provide
source: null                # optional: "Book Title, p.42"
created_at: 2026-06-22      # today's date
version: 1
```

### 4. Write language files (`{lang}.md`)

One file per language declared in `metadata.yaml`. Template:

```markdown
# Question

Your question text here.

## Choices

- Option A
- Option B
- Option C
- Option D

## Answer

2

## Explanation

Why this is the correct answer.
```

Rules:
- `Answer` must be a **1-based integer** (1 = first choice).
- At least 2 choices; 4 is the recommended default.
- `Explanation` is required.

### 5. Update the language index

Add the question to `indexes/{lang}.yaml` for each language you provide:

```yaml
  - id: qcm-0003
    difficulty: easy
    tags:
      - your-tag
```

### 6. Validate and build

```bash
python3 scripts/validate.py   # checks structure
python3 scripts/build.py      # rebuilds dist/questions.json
```

The pre-commit hook runs both steps automatically.

## Adding a new topic

1. Create `questions/{new-topic}/` — use kebab-case.
2. Add questions following the steps above.
3. Choose a consistent ID prefix (e.g., `qcm-sira-0001` for topic `sira`).

## Modifying an existing question

Increment `version` in `metadata.yaml` when the question text, choices, answer, or explanation changes.

## Updating translations

Add or update the `{lang}.md` file and ensure `metadata.yaml → languages` includes the language code.
