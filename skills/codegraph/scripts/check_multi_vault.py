#!/usr/bin/env python3
"""Validate a versioned data catalog and independent Obsidian vault projections."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


class VaultError(ValueError):
    pass


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VaultError(f"JSON을 읽을 수 없습니다: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VaultError(f"JSON 객체가 필요합니다: {path}")
    return value


def digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise VaultError(f"파일을 읽을 수 없습니다: {path}: {exc}") from exc


def inside(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise VaultError(f"{label} 경로가 허용 범위를 벗어납니다: {path}")
    return resolved


def check(version: Path) -> dict[str, int]:
    version = version.resolve()
    catalog_path = version / "data/catalog.json"
    catalog = load(catalog_path)
    if catalog.get("schema_version") != 1:
        raise VaultError("data/catalog.json의 schema_version은 1이어야 합니다")
    sources = catalog.get("sources")
    if not isinstance(sources, dict) or "capabilities" not in sources:
        raise VaultError("데이터 목록에 capabilities 입력이 필요합니다")
    source_hashes: dict[str, str] = {}
    for name, entry in sources.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise VaultError(f"입력 경로가 없습니다: {name}")
        source_path = (catalog_path.parent / entry["path"]).resolve()
        # A new version may inherit a prior version's immutable data, but the
        # link must stay within this analysis scope rather than escape to any file.
        inside(source_path, version.parent, f"입력 {name}")
        actual = digest(source_path)
        if entry.get("sha256") != actual:
            raise VaultError(f"입력 지문이 다릅니다: {name}")
        source_hashes[name] = actual

    project_data = load((catalog_path.parent / sources["capabilities"]["path"]).resolve())
    projects = project_data.get("projects")
    if not isinstance(projects, list) or not projects:
        raise VaultError("기능 지도에 프로젝트가 없습니다")
    project_ids = {item["id"] for item in projects}
    if len(project_ids) != len(projects):
        raise VaultError("기능 지도에 중복 프로젝트 ID가 있습니다")
    counts = catalog.get("counts", {})
    if counts.get("solutions") != len(projects):
        raise VaultError("데이터 목록의 솔루션 수가 실제 프로젝트 수와 다릅니다")
    if "methods" in sources:
        method_data = load((catalog_path.parent / sources["methods"]["path"]).resolve())
        if counts.get("methods") != len(method_data.get("nodes", [])) or counts.get("static_edges") != len(method_data.get("edges", [])):
            raise VaultError("데이터 목록의 메서드·정적 연결 수가 원본과 다릅니다")
        if {item["project"] for item in method_data["nodes"]} != project_ids:
            raise VaultError("메서드 색인의 프로젝트 범위가 기능 지도와 다릅니다")
    if "reviewed_flows" in sources:
        reviewed = load((catalog_path.parent / sources["reviewed_flows"]["path"]).resolve())
        for key, field in (("reviewed_nodes", "nodes"), ("reviewed_edges", "edges"), ("reviewed_flows", "flows")):
            if counts.get(key) != len(reviewed.get(field, [])):
                raise VaultError(f"데이터 목록의 {key} 수가 원본과 다릅니다")
        node_ids = {item["id"] for item in reviewed["nodes"]}
        edge_ids = {item["id"] for item in reviewed["edges"]}
        if len(node_ids) != len(reviewed["nodes"]) or len(edge_ids) != len(reviewed["edges"]):
            raise VaultError("검토 흐름의 노드·연결 ID가 중복됩니다")
        if any(edge["source"] not in node_ids or edge["target"] not in node_ids for edge in reviewed["edges"]):
            raise VaultError("검토 연결의 양쪽 노드가 없습니다")
        if any(not set(flow["nodes"]) <= node_ids or not set(flow["edges"]) <= edge_ids for flow in reviewed["flows"]):
            raise VaultError("검토 흐름이 존재하지 않는 노드·연결을 참조합니다")

    registry_path = inside(catalog_path.parent / catalog.get("vault_registry", ""), version, "볼트 목록")
    registry = load(registry_path).get("vaults")
    if not isinstance(registry, list) or not registry:
        raise VaultError("볼트 목록이 비어 있습니다")
    names = {item["vault_name"] for item in registry}
    ids = {item["id"] for item in registry}
    if len(names) != len(registry) or len(ids) != len(registry):
        raise VaultError("중복 볼트 이름 또는 ID가 있습니다")
    solution_ids = {item["id"] for item in registry if item.get("kind") == "solution"}
    if solution_ids != project_ids:
        raise VaultError(f"솔루션 볼트 누락·초과: {sorted(solution_ids ^ project_ids)}")
    hubs = [item for item in registry if item.get("kind") == "hub"]
    if len(projects) > 1 and len(hubs) != 1:
        raise VaultError("다중 프로젝트에는 상위 볼트가 정확히 하나 필요합니다")
    roots = {}
    vaults_root = version / "vaults"
    if (vaults_root / ".obsidian").exists():
        raise VaultError("vaults/ 컨테이너 자체를 볼트로 열면 안 됩니다")
    for item in registry:
        root = inside(version / item["path"], vaults_root, "볼트")
        if root.parent != vaults_root.resolve() or root.name != item["vault_name"]:
            raise VaultError(f"볼트는 vaults/ 직계 폴더이며 폴더명이 고유 이름이어야 합니다: {root}")
        if not (root / item.get("home", "00_HOME.md")).is_file():
            raise VaultError(f"볼트 홈이 없습니다: {root}")
        if not (root / ".obsidian").is_dir():
            raise VaultError(f"독립 볼트 설정 폴더가 없습니다: {root}")
        roots[item["vault_name"]] = root

    manifest_path = version / "generation-manifest.json"
    manifest = load(manifest_path)
    if manifest.get("inputs") != source_hashes:
        raise VaultError("생성 manifest의 입력 지문이 데이터 목록과 다릅니다")
    generated = manifest.get("generated")
    if not isinstance(generated, list) or not generated:
        raise VaultError("생성 파일 목록이 없습니다")
    owned = set()
    for item in generated:
        path = inside(version / item["path"], version, "생성 파일")
        if path in owned or digest(path) != item.get("sha256"):
            raise VaultError(f"생성 파일의 중복 또는 지문 불일치: {path}")
        owned.add(path)

    notes_count = links_count = uris_count = 0
    for vault_name, root in roots.items():
        notes = {str(path.relative_to(root).with_suffix("")): path for path in root.rglob("*.md")}
        graph: dict[str, set[str]] = defaultdict(set)
        for name, path in notes.items():
            if path.resolve() in owned and re.fullmatch(r"[0-9a-fA-F]{12,64}", path.stem):
                raise VaultError(f"그래프에서 식별할 수 없는 해시 전용 생성 노트명: {vault_name}/{name}")
            content = path.read_text(encoding="utf-8")
            for raw in re.findall(r"\[\[([^\]]+)\]\]", content):
                target = raw.split(r"\|", 1)[0].split("|", 1)[0].split("#", 1)[0]
                if target not in notes:
                    raise VaultError(f"볼트 내부 링크가 끊겼습니다: {vault_name}/{name} → {target}")
                graph[name].add(target)
                links_count += 1
            for raw in re.findall(r"\]\((obsidian://[^)]+)\)", content):
                parsed = urlparse(raw)
                params = parse_qs(parsed.query)
                if parsed.netloc != "open" or "vault" not in params or "file" not in params:
                    raise VaultError(f"볼트 이동 URI가 올바르지 않습니다: {raw}")
                target_vault = params["vault"][0]
                target_file = params["file"][0]
                if target_vault not in roots:
                    raise VaultError(f"볼트 이동 대상이 없습니다: {raw}")
                target_path = inside(roots[target_vault] / target_file, roots[target_vault], "볼트 이동")
                if not target_path.is_file():
                    raise VaultError(f"볼트 이동 대상이 없습니다: {raw}")
                uris_count += 1
            for raw in re.findall(r"\]\(([^)]+)\)", content):
                if raw.startswith(("http:", "https:", "obsidian:", "mailto:", "#")):
                    continue
                target = unquote(raw.split("#", 1)[0])
                if target and not (path.parent / target).exists():
                    raise VaultError(f"로컬 파일 링크가 끊겼습니다: {vault_name}/{name} → {raw}")
        reached = {"00_HOME"}
        queue = deque(reached)
        while queue:
            for target in graph[queue.popleft()]:
                if target not in reached:
                    reached.add(target)
                    queue.append(target)
        generated_notes = {str(path.relative_to(root).with_suffix("")) for path in owned if path.suffix == ".md" and path.is_relative_to(root)}
        if not generated_notes <= reached:
            raise VaultError(f"홈에서 닿지 않는 생성 노트: {vault_name}: {sorted(generated_notes - reached)[:5]}")
        notes_count += len(notes)

    return {"vaults": len(registry), "solutions": len(projects), "notes": notes_count,
            "links": links_count, "cross_vault_uris": uris_count, "owned_files": len(owned)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps({"ok": True, **check(args.version_dir)}, ensure_ascii=False))
        return 0
    except (VaultError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
