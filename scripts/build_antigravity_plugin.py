#!/usr/bin/env python3
"""현재 저장소를 설치 가능한 Antigravity 플러그인 패키지로 만든다."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path


SCHEMA = "https://antigravity.google/schemas/v1/plugin.json"
ALLOWED_MANIFEST_KEYS = {"$schema", "name", "description"}
NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
GENERATED_MARKER = ".doon-antigravity-package"


def ignored(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in {".DS_Store", "__pycache__"} or name.endswith(".pyc")}


def load_manifest(root: Path) -> dict[str, str]:
    path = root / "antigravity" / "plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if set(data) - ALLOWED_MANIFEST_KEYS:
        raise ValueError(f"지원하지 않는 Antigravity manifest 필드: {sorted(set(data) - ALLOWED_MANIFEST_KEYS)}")
    if data.get("$schema") != SCHEMA:
        raise ValueError(f"Antigravity schema가 올바르지 않습니다: {path}")
    name = data.get("name")
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        raise ValueError(f"Antigravity plugin 이름이 올바르지 않습니다: {name!r}")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        raise ValueError("Antigravity plugin 설명이 비어 있습니다")
    return data


def build(root: Path, output_parent: Path) -> Path:
    root = root.resolve()
    manifest = load_manifest(root)
    skills = root / "skills"
    if not skills.is_dir() or not any(skills.glob("*/SKILL.md")):
        raise ValueError(f"설치할 Agent Skills가 없습니다: {skills}")
    output_parent = output_parent.resolve()
    output_parent.mkdir(parents=True, exist_ok=True)
    target = output_parent / manifest["name"]
    if target.exists() and not (target / GENERATED_MARKER).is_file():
        raise ValueError(f"생성 패키지가 아닌 기존 경로는 덮어쓰지 않습니다: {target}")
    stage = Path(tempfile.mkdtemp(prefix=f".{manifest['name']}-", dir=output_parent))
    try:
        (stage / "plugin.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copytree(skills, stage / "skills", ignore=ignored)
        resources = root / "resources"
        if resources.is_dir():
            shutil.copytree(resources, stage / "resources", ignore=ignored)
        (stage / GENERATED_MARKER).write_text("generated\n", encoding="utf-8")
        if target.exists():
            shutil.rmtree(target)
        stage.replace(target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="패키지 상위 폴더")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / ".build" / "antigravity"
    print(build(root, output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
