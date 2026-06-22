#!/usr/bin/env python3
"""Build dist/ artifacts from the questions/ source tree.

Outputs:
  dist/questions.json       — metadata catalog (no content)
  dist/questions_<lang>.json — per-language content files
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUESTIONS_DIR = ROOT / "questions"
DIST_DIR = ROOT / "dist"


def parse_md(text: str) -> dict:
    """Parse a question Markdown file into a dict."""
    sections = re.split(r"^##? ", text, flags=re.MULTILINE)
    result = {}
    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().splitlines()
        header = lines[0].strip()
        body = "\n".join(lines[1:]).strip()

        if header == "Question":
            result["question"] = body
        elif header == "Choices":
            result["choices"] = [
                line.lstrip("- ").strip()
                for line in body.splitlines()
                if line.strip().startswith("-")
            ]
        elif header == "Answer":
            raw = body.strip()
            if not raw.isdigit():
                raise ValueError(f"Answer must be a digit, got: {raw!r}")
            result["answer"] = int(raw) - 1  # convert 1-based → 0-based
        elif header == "Explanation":
            result["explanation"] = body

    missing = {"question", "choices", "answer", "explanation"} - result.keys()
    if missing:
        raise ValueError(f"Missing sections: {missing}")
    if not (0 <= result["answer"] < len(result["choices"])):
        raise ValueError(
            f"Answer index {result['answer']} out of range for {len(result['choices'])} choices"
        )
    return result


def load_metadata(path: Path) -> dict:
    """Minimal YAML parser — only handles the simple key/value + list format we use."""
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
            if val == "" or val is None:
                meta[key] = None
                current_list_key = None
            elif val.lower() == "null":
                meta[key] = None
                current_list_key = None
            else:
                meta[key] = val
                current_list_key = None
            if val == "":
                meta[key] = []
                current_list_key = key
    return meta


def build() -> None:
    errors = []
    by_lang: dict[str, list[dict]] = defaultdict(list)

    for topic_dir in sorted(QUESTIONS_DIR.iterdir()):
        if not topic_dir.is_dir():
            continue
        for q_dir in sorted(topic_dir.iterdir()):
            if not q_dir.is_dir():
                continue

            meta_file = q_dir / "metadata.yaml"
            if not meta_file.exists():
                errors.append(f"[{q_dir.name}] missing metadata.yaml")
                continue

            try:
                meta = load_metadata(meta_file)
            except Exception as e:
                errors.append(f"[{q_dir.name}] metadata.yaml parse error: {e}")
                continue

            declared_langs = meta.get("languages") or []
            content: dict[str, dict] = {}
            for lang_file in sorted(q_dir.glob("*.md")):
                lang = lang_file.stem
                try:
                    content[lang] = parse_md(lang_file.read_text(encoding="utf-8"))
                except ValueError as e:
                    errors.append(f"[{q_dir.name}/{lang}.md] {e}")

            for lang in declared_langs:
                if lang not in content:
                    errors.append(
                        f"[{q_dir.name}] metadata declares language '{lang}' but {lang}.md not found"
                    )

            if not content:
                errors.append(f"[{q_dir.name}] no language files found")
                continue

            q_meta = {
                "id": meta.get("id", q_dir.name),
                "topic": meta.get("topic", topic_dir.name),
                "difficulty": meta.get("difficulty", "easy"),
                "tags": meta.get("tags") or [],
                "source": meta.get("source"),
                "created_at": meta.get("created_at"),
                "version": int(meta.get("version") or 1),
            }

            for lang, lang_content in content.items():
                by_lang[lang].append({**q_meta, **lang_content})

    if errors:
        print("BUILD FAILED — validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    DIST_DIR.mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    languages_index = {
        lang: {"count": len(entries), "updated_at": today}
        for lang, entries in sorted(by_lang.items())
    }
    manifest_file = DIST_DIR / "questions.json"
    manifest_file.write_text(
        json.dumps(
            {"version": 2, "generated_at": today, "languages": languages_index},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Built manifest → {manifest_file.relative_to(ROOT)}")

    for lang, entries in sorted(by_lang.items()):
        lang_file = DIST_DIR / f"questions_{lang}.json"
        lang_file.write_text(
            json.dumps(
                {"version": 2, "generated_at": today, "lang": lang, "count": len(entries), "questions": entries},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"  → {lang_file.relative_to(ROOT)} ({len(entries)} questions)")


if __name__ == "__main__":
    build()
