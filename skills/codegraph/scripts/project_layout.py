#!/usr/bin/env python3
"""프로젝트의 범위별 코드베이스 지도 폴더를 점검·준비한다."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HUB_NAME = "codebase-map"
GRAPH_NAME = "graphify-out"
RESERVED = {GRAPH_NAME, "archify", "vault", "overview", "VERSION.md", "README.md", "version-ledger.json"}


def scope_name(value: str) -> str:
    if (
        not value or value.strip() != value or value in {".", ".."}
        or Path(value).name != value or "\\" in value
        or any(ord(char) < 32 for char in value)
        or value in RESERVED or re.fullmatch(r"v\d+\.\d+\.\d+", value)
    ):
        raise ValueError(f"범위 이름은 codebase-map 바로 아래의 안전한 폴더 이름이어야 합니다: {value!r}")
    return value


def paths(project: Path) -> tuple[Path, Path, Path]:
    root = project.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"프로젝트 폴더가 없습니다: {root}")
    hub = root / HUB_NAME
    if hub.is_symlink():
        raise ValueError(f"분석 폴더가 심볼릭 링크입니다: {hub}")
    graph = hub / GRAPH_NAME
    return hub, graph, root / GRAPH_NAME


def status(project: Path, scope: str | None = None) -> dict[str, object]:
    hub, graph, link = paths(project)
    if scope is not None:
        name = scope_name(scope)
        scoped = hub / name
        if scoped.is_symlink():
            raise ValueError(f"범위 폴더가 심볼릭 링크입니다: {scoped}")
        ledger = scoped / "version-ledger.json"
        versions = json.loads(ledger.read_text(encoding="utf-8")).get("versions", []) if ledger.is_file() else []
        return {
            "project": str(project.expanduser().resolve()),
            "hub": str(hub),
            "scope": name,
            "scope_path": str(scoped),
            "scope_exists": scoped.is_dir(),
            "current_version": versions[-1].get("version") if versions else None,
            "legacy_unscoped_exists": any((hub / item).exists() for item in (GRAPH_NAME, "archify", "vault", "version-ledger.json")),
        }
    expected = graph.resolve(strict=False)
    if link.is_symlink():
        link_state = "managed" if link.resolve(strict=False) == expected else "foreign-link"
    elif link.exists():
        link_state = "real-directory" if link.is_dir() else "occupied"
    else:
        link_state = "missing"
    return {
        "project": str(project.expanduser().resolve()),
        "hub": str(hub),
        "hub_exists": hub.is_dir(),
        "graph_exists": graph.is_dir(),
        "archify_exists": (hub / "archify").is_dir(),
        "vault_exists": (hub / "vault").is_dir(),
        "root_graphify_out": link_state,
        "legacy_archify_exists": (hub.parent / ".archify").exists(),
        "scopes": sorted(child.name for child in hub.iterdir() if child.is_dir() and not child.is_symlink() and (child / "version-ledger.json").is_file()) if hub.is_dir() else [],
    }


def prepare(project: Path, *, scope: str, migrate_existing: bool = False) -> dict[str, object]:
    if migrate_existing:
        raise ValueError("기존 결과는 내부 링크와 생성기를 확인해야 하므로 자동 이동하지 않습니다.")
    hub, _, _ = paths(project)
    name = scope_name(scope)
    scoped = hub / name
    if hub.exists() and not hub.is_dir():
        raise ValueError(f"분석 폴더 경로를 사용할 수 없습니다: {hub}")
    if scoped.is_symlink() or (scoped.exists() and not scoped.is_dir()):
        raise ValueError(f"범위 폴더 경로를 사용할 수 없습니다: {scoped}")
    hub.mkdir(exist_ok=True)
    scoped.mkdir(exist_ok=True)
    return status(project, name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--scope", help="codebase-map 아래의 분석 범위 이름")
    parser.add_argument("action", choices=("status", "prepare"))
    args = parser.parse_args()
    try:
        if args.action == "prepare" and args.scope is None:
            raise ValueError("새 코드그래프는 --scope로 분석 범위를 지정해야 합니다.")
        result = (
            status(args.project, args.scope)
            if args.action == "status"
            else prepare(args.project, scope=args.scope)
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
