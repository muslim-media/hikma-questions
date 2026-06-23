#!/usr/bin/env python3
"""Validate question structure before commit."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUESTIONS_DIR = ROOT / "questions"

VALID_DIFFICULTIES = {"easy", "medium", "hard"}

errors = []
warnings = []


def load_metadata(path: Path) -> dict:
    meta = {}
    current_parent = None
    current_subkey = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent >= 4 and stripped.startswith("- "):
            if current_parent and current_subkey is not None:
                parent_val = meta.get(current_parent)
                if isinstance(parent_val, dict):
                    parent_val.setdefault(current_subkey, []).append(stripped[2:])
            continue
        if indent == 2:
            if stripped.startswith("- ") and current_parent:
                if isinstance(meta.get(current_parent), list):
                    meta[current_parent].append(stripped[2:])
            elif ":" in stripped and current_parent:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip().strip('"')
                if isinstance(meta.get(current_parent), list):
                    meta[current_parent] = {}
                current_subkey = key
                meta[current_parent][key] = [] if (val == "" or val.lower() == "null") else val
            continue
        if indent == 0 and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"')
            current_parent = None
            current_subkey = None
            if val == "":
                meta[key] = []
                current_parent = key
            elif val.lower() == "null":
                meta[key] = None
            else:
                meta[key] = val
    return meta


def check_formation(path: Path, meta: dict) -> None:
    if not meta.get("id"):
        errors.append(f"{path.name}: formation missing 'id'")
    if not meta.get("languages"):
        errors.append(f"{path.name}: formation missing 'languages'")
    has_title = any(k.startswith("title_") for k in meta)
    if not has_title:
        warnings.append(f"{path.name}: formation has no 'title_<lang>' field")


def check_category(path: Path, meta: dict) -> None:
    if not meta.get("id"):
        errors.append(f"{path.name}: category missing 'id'")
    has_title = any(k.startswith("title_") for k in meta)
    if not has_title:
        warnings.append(f"{path.name}: category has no 'title_<lang>' field")


def check_question(path: Path, meta: dict) -> None:
    for field in ("id", "difficulty", "tags", "languages", "created_at"):
        if field not in meta:
            errors.append(f"{path.name}: question missing '{field}'")
    if meta.get("difficulty") and meta["difficulty"] not in VALID_DIFFICULTIES:
        errors.append(f"{path.name}: invalid difficulty '{meta['difficulty']}'")
    declared_langs = meta.get("languages") or []
    actual_langs = {f.stem for f in path.glob("*.md")}
    for lang in declared_langs:
        if lang not in actual_langs:
            errors.append(f"{path.name}: declared '{lang}' but {lang}.md missing")
    for lang in actual_langs:
        if lang not in declared_langs:
            warnings.append(f"{path.name}: {lang}.md exists but not declared in languages")


def traverse(path: Path) -> int:
    """Walk the tree and validate. Returns count of questions found."""
    meta_file = path / "metadata.yaml"
    if not meta_file.exists():
        errors.append(f"{path}: missing metadata.yaml")
        return 0

    meta = load_metadata(meta_file)
    node_type = meta.get("type")

    if node_type == "formation":
        check_formation(path, meta)
        count = 0
        for child in sorted(p for p in path.iterdir() if p.is_dir()):
            count += traverse(child)
        return count

    elif node_type == "category":
        check_category(path, meta)
        count = 0
        for child in sorted(p for p in path.iterdir() if p.is_dir()):
            count += traverse(child)
        return count

    else:
        check_question(path, meta)
        return 1


total = 0
for formation_dir in sorted(p for p in QUESTIONS_DIR.iterdir() if p.is_dir()):
    total += traverse(formation_dir)

if warnings:
    for w in warnings:
        print(f"  WARN  {w}")

if errors:
    print("Validation failed:", file=sys.stderr)
    for e in errors:
        print(f"  ERROR {e}", file=sys.stderr)
    sys.exit(1)

print(f"Validation passed ({total} questions)")
