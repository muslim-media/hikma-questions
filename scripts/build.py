#!/usr/bin/env python3
"""Build dist/ artifacts from the questions/ source tree.

Outputs:
  dist/questions.json        — manifest (formation catalog, no content)
  dist/questions_<lang>.json — per-language files with formations + questions
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
            result["answer"] = int(raw) - 1
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


def merge_tags(meta: dict, lang: str) -> list:
    global_tags = meta.get("tags") or []
    lang_tags = (meta.get("tags_by_lang") or {}).get(lang) or []
    return global_tags + [t for t in lang_tags if t not in global_tags]


def build() -> None:
    errors: list[str] = []
    by_lang: dict[str, list[dict]] = defaultdict(list)
    formation_store: dict[str, dict] = {}
    category_store: dict[tuple, dict] = {}
    cat_counts: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    formation_q_ids: dict[str, set] = defaultdict(set)
    formation_langs: dict[str, set] = defaultdict(set)

    def traverse(path: Path, f_meta: dict | None, cat_path: list[str]) -> None:
        meta_file = path / "metadata.yaml"
        if not meta_file.exists():
            errors.append(f"[{path.name}] missing metadata.yaml")
            return
        try:
            meta = load_metadata(meta_file)
        except Exception as e:
            errors.append(f"[{path.name}] parse error: {e}")
            return

        node_type = meta.get("type")

        if node_type == "formation":
            fid = meta.get("id", path.name)
            formation_store[fid] = meta
            for child in sorted(p for p in path.iterdir() if p.is_dir()):
                traverse(child, meta, [])

        elif node_type == "category":
            new_path = cat_path + [meta.get("id", path.name)]
            if f_meta:
                store_key = (f_meta.get("id", ""),) + tuple(new_path)
                category_store[store_key] = meta
            for child in sorted(p for p in path.iterdir() if p.is_dir()):
                traverse(child, f_meta, new_path)

        else:
            if f_meta is None:
                errors.append(f"[{path.name}] question found outside a formation")
                return
            fid = f_meta.get("id", "")
            declared_langs = meta.get("languages") or []
            content: dict[str, dict] = {}
            for lang_file in sorted(path.glob("*.md")):
                lang = lang_file.stem
                try:
                    content[lang] = parse_md(lang_file.read_text(encoding="utf-8"))
                except ValueError as e:
                    errors.append(f"[{path.name}/{lang}.md] {e}")
            for lang in declared_langs:
                if lang not in content:
                    errors.append(f"[{path.name}] declared '{lang}' but {lang}.md missing")
            if not content:
                errors.append(f"[{path.name}] no language files found")
                return

            q_id = meta.get("id", path.name)
            category_paths = [cat_path[:i + 1] for i in range(len(cat_path))]
            q_base = {
                "id": q_id,
                "formation_id": fid,
                "categories": list(cat_path),
                "category_paths": category_paths,
                "difficulty": meta.get("difficulty", "easy"),
                "source": meta.get("source"),
                "created_at": meta.get("created_at"),
            }

            for lang, lang_content in content.items():
                by_lang[lang].append({**q_base, "tags": merge_tags(meta, lang), **lang_content})
                formation_q_ids[fid].add(q_id)
                formation_langs[fid].add(lang)
                for prefix in category_paths:
                    cat_counts[lang][fid][tuple(prefix)] += 1

    for formation_dir in sorted(p for p in QUESTIONS_DIR.iterdir() if p.is_dir()):
        traverse(formation_dir, None, [])

    if errors:
        print("BUILD FAILED — validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    DIST_DIR.mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest_file = DIST_DIR / "questions.json"
    manifest_file.write_text(
        json.dumps(
            {
                "version": 1,
                "generated_at": today,
                "formations": {
                    fid: {
                        "languages": sorted(formation_langs[fid]),
                        "question_count": len(formation_q_ids[fid]),
                    }
                    for fid in sorted(formation_store)
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Built manifest → {manifest_file.relative_to(ROOT)}")

    for lang, questions in sorted(by_lang.items()):
        formations_out = []
        for fid, fmeta in sorted(formation_store.items()):
            lang_qs = [q for q in questions if q["formation_id"] == fid]
            if not lang_qs:
                continue
            title = fmeta.get(f"title_{lang}") or fmeta.get("title_en") or fid
            description = fmeta.get(f"description_{lang}") or fmeta.get("description_en") or None

            categories_out = []
            for cat_path_tuple, count in sorted(cat_counts[lang][fid].items()):
                cat_path_list = list(cat_path_tuple)
                cat_id = cat_path_list[-1]
                store_key = (fid,) + cat_path_tuple
                cat_meta = category_store.get(store_key, {})
                cat_title = cat_meta.get(f"title_{lang}") or cat_meta.get("title_en") or cat_id
                categories_out.append({
                    "id": cat_id,
                    "title": cat_title,
                    "path": cat_path_list,
                    "question_count": count,
                })

            formations_out.append({
                "id": fid,
                "title": title,
                "description": description,
                "question_count": len(lang_qs),
                "categories": categories_out,
            })

        lang_file = DIST_DIR / f"questions_{lang}.json"
        lang_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "generated_at": today,
                    "language": lang,
                    "formations": formations_out,
                    "questions": questions,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"  → {lang_file.relative_to(ROOT)} ({len(questions)} questions)")


if __name__ == "__main__":
    build()
