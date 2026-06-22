#!/usr/bin/env python3
"""Validate question structure before commit."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUESTIONS_DIR = ROOT / "questions"

REQUIRED_META_FIELDS = {"id", "topic", "difficulty", "tags", "languages", "created_at", "version"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}

errors = []
warnings = []


def load_metadata(path: Path) -> dict:
    meta = {}
    current_list_key = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("  - ") or line.startswith("- "):
            if current_list_key:
                meta[current_list_key].append(line.strip().lstrip("- "))
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"')
            if val == "":
                meta[key] = []
                current_list_key = key
            elif val.lower() == "null":
                meta[key] = None
                current_list_key = None
            else:
                meta[key] = val
                current_list_key = None
    return meta


def check_question(q_dir: Path, topic: str) -> None:
    meta_file = q_dir / "metadata.yaml"

    if not meta_file.exists():
        errors.append(f"{q_dir}: missing metadata.yaml")
        return

    meta = load_metadata(meta_file)

    missing = REQUIRED_META_FIELDS - meta.keys()
    if missing:
        errors.append(f"{q_dir.name}: metadata missing fields: {missing}")

    if meta.get("topic") and meta["topic"] != topic:
        errors.append(
            f"{q_dir.name}: metadata.topic='{meta['topic']}' but folder is '{topic}'"
        )

    if meta.get("difficulty") and meta["difficulty"] not in VALID_DIFFICULTIES:
        errors.append(
            f"{q_dir.name}: invalid difficulty '{meta['difficulty']}' (expected: {VALID_DIFFICULTIES})"
        )

    declared_langs = meta.get("languages") or []
    actual_langs = {f.stem for f in q_dir.glob("*.md")}

    for lang in declared_langs:
        if lang not in actual_langs:
            errors.append(
                f"{q_dir.name}: metadata declares '{lang}' but {lang}.md not found"
            )

    for lang in actual_langs:
        if lang not in declared_langs:
            warnings.append(
                f"{q_dir.name}: {lang}.md exists but not declared in metadata.languages"
            )


for topic_dir in sorted(QUESTIONS_DIR.iterdir()):
    if not topic_dir.is_dir():
        continue
    for q_dir in sorted(topic_dir.iterdir()):
        if q_dir.is_dir():
            check_question(q_dir, topic_dir.name)

if warnings:
    for w in warnings:
        print(f"  WARN  {w}")

if errors:
    print("Validation failed:", file=sys.stderr)
    for e in errors:
        print(f"  ERROR {e}", file=sys.stderr)
    sys.exit(1)

print(f"Validation passed ({sum(1 for t in QUESTIONS_DIR.iterdir() if t.is_dir() for q in t.iterdir() if q.is_dir())} questions)")
