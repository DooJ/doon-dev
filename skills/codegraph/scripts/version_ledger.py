"""프로젝트 codebase-map 전체 버전과 구성요소별 변경 이력을 관리한다."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

COMPONENTS = ("graphify", "archify", "obsidian")
LEDGER_NAME = "version-ledger.json"
SUMMARY_NAME = "VERSION.md"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def version_parts(value: str) -> tuple[int, int, int]:
    numbers = value.removeprefix("v").split(".")
    if len(numbers) != 3 or any(not item.isdigit() for item in numbers):
        raise ValueError(f"올바르지 않은 버전: {value}")
    return tuple(map(int, numbers))  # type: ignore[return-value]


def next_version(previous: str, level: str) -> str:
    major, minor, patch = version_parts(previous)
    if level == "major":
        return f"v{major + 1}.0.0"
    if level == "minor":
        return f"v{major}.{minor + 1}.0"
    if level == "patch":
        return f"v{major}.{minor}.{patch + 1}"
    raise ValueError(f"올바르지 않은 변경 수준: {level}")


def map_root(project: Path) -> Path:
    root = project.resolve() / "codebase-map"
    if not root.is_dir() or root.is_symlink():
        raise ValueError("프로젝트의 실제 codebase-map 폴더가 필요합니다.")
    return root


def load(root: Path) -> dict:
    path = root / LEDGER_NAME
    if not path.is_file():
        raise ValueError("버전 이력이 없습니다. 먼저 init을 실행하세요.")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not data.get("versions"):
        raise ValueError("지원하지 않는 버전 이력 형식입니다.")
    return data


def digest_artifact(root: Path, value: str) -> dict:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"codebase-map 내부 상대 경로만 허용합니다: {value}")
    target = root / relative
    if any(path.is_symlink() for path in (root / Path(*relative.parts[:index]) for index in range(1, len(relative.parts)))):
        raise ValueError(f"산출물 경로에 링크가 포함돼 있습니다: {value}")
    if not target.exists() or target.is_symlink():
        raise ValueError(f"산출물 파일이 없거나 링크입니다: {value}")
    files = sorted(target.rglob("*")) if target.is_dir() else [target]
    hasher = hashlib.sha256()
    count = 0
    for path in files:
        if path.is_symlink():
            raise ValueError(f"산출물에 링크가 포함돼 있습니다: {path}")
        if not path.is_file():
            continue
        relative_file = path.relative_to(root)
        hasher.update(relative_file.as_posix().encode("utf-8"))
        hasher.update(b"\0")
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(block)
        count += 1
    if not count:
        raise ValueError(f"비어 있는 산출물은 기록할 수 없습니다: {value}")
    return {"path": relative.as_posix(), "sha256": hasher.hexdigest(), "files": count}


def render(data: dict) -> str:
    current = data["versions"][-1]
    lines = ["# 코드그래프 버전", "", f"현재 버전: `{current['version']}`", "", "각 시각은 실행 환경의 현지 시각과 UTC 오프셋입니다. 산출물 지문은 변경 확인용이며 백업 파일을 대신하지 않습니다.", ""]
    latest: dict[str, tuple[str, dict]] = {}
    for version in data["versions"]:
        lines.extend([f"## {version['version']} · {'진행 중' if version['state'] == 'open' else '종료'}", "", f"정의: {version['note']}", ""])
        for component in COMPONENTS:
            lines.append(f"### {component.capitalize() if component != 'obsidian' else 'Obsidian'}")
            lines.append("")
            revisions = version["revisions"][component]
            if revisions:
                for revision in revisions:
                    artifacts = ", ".join(f"`{item['path']}` (`{item['sha256'][:12]}`)" for item in revision["artifacts"])
                    lines.append(f"- {revision['at']} · {revision['note']} · {artifacts}")
                latest[component] = (version["version"], revisions[-1])
            elif component in latest:
                source_version, inherited = latest[component]
                lines.append(f"- 이전 결과 승계: {source_version} / {inherited['at']} (새 실행 없음)")
            else:
                lines.append("- 기록 없음")
            lines.append("")
    return "\n".join(lines)


def save(root: Path, data: dict) -> None:
    ledger = root / LEDGER_NAME
    temporary = root / f".{LEDGER_NAME}.tmp"
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, ledger)
    summary = root / SUMMARY_NAME
    temporary = root / f".{SUMMARY_NAME}.tmp"
    temporary.write_text(render(data), encoding="utf-8")
    os.replace(temporary, summary)


def init(project: Path, note: str = "코드그래프 기준선") -> dict:
    root = map_root(project)
    if (root / LEDGER_NAME).exists() or (root / SUMMARY_NAME).exists():
        raise ValueError("기존 버전 파일이 있습니다. 덮어쓰지 않습니다.")
    data = {"schema_version": 1, "versions": [{"version": "v1.0.0", "state": "open", "opened_at": now(), "note": note, "revisions": {component: [] for component in COMPONENTS}}]}
    save(root, data)
    return data


def record(project: Path, component: str, artifacts: list[str], note: str) -> tuple[dict, bool]:
    root = map_root(project)
    data = load(root)
    current = data["versions"][-1]
    if current["state"] != "open" or component not in COMPONENTS or not artifacts:
        raise ValueError("진행 중인 버전, 올바른 구성요소와 산출물 경로가 필요합니다.")
    if len(artifacts) != len(set(artifacts)):
        raise ValueError("같은 산출물 경로를 중복 기록할 수 없습니다.")
    fingerprints = sorted((digest_artifact(root, path) for path in artifacts), key=lambda item: item["path"])
    latest = next((version["revisions"][component][-1] for version in reversed(data["versions"]) if version["revisions"][component]), None)
    if latest and latest["artifacts"] == fingerprints:
        return data, False
    current["revisions"][component].append({"at": now(), "note": note, "artifacts": fingerprints})
    save(root, data)
    return data, True


def bump(project: Path, level: str, note: str) -> dict:
    root = map_root(project)
    data = load(root)
    current = data["versions"][-1]
    if current["state"] != "open":
        raise ValueError("현재 버전이 진행 중이 아닙니다.")
    target = next_version(current["version"], level)
    current["state"] = "closed"
    current["closed_at"] = now()
    data["versions"].append({"version": target, "state": "open", "opened_at": now(), "note": note, "revisions": {component: [] for component in COMPONENTS}})
    save(root, data)
    return data


def reclassify(project: Path, level: str, note: str | None = None) -> dict:
    root = map_root(project)
    data = load(root)
    if len(data["versions"]) < 2 or data["versions"][-1]["state"] != "open":
        raise ValueError("이전 버전에서 분기한 진행 중 버전만 재분류할 수 있습니다.")
    previous, current = data["versions"][-2:]
    current["version"] = next_version(previous["version"], level)
    if note:
        current["note"] = note
    save(root, data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    init_command = commands.add_parser("init")
    init_command.add_argument("--note", default="코드그래프 기준선")
    record_command = commands.add_parser("record")
    record_command.add_argument("--component", choices=COMPONENTS, required=True)
    record_command.add_argument("--artifact", action="append", required=True)
    record_command.add_argument("--note", required=True)
    bump_command = commands.add_parser("bump")
    bump_command.add_argument("--level", choices=("patch", "minor", "major"), required=True)
    bump_command.add_argument("--note", required=True)
    reclassify_command = commands.add_parser("reclassify")
    reclassify_command.add_argument("--level", choices=("patch", "minor", "major"), required=True)
    reclassify_command.add_argument("--note")
    commands.add_parser("status")
    args = parser.parse_args()
    try:
        if args.command == "init":
            data = init(args.project, args.note)
        elif args.command == "record":
            data, changed = record(args.project, args.component, args.artifact, args.note)
            if not changed:
                print("산출물 지문이 같아 새 이력을 기록하지 않았습니다.")
        elif args.command == "bump":
            data = bump(args.project, args.level, args.note)
        elif args.command == "reclassify":
            data = reclassify(args.project, args.level, args.note)
        else:
            data = load(map_root(args.project))
        current = data["versions"][-1]
        print(f"{current['version']} ({current['state']}) · {map_root(args.project) / SUMMARY_NAME}")
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(2, f"오류: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
