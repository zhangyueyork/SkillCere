#!/usr/bin/env python3
"""SkillCere command line utility.

First version: scan installed skills and show index status.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
INDEX_FILE = ROOT / "skill-index.json"
PLATFORMS_FILE = ROOT / "platforms.json"
LOCAL_PLATFORMS_FILE = ROOT / "platforms.local.json"
INSTALL_LOG_FILE = ROOT / "install-log.jsonl"
SKILL_FILE_NAME = "SKILL.md"


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def read_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def append_log(event: dict[str, Any]) -> None:
    event = {"created_at": now_iso(), **event}
    with INSTALL_LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def normalize_id(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = value.strip("-._")
    return value or "unknown-skill"


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text

    metadata: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            metadata[key] = value

    body = "\n".join(lines[end_index + 1 :])
    return metadata, body


def first_heading(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def first_paragraph(text: str) -> str:
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if not block or block.startswith("#") or block.startswith("```"):
            continue
        return re.sub(r"\s+", " ", block)[:300]
    return ""


def text_keywords(text: str, limit: int = 12) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", text)
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "when",
        "use",
        "using",
        "skill",
        "skills",
        "should",
        "must",
        "will",
        "you",
        "your",
    }
    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        normalized = token.lower()
        if normalized in stop_words or normalized in seen:
            continue
        seen.add(normalized)
        result.append(token)
        if len(result) >= limit:
            break
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def sha256_text(value: str, prefix: str = "sha256:") -> str:
    return prefix + hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_excluded(path: Path, excluded_dirs: list[Path]) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    for excluded in excluded_dirs:
        try:
            resolved.relative_to(excluded)
            return True
        except ValueError:
            continue
    return False


def discover_skill_dirs(root: Path, excluded_dirs: list[Path]) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []

    skills: list[Path] = []
    for skill_file in root.rglob(SKILL_FILE_NAME):
        skill_dir = skill_file.parent
        if is_excluded(skill_dir, excluded_dirs):
            continue
        skills.append(skill_dir)
    return sorted(set(skills), key=lambda item: str(item).lower())


def read_skill(skill_dir: Path) -> dict[str, Any]:
    skill_file = skill_dir / SKILL_FILE_NAME
    text = skill_file.read_text(encoding="utf-8", errors="replace")
    metadata, body = parse_front_matter(text)

    name = metadata.get("name") or skill_dir.name
    skill_id = normalize_id(name)
    description = metadata.get("description") or first_paragraph(body)
    display_name = first_heading(body) or name
    file_hash = sha256_file(skill_file)
    keywords = text_keywords(" ".join([name, description, body[:2000]]))

    return {
        "id": skill_id,
        "name": name,
        "display_name": display_name,
        "description": description,
        "keywords": keywords,
        "categories": [],
        "source": {"type": "unknown", "url": ""},
        "latest_version": "unknown",
        "version_strategy": "file_hash",
        "latest_ref": file_hash,
        "status": "active",
    }


def ensure_index_shape(index: dict[str, Any]) -> dict[str, Any]:
    index.setdefault("schema_version", "1.0.0")
    index.setdefault("updated_at", now_iso())
    index.setdefault("skills", {})
    index.setdefault("aliases", {})
    index.setdefault("tags", {})
    return index


def merge_skill(index: dict[str, Any], skill: dict[str, Any], platform: str) -> str:
    skills = index["skills"]
    skill_id = skill["id"]
    existing = skills.get(skill_id)
    event_type = "unchanged"

    if existing is None:
        existing = skill | {
            "supported_platforms": [],
            "installed_on": {},
            "last_checked": "",
            "notes": "",
        }
        skills[skill_id] = existing
        event_type = "added"
    else:
        # Keep user-curated fields when present; only fill empty metadata.
        for key in ("name", "display_name", "description"):
            if not existing.get(key) and skill.get(key):
                existing[key] = skill[key]
        for key in ("source", "latest_version", "version_strategy", "latest_ref", "status"):
            existing.setdefault(key, skill.get(key))
        existing_keywords = set(existing.get("keywords", []))
        merged_keywords = list(existing.get("keywords", []))
        for keyword in skill.get("keywords", []):
            if keyword not in existing_keywords:
                merged_keywords.append(keyword)
                existing_keywords.add(keyword)
        existing["keywords"] = merged_keywords[:20]
        existing.setdefault("categories", [])
        existing.setdefault("supported_platforms", [])
        existing.setdefault("installed_on", {})

    if platform not in existing["supported_platforms"]:
        existing["supported_platforms"].append(platform)
        existing["supported_platforms"].sort()
        if event_type == "unchanged":
            event_type = "new_platform"

    previous_platform = existing["installed_on"].get(platform, {})
    if previous_platform.get("ref") != skill.get("latest_ref") and event_type == "unchanged":
        event_type = "updated"

    existing["installed_on"][platform] = {
        "version": skill.get("latest_version", "unknown"),
        "ref": skill.get("latest_ref", ""),
        "last_seen": now_iso(),
        "status": "installed",
    }
    return event_type


def aggregate_duplicate_skills(skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    refs: dict[str, set[str]] = {}

    for skill in skills:
        skill_id = skill["id"]
        if skill_id not in grouped:
            grouped[skill_id] = skill
            refs[skill_id] = set()
        refs[skill_id].add(skill.get("latest_ref", ""))

    for skill_id, skill_refs in refs.items():
        clean_refs = sorted(ref for ref in skill_refs if ref)
        if len(clean_refs) > 1:
            grouped[skill_id]["latest_ref"] = sha256_text("|".join(clean_refs), "sha256-multi:")

    return [grouped[key] for key in sorted(grouped)]


def load_scan_config() -> tuple[dict[str, Any], dict[str, Any], list[Path]]:
    platforms = read_json(PLATFORMS_FILE, {"platforms": {}})
    local = read_json(LOCAL_PLATFORMS_FILE, {"platform_skill_dirs": {}, "excluded_dirs": []})
    excluded = [Path(item).expanduser() for item in local.get("excluded_dirs", [])]
    return platforms, local, excluded


def command_scan(_: argparse.Namespace) -> int:
    index = ensure_index_shape(read_json(INDEX_FILE))
    platforms, local, excluded_dirs = load_scan_config()
    known_platforms = set(platforms.get("platforms", {}).keys())

    added = 0
    updated = 0
    unchanged = 0
    scanned = 0
    missing_roots: list[str] = []

    for platform, roots in local.get("platform_skill_dirs", {}).items():
        if known_platforms and platform not in known_platforms:
            print(f"Warning: {platform} is not defined in platforms.json", file=sys.stderr)

        for root_config in roots:
            if root_config.get("role", "target") not in {"target", "system"}:
                continue
            root = Path(root_config["path"]).expanduser()
            if not root.exists():
                missing_roots.append(f"{platform}: {root}")
                continue
            discovered = [read_skill(skill_dir) for skill_dir in discover_skill_dirs(root, excluded_dirs)]
            for skill in aggregate_duplicate_skills(discovered):
                event_type = merge_skill(index, skill, platform)
                scanned += 1
                if event_type == "added":
                    added += 1
                elif event_type in {"updated", "new_platform"}:
                    updated += 1
                else:
                    unchanged += 1
                if event_type != "unchanged":
                    append_log(
                        {
                            "event": event_type,
                            "skill_id": skill["id"],
                            "platform": platform,
                            "version": skill.get("latest_version", "unknown"),
                            "ref": skill.get("latest_ref", ""),
                        }
                    )

    index["updated_at"] = now_iso()
    write_json(INDEX_FILE, index)

    print(f"Scanned skills: {scanned}")
    print(f"Added skills: {added}")
    print(f"Updated or new platform sightings: {updated}")
    print(f"Unchanged sightings: {unchanged}")
    print(f"Total indexed skills: {len(index['skills'])}")
    if missing_roots:
        print("Missing scan roots:")
        for item in missing_roots:
            print(f"  - {item}")
    return 0


def command_status(_: argparse.Namespace) -> int:
    index = ensure_index_shape(read_json(INDEX_FILE))
    skills = index["skills"]
    platform_counts: dict[str, int] = {}
    missing_source = 0
    unknown_version = 0

    for skill in skills.values():
        source = skill.get("source") or {}
        if not source.get("url"):
            missing_source += 1
        if skill.get("latest_version") in {"", None, "unknown"}:
            unknown_version += 1
        for platform in (skill.get("installed_on") or {}).keys():
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

    print("SkillCere status")
    print(f"  Indexed skills: {len(skills)}")
    print(f"  Missing source URL: {missing_source}")
    print(f"  Unknown version: {unknown_version}")
    print("  Installed by platform:")
    if platform_counts:
        for platform, count in sorted(platform_counts.items()):
            print(f"    {platform}: {count}")
    else:
        print("    none")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillcere",
        description="SkillCere: cross-Agent skill coordination utility.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    scan = subcommands.add_parser("scan", help="Scan local skill directories into the central index.")
    scan.set_defaults(func=command_scan)

    status = subcommands.add_parser("status", help="Show central index status.")
    status.set_defaults(func=command_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
