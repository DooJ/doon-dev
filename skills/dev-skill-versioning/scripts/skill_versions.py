#!/usr/bin/env python3
"""독립 플러그인 저장소의 스킬과 플러그인 버전 기록을 검증한다."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date as calendar_date
from pathlib import Path
from typing import Any


VERSION_PATTERN = re.compile(r"^현재 버전: `(v\d+\.\d+\.\d+)`$", re.MULTILINE)
FINGERPRINT_PATTERN = re.compile(r"^내용 SHA-256: `sha256:([0-9a-f]{64})`$", re.MULTILINE)
SOURCE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: JSON을 읽을 수 없습니다: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path}: 최상위 값은 객체여야 합니다")
    return value


def skill_directories(root: Path) -> list[Path]:
    skills_root = root.resolve() / "skills"
    if not skills_root.is_dir():
        raise ValueError(f"스킬 폴더가 없습니다: {skills_root}")
    return sorted(path.parent for path in skills_root.glob("*/SKILL.md"))


def fingerprint(skill_dir: Path) -> str:
    """VERSION.md와 생성 파일을 제외한 스킬 패키지의 경로와 바이트를 해시한다."""

    digest = hashlib.sha256()
    for path in sorted(skill_dir.rglob("*")):
        if (
            not path.is_file()
            or path.is_symlink()
            or path.name in {"VERSION.md", ".DS_Store"}
            or "__pycache__" in path.parts
            or path.suffix == ".pyc"
        ):
            continue
        relative = path.relative_to(skill_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def table_rows(section: str) -> list[list[str]]:
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 4 or cells[0] in {"ID", "버전"}:
            continue
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        rows.append(cells)
    return rows


def validate_record(skill_dir: Path) -> list[str]:
    errors = []
    record = skill_dir / "VERSION.md"
    if not record.is_file():
        return [f"{record}: 파일이 없습니다"]

    content = record.read_text(encoding="utf-8")
    version_match = VERSION_PATTERN.search(content)
    hash_match = FINGERPRINT_PATTERN.search(content)
    if version_match is None:
        errors.append(f"{record}: 현재 버전 형식이 없습니다")
    if hash_match is None:
        errors.append(f"{record}: 내용 SHA-256 형식이 없습니다")
    elif hash_match.group(1) != fingerprint(skill_dir):
        errors.append(f"{record}: 내용 지문이 현재 스킬 파일과 다릅니다")

    source_heading = "## 출처\n"
    history_heading = "## 버전 이력\n"
    if source_heading not in content or history_heading not in content:
        errors.append(f"{record}: 출처 또는 버전 이력 표가 없습니다")
        return errors
    if content.index(source_heading) >= content.index(history_heading):
        errors.append(f"{record}: 출처 표는 버전 이력 표보다 앞에 있어야 합니다")
        return errors

    source_text = content.split(source_heading, 1)[1].split(history_heading, 1)[0]
    history_text = content.split(history_heading, 1)[1]
    sources = table_rows(source_text)
    history = table_rows(history_text)
    source_ids = set()
    for source_id, kind, material, scope in sources:
        normalized = source_id.strip("`")
        if not SOURCE_ID_PATTERN.fullmatch(normalized) or normalized in source_ids:
            errors.append(f"{record}: 출처 ID가 잘못되었거나 중복됐습니다: {source_id}")
        source_ids.add(normalized)
        if kind not in {"자체 생성", "외부 참고", "외부 원문 도입", "기원 미확인"}:
            errors.append(f"{record}: 출처 분류가 잘못됐습니다: {kind}")
        if not material or not scope:
            errors.append(f"{record}: 출처 자료와 반영 범위가 비었습니다: {source_id}")
    if not sources:
        errors.append(f"{record}: 출처 항목이 없습니다")

    versions = set()
    previous_version = None
    for listed_version, listed_date, summary, references in history:
        normalized = listed_version.strip("`")
        if not VERSION_PATTERN.fullmatch(f"현재 버전: `{normalized}`") or normalized in versions:
            errors.append(f"{record}: 버전이 잘못됐거나 중복됐습니다: {listed_version}")
        else:
            numeric_version = tuple(map(int, normalized[1:].split(".")))
            if previous_version is not None and numeric_version >= previous_version:
                errors.append(f"{record}: 버전 이력은 최신 버전부터 내림차순이어야 합니다")
            previous_version = numeric_version
        versions.add(normalized)
        try:
            if not DATE_PATTERN.fullmatch(listed_date):
                raise ValueError
            calendar_date.fromisoformat(listed_date)
        except ValueError:
            errors.append(f"{record}: 날짜 형식이 잘못됐습니다: {listed_date}")
        if len(summary) < 12:
            errors.append(f"{record}: 변경 요약이 너무 짧습니다: {listed_version}")
        used_ids = [part.strip().strip("`") for part in references.split(",")]
        if not used_ids or any(source_id not in source_ids for source_id in used_ids):
            errors.append(f"{record}: 없는 출처 ID를 참조합니다: {references}")
    if not history:
        errors.append(f"{record}: 버전 이력이 없습니다")
    elif version_match and history[0][0].strip("`") != version_match.group(1):
        errors.append(f"{record}: 첫 이력 버전과 현재 버전이 다릅니다")
    return errors


def validate_plugin_metadata(root: Path, skill_dirs: list[Path]) -> list[str]:
    errors = []
    manifest_paths = [
        root / "plugin.json",
        root / ".codex-plugin/plugin.json",
        root / ".claude-plugin/plugin.json",
    ]
    try:
        manifests = [load_json(path) for path in manifest_paths]
        antigravity = load_json(root / "antigravity/plugin.json")
        catalog = load_json(root / "catalog.json")
    except ValueError as error:
        return [str(error)]

    plugin_record = root / "PLUGIN_VERSION.md"
    if not plugin_record.is_file():
        errors.append(f"{plugin_record}: 파일이 없습니다")
        return errors
    version_match = VERSION_PATTERN.search(plugin_record.read_text(encoding="utf-8"))
    if version_match is None:
        errors.append(f"{plugin_record}: 현재 버전 형식이 없습니다")
        return errors
    expected_version = version_match.group(1).removeprefix("v")

    antigravity_keys = {"$schema", "name", "description"}
    if set(antigravity) != antigravity_keys:
        errors.append(f"{root / 'antigravity/plugin.json'}: 허용 필드가 {sorted(antigravity_keys)}와 다릅니다")
    if antigravity.get("$schema") != "https://antigravity.google/schemas/v1/plugin.json":
        errors.append(f"{root / 'antigravity/plugin.json'}: 공식 Antigravity schema가 아닙니다")
    if antigravity.get("name") != manifests[0].get("name"):
        errors.append(f"{root / 'antigravity/plugin.json'}: plugin 이름이 portable manifest와 다릅니다")
    if not isinstance(antigravity.get("description"), str) or not antigravity["description"].strip():
        errors.append(f"{root / 'antigravity/plugin.json'}: description이 비어 있습니다")

    catalog_plugin = catalog.get("plugin")
    versions = [manifest.get("version") for manifest in manifests]
    if isinstance(catalog_plugin, dict):
        versions.append(catalog_plugin.get("version"))
    else:
        errors.append(f"{root / 'catalog.json'}: plugin 객체가 없습니다")
    if any(version != expected_version for version in versions):
        errors.append(
            f"{root}: 플러그인 버전이 일치하지 않습니다: "
            f"PLUGIN_VERSION=v{expected_version}, manifests={versions}"
        )

    catalog_skills = catalog.get("skills")
    if not isinstance(catalog_skills, list):
        errors.append(f"{root / 'catalog.json'}: skills 목록이 없습니다")
        return errors
    registered = {
        item.get("name"): item.get("path")
        for item in catalog_skills
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    actual = {path.name: f"skills/{path.name}" for path in skill_dirs}
    if registered != actual:
        errors.append(f"{root / 'catalog.json'}: 스킬 목록이나 경로가 실제 skills/와 다릅니다")
    return errors


def validate_repository(root: Path) -> list[str]:
    try:
        skill_dirs = skill_directories(root)
    except ValueError as error:
        return [str(error)]
    return [
        *[error for path in skill_dirs for error in validate_record(path)],
        *validate_plugin_metadata(root.resolve(), skill_dirs),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "fingerprint"])
    parser.add_argument("skill", nargs="?", help="검사할 스킬 폴더 이름")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    try:
        skill_dirs = skill_directories(args.root)
    except ValueError as error:
        parser.error(str(error))
    if args.command == "fingerprint":
        if not args.skill:
            parser.error("fingerprint에는 스킬 이름이 필요합니다")
        matches = [path for path in skill_dirs if path.name == args.skill]
        if not matches:
            parser.error(f"스킬을 찾을 수 없습니다: {args.skill}")
        print(f"sha256:{fingerprint(matches[0])}")
        return 0

    if args.skill:
        skill_dirs = [path for path in skill_dirs if path.name == args.skill]
        if not skill_dirs:
            parser.error(f"스킬을 찾을 수 없습니다: {args.skill}")
        errors = [error for path in skill_dirs for error in validate_record(path)]
    else:
        errors = validate_repository(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"검증 실패: {len(errors)}개 오류", file=sys.stderr)
        return 1
    print(f"스킬·플러그인 버전 검증 완료: {len(skill_dirs)}개 스킬")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
