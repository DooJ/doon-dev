#!/usr/bin/env python3
"""프로젝트의 코드베이스 지식 폴더와 Graphify 호환 링크를 점검·준비한다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


HUB_NAME = "codebase-map"
GRAPH_NAME = "graphify-out"


def paths(project: Path) -> tuple[Path, Path, Path]:
    root = project.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"프로젝트 폴더가 없습니다: {root}")
    hub = root / HUB_NAME
    if hub.is_symlink():
        raise ValueError(f"분석 폴더가 심볼릭 링크입니다: {hub}")
    graph = hub / GRAPH_NAME
    if graph.is_symlink():
        raise ValueError(f"Graphify 데이터 폴더가 심볼릭 링크입니다: {graph}")
    return hub, graph, root / GRAPH_NAME


def status(project: Path) -> dict[str, str | bool]:
    hub, graph, link = paths(project)
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
    }


def prepare(project: Path, *, migrate_existing: bool) -> dict[str, str | bool]:
    hub, graph, link = paths(project)
    if hub.exists() and not hub.is_dir():
        raise ValueError(f"분석 폴더 경로를 사용할 수 없습니다: {hub}")
    for name in ("archify", "vault"):
        if (hub / name).is_symlink():
            raise ValueError(f"관리 폴더가 심볼릭 링크입니다: {hub / name}")
    if link.is_symlink():
        if link.resolve(strict=False) != graph.resolve(strict=False):
            raise ValueError(f"기존 Graphify 링크가 다른 위치를 가리킵니다: {link}")
    elif link.exists():
        if not link.is_dir():
            raise ValueError(f"기존 Graphify 경로가 폴더가 아닙니다: {link}")
        if not migrate_existing:
            raise ValueError("기존 graphify-out 실폴더가 있습니다. 확인 후 --migrate-existing을 지정하세요.")
        if graph.exists():
            raise ValueError(f"이동 대상이 이미 존재합니다: {graph}")

    hub.mkdir(exist_ok=True)
    if link.exists() and not link.is_symlink():
        link.rename(graph)
    else:
        graph.mkdir(exist_ok=True)
    (hub / "archify").mkdir(exist_ok=True)
    (hub / "vault").mkdir(exist_ok=True)
    if not link.is_symlink():
        link.symlink_to(Path(HUB_NAME) / GRAPH_NAME, target_is_directory=True)
    return status(project)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("action", choices=("status", "prepare"))
    parser.add_argument("--migrate-existing", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            status(args.project)
            if args.action == "status"
            else prepare(args.project, migrate_existing=args.migrate_existing)
        )
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
