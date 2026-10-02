#!/usr/bin/env python3
"""Validate a source-backed project capability inventory and render its vault map."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path


KINDS = {
    "cooperation": "협력 연결",
    "shared_implementation": "공통 구현 사용",
    "duplicate_implementation": "중복 구현",
    "similar_distinct": "유사하지만 목적이 다름",
    "unverified": "확인 필요",
}
STATUSES = {
    "static_confirmed": "정적 확인",
    "inferred": "추정",
    "runtime_required": "운영 확인 필요",
}
EVIDENCE_BASES = {"source", "archive", "config"}
MANIFEST_NAME = "80_Generated/capability-map-manifest.json"
LEGACY_MANIFEST_NAME = "80_Generated/manifest.json"


class MapError(ValueError):
    pass


def require_text(value: object, location: str, minimum: int = 8) -> str:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise MapError(f"{location}: 구체적인 설명이 필요합니다")
    result = value.strip()
    if re.search(r"\b(TODO|TBD|placeholder|추후 작성)\b", result, re.I):
        raise MapError(f"{location}: 임시 문구를 완료 내용으로 사용할 수 없습니다")
    return result


def require_id(value: object, location: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", value):
        raise MapError(f"{location}: 안정적인 영문 ID가 필요합니다")
    return value


def require_list(value: object, location: str, minimum: int = 1) -> list:
    if not isinstance(value, list) or len(value) < minimum:
        raise MapError(f"{location}: {minimum}개 이상 필요합니다")
    return value


def evidence_items(value: object, location: str, project_root: Path) -> list[dict]:
    items = require_list(value, location)
    for index, item in enumerate(items):
        position = f"{location}[{index}]"
        if not isinstance(item, dict):
            raise MapError(f"{position}: 근거 객체가 필요합니다")
        path = require_text(item.get("path"), f"{position}.path", 1)
        if Path(path).is_absolute():
            raise MapError(f"{position}.path: 프로젝트 상대경로만 허용합니다")
        source = (project_root / path).resolve()
        if not source.is_file():
            raise MapError(f"{position}.path: 파일을 찾을 수 없습니다: {path}")
        require_text(item.get("locator"), f"{position}.locator", 2)
        if item.get("basis") not in EVIDENCE_BASES:
            raise MapError(f"{position}.basis: source, archive, config 중 하나여야 합니다")
    return items


def validate(data: object, project_root: Path, expected: list[str]) -> dict:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise MapError("schema_version은 1이어야 합니다")
    require_text(data.get("scope"), "scope", 2)
    if not isinstance(data.get("version"), str) or not re.fullmatch(r"v\d+\.\d+\.\d+", data["version"]):
        raise MapError("version은 vX.Y.Z 형식이어야 합니다")
    requested = [require_id(x, "requested_projects") for x in require_list(data.get("requested_projects"), "requested_projects")]
    if len(set(requested)) != len(requested):
        raise MapError("requested_projects에 중복 ID가 있습니다")
    if expected and set(expected) != set(requested):
        raise MapError(f"요청 범위 불일치: 입력={sorted(requested)}, 명령={sorted(expected)}")

    projects = require_list(data.get("projects"), "projects")
    project_by_id: dict[str, dict] = {}
    note_names: set[str] = set()
    for index, project in enumerate(projects):
        where = f"projects[{index}]"
        if not isinstance(project, dict):
            raise MapError(f"{where}: 프로젝트 객체가 필요합니다")
        project_id = require_id(project.get("id"), f"{where}.id")
        if project_id in project_by_id:
            raise MapError(f"중복 프로젝트 ID: {project_id}")
        name = require_text(project.get("name"), f"{where}.name", 2)
        if any(character in name for character in ("|", "[", "]", "\n")):
            raise MapError(f"{where}.name: 위키링크를 깨는 문자는 사용할 수 없습니다")
        note = project.get("note", project_id)
        if not isinstance(note, str) or not re.fullmatch(r"[\w가-힣 -]+", note):
            raise MapError(f"{where}.note: 안전한 노트 파일명이 필요합니다")
        if note in note_names:
            raise MapError(f"{where}.note: 중복 노트 파일명")
        note_names.add(note)
        require_text(project.get("role"), f"{where}.role", 12)
        capabilities = require_list(project.get("capabilities"), f"{where}.capabilities")
        capability_ids: set[str] = set()
        for number, capability in enumerate(capabilities):
            place = f"{where}.capabilities[{number}]"
            if not isinstance(capability, dict):
                raise MapError(f"{place}: 기능 객체가 필요합니다")
            capability_id = require_id(capability.get("id"), f"{place}.id")
            if capability_id in capability_ids:
                raise MapError(f"{place}: 중복 기능 ID")
            capability_ids.add(capability_id)
            require_text(capability.get("name"), f"{place}.name", 2)
            require_text(capability.get("description"), f"{place}.description", 15)
            evidence_items(capability.get("evidence"), f"{place}.evidence", project_root)
        if "unknowns" not in project or not isinstance(project["unknowns"], list):
            raise MapError(f"{where}.unknowns: 확인하지 못한 범위 목록이 필요합니다")
        for unknown in project["unknowns"]:
            require_text(unknown, f"{where}.unknowns", 5)
        project_by_id[project_id] = project
    if set(project_by_id) != set(requested):
        raise MapError(f"프로젝트 누락·초과: 요청={sorted(requested)}, 작성={sorted(project_by_id)}")

    relations = require_list(data.get("relations"), "relations", 0 if len(projects) == 1 else 1)
    relation_ids: set[str] = set()
    related_projects: set[str] = set()
    for index, relation in enumerate(relations):
        where = f"relations[{index}]"
        if not isinstance(relation, dict):
            raise MapError(f"{where}: 관계 객체가 필요합니다")
        relation_id = require_id(relation.get("id"), f"{where}.id")
        if relation_id in relation_ids:
            raise MapError(f"{where}: 중복 관계 ID")
        relation_ids.add(relation_id)
        require_text(relation.get("function"), f"{where}.function", 2)
        kind = relation.get("kind")
        if kind not in KINDS:
            raise MapError(f"{where}.kind: 지원하지 않는 관계 유형")
        if relation.get("status") not in STATUSES:
            raise MapError(f"{where}.status: 확인 수준이 필요합니다")
        require_text(relation.get("contract"), f"{where}.contract", 12)
        require_text(relation.get("result"), f"{where}.result", 12)
        if kind in {"duplicate_implementation", "shared_implementation", "similar_distinct"}:
            require_text(relation.get("comparison"), f"{where}.comparison", 20)
        participants = require_list(relation.get("participants"), f"{where}.participants", 2)
        member_ids: set[str] = set()
        for number, member in enumerate(participants):
            place = f"{where}.participants[{number}]"
            if not isinstance(member, dict):
                raise MapError(f"{place}: 참여 프로젝트 객체가 필요합니다")
            project_id = require_id(member.get("project"), f"{place}.project")
            if project_id not in project_by_id or project_id in member_ids:
                raise MapError(f"{place}: 범위 밖 또는 중복 프로젝트: {project_id}")
            member_ids.add(project_id)
            require_text(member.get("responsibility"), f"{place}.responsibility", 10)
            evidence_items(member.get("evidence"), f"{place}.evidence", project_root)
        related_projects.update(member_ids)
        if kind == "duplicate_implementation" and len(member_ids) < 2:
            raise MapError(f"{where}: 중복 구현은 두 구현의 근거가 필요합니다")
        unknowns = relation.get("unknowns", [])
        if not isinstance(unknowns, list):
            raise MapError(f"{where}.unknowns: 목록이 필요합니다")
        for unknown in unknowns:
            require_text(unknown, f"{where}.unknowns", 5)
    for project_id, project in project_by_id.items():
        if project_id not in related_projects:
            require_text(project.get("isolated_reason"), f"projects[{project_id}].isolated_reason", 12)
    return data


def evidence_text(items: list[dict]) -> str:
    return ", ".join(f"`{item['path']}#{item['locator']}` ({item['basis']})" for item in items)


def render_documents(data: dict) -> dict[str, str]:
    names = {item["id"]: item["name"] for item in data["projects"]}
    notes = {item["id"]: item.get("note", item["id"]) for item in data["projects"]}
    capability_lines = [
        "# 프로젝트별 역할과 주요 기능", "",
        f"범위: {data['scope']} · 버전: {data['version']}. 이 지도는 확인한 코드·설정·배포 아카이브의 근거를 기준으로 작성했다.", "",
        "| 프로젝트 | 역할 | 주요 기능 | 함께 참여하는 프로젝트 |", "|---|---|---|---|",
    ]
    for project in data["projects"]:
        project_id = project["id"]
        others = sorted({member["project"] for relation in data["relations"] for member in relation["participants"] if project_id in {p["project"] for p in relation["participants"]} and member["project"] != project_id})
        related = ", ".join(names[item] for item in others) or "확인된 연결 없음"
        features = ", ".join(item["name"] for item in project["capabilities"])
        capability_lines.append(f"| [[10_Projects/{notes[project_id]}|{project['name']}]] | {project['role']} | {features} | {related} |")
    capability_lines += ["", "## 기능과 근거", ""]
    for project in data["projects"]:
        capability_lines += [f"### [[10_Projects/{notes[project['id']]}|{project['name']}]]", ""]
        for capability in project["capabilities"]:
            capability_lines.append(f"- **{capability['name']}**: {capability['description']} 근거: {evidence_text(capability['evidence'])}")
        if project["unknowns"]:
            capability_lines.append("- **미확인:** " + "; ".join(project["unknowns"]))
        capability_lines.append("")
    capability_lines += ["프로젝트 사이 기능의 책임·계약·중복 판정은 [[03_FUNCTION_RELATIONS]]에서 확인한다.", ""]

    relation_lines = [
        "# 프로젝트 간 기능 관계", "",
        "같은 API나 공통 라이브러리를 사용한다는 사실만으로 중복 구현으로 분류하지 않는다. [[02_PROJECT_CAPABILITIES|프로젝트별 기능 지도]]에서 각 프로젝트의 역할을 먼저 볼 수 있다.", "",
    ]
    if not any(relation["kind"] == "duplicate_implementation" for relation in data["relations"]):
        relation_lines += ["**이번 근거에서 중복 구현으로 확정한 기능은 없다.** 유사 기능과 공통 구현은 아래에서 별도로 비교한다.", ""]
    for relation in data["relations"]:
        relation_lines += [f"## {relation['function']}", "", f"**관계:** {KINDS[relation['kind']]} · **확인 수준:** {STATUSES[relation['status']]}", ""]
        for member in relation["participants"]:
            relation_lines.append(f"- [[10_Projects/{notes[member['project']]}|{names[member['project']]}]]: {member['responsibility']} 근거: {evidence_text(member['evidence'])}")
        relation_lines += ["", f"**연결 계약:** {relation['contract']}", "", f"**결과:** {relation['result']}", ""]
        if relation.get("comparison"):
            relation_lines += [f"**구현 비교:** {relation['comparison']}", ""]
        if relation.get("unknowns"):
            relation_lines += ["**미확인:** " + "; ".join(relation["unknowns"]), ""]
    if not data["relations"]:
        relation_lines += ["이 범위에서 확인된 프로젝트 간 기능 관계는 없다.", ""]

    documents = {
        "02_PROJECT_CAPABILITIES.md": "\n".join(capability_lines).rstrip() + "\n",
        "03_FUNCTION_RELATIONS.md": "\n".join(relation_lines).rstrip() + "\n",
    }
    for project in data["projects"]:
        project_id = project["id"]
        lines = [f"# {project['name']}", "", f"**시스템 역할:** {project['role']}", "", "## 주요 기능", ""]
        for capability in project["capabilities"]:
            lines += [f"### {capability['name']}", "", capability["description"], "", f"근거: {evidence_text(capability['evidence'])}", ""]
        lines += ["## 다른 프로젝트와의 관계", ""]
        project_relations = [relation for relation in data["relations"] if project_id in {member["project"] for member in relation["participants"]}]
        for relation in project_relations:
            partners = ", ".join(f"[[10_Projects/{notes[member['project']]}|{names[member['project']]}]]" for member in relation["participants"] if member["project"] != project_id)
            member = next(member for member in relation["participants"] if member["project"] == project_id)
            lines.append(f"- **{relation['function']}** ({KINDS[relation['kind']]} · {STATUSES[relation['status']]}): {member['responsibility']} 연결 대상: {partners}. 계약: {relation['contract']} 결과: {relation['result']}")
        if not project_relations:
            lines.append(f"- 확인된 연결 없음: {project['isolated_reason']}")
        lines += ["", "## 확인하지 못한 범위", ""]
        lines.extend(f"- {item}" for item in project["unknowns"])
        if not project["unknowns"]:
            lines.append("- 이번 범위에서 추가로 명시한 공백 없음.")
        lines += ["", "[[02_PROJECT_CAPABILITIES|전체 프로젝트 지도]] · [[03_FUNCTION_RELATIONS|기능 관계 지도]]", ""]
        documents[f"10_Projects/{notes[project_id]}.md"] = "\n".join(lines).rstrip() + "\n"
    return documents


def existing_hashes(vault: Path) -> dict[str, str]:
    for name in (MANIFEST_NAME, LEGACY_MANIFEST_NAME):
        manifest = vault / name
        if manifest.exists():
            content = json.loads(manifest.read_text(encoding="utf-8"))
            return {item["path"]: item["sha256"] for item in content.get("files", [])}
    return {}


def write_documents(vault: Path, documents: dict[str, str], scope: str, version: str, shortening_reason: str | None) -> None:
    prior_manifest = vault / MANIFEST_NAME
    if prior_manifest.exists():
        prior_paths = {item["path"] for item in json.loads(prior_manifest.read_text(encoding="utf-8")).get("files", [])}
        removed = prior_paths - set(documents)
        if removed:
            raise MapError(f"기존 생성 노트가 입력에서 사라졌습니다. 별도 이전 절차가 필요합니다: {sorted(removed)}")
    ownership = existing_hashes(vault)
    for relative, content in documents.items():
        target = vault / relative
        if target.exists():
            previous = ownership.get(relative)
            if previous is None or hashlib.sha256(target.read_bytes()).hexdigest() != previous:
                raise MapError(f"소유권이 없거나 사용자가 수정한 노트입니다: {relative}")
            if len(content.encode("utf-8")) < target.stat().st_size and not shortening_reason:
                raise MapError(f"기존 노트보다 짧아졌습니다. 내용을 대조한 뒤 반영하세요: {relative}")
    vault.mkdir(parents=True, exist_ok=True)
    for relative, content in documents.items():
        target = vault / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, target)
    manifest = vault / MANIFEST_NAME
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "scope": scope, "version": version,
        "shortening_reason": shortening_reason,
        "files": [{"path": relative, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()} for relative, content in sorted(documents.items())],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    legacy_manifest = vault / LEGACY_MANIFEST_NAME
    if legacy_manifest.exists():
        legacy = json.loads(legacy_manifest.read_text(encoding="utf-8"))
        by_path = {item["path"]: item for item in legacy.get("files", [])}
        for relative, content in documents.items():
            by_path[relative] = {"path": relative, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}
        legacy["files"] = [by_path[key] for key in sorted(by_path)]
        legacy_manifest.write_text(json.dumps(legacy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_vault(data: dict, version_dir: Path, vault: Path, documents: dict[str, str]) -> None:
    manifest = vault / MANIFEST_NAME
    if not manifest.is_file():
        raise MapError(f"기능 지도 생성 manifest가 없습니다: {manifest}")
    entries = json.loads(manifest.read_text(encoding="utf-8")).get("files", [])
    if {item["path"] for item in entries} != set(documents):
        raise MapError("생성 manifest와 현재 입력의 노트 목록이 다릅니다")
    for relative, content in documents.items():
        path = vault / relative
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise MapError(f"기능 지도 노트가 입력과 다릅니다: {relative}")
    for item in entries:
        if hashlib.sha256((vault / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise MapError(f"생성 노트 지문이 맞지 않습니다: {item['path']}")

    home = vault / "00_HOME.md"
    if not home.is_file():
        raise MapError("볼트 시작 문서 00_HOME.md가 없습니다")
    home_text = home.read_text(encoding="utf-8")
    if "02_PROJECT_CAPABILITIES" not in home_text or "03_FUNCTION_RELATIONS" not in home_text:
        raise MapError("00_HOME.md에서 프로젝트·관계 지도로 이동할 수 없습니다")
    for path in [home, *(vault / relative for relative in documents)]:
        for raw in re.findall(r"\[\[([^\]]+)\]\]", path.read_text(encoding="utf-8")):
            target = raw.split("|", 1)[0].split("#", 1)[0]
            if target and not (vault / f"{target}.md").is_file() and not (path.parent / f"{target}.md").is_file():
                raise MapError(f"끊어진 볼트 링크: {path.name} → {raw}")
    if len(data["projects"]) > 1:
        if not (vault / "01_SYSTEM_MAP.md").is_file():
            raise MapError("여러 프로젝트의 시스템 지도 01_SYSTEM_MAP.md가 없습니다")
        if not (version_dir / "graphify-out/graph.json").is_file():
            raise MapError("Graphify 상세 그래프가 없습니다")
        if not any((version_dir / "archify").glob("**/index.html")):
            raise MapError("Archify 구조도가 없습니다")
        overview = version_dir / "graphify-out/overview/graph.json"
        if not overview.is_file():
            raise MapError("여러 프로젝트의 통합 개요 그래프가 없습니다")
        graph = json.loads(overview.read_text(encoding="utf-8"))
        node_ids = {node.get("id") for node in graph.get("nodes", [])}
        missing = set(data["requested_projects"]) - node_ids
        if missing:
            raise MapError(f"통합 개요 그래프에 요청 프로젝트가 빠졌습니다: {sorted(missing)}")
    if data["version"] != "v1.0.0" and not (version_dir / "CHANGE_REPORT.md").is_file():
        raise MapError("새 전체 버전의 CHANGE_REPORT.md가 없습니다")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "render", "check"))
    parser.add_argument("--input", type=Path, required=True, help="버전 폴더의 capability-map.json")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--vault", type=Path, help="render 대상 볼트")
    parser.add_argument("--expected-project", action="append", default=[], help="사용자가 요청한 프로젝트 ID; 반복 지정")
    parser.add_argument("--shortening-reason", help="기존 노트 축소를 검토하고 승인한 근거")
    args = parser.parse_args()
    try:
        data = validate(json.loads(args.input.read_text(encoding="utf-8")), args.project_root.resolve(), args.expected_project)
        documents = render_documents(data)
        if args.action in {"render", "check"}:
            if args.vault is None:
                raise MapError(f"{args.action}에는 --vault가 필요합니다")
            if args.input.resolve().parent.name != data["version"] or args.vault.resolve().parent != args.input.resolve().parent:
                raise MapError("입력 파일·볼트·버전 폴더가 같은 버전을 가리켜야 합니다")
            if args.action == "render":
                reason = require_text(args.shortening_reason, "shortening-reason", 12) if args.shortening_reason else None
                write_documents(args.vault.resolve(), documents, data["scope"], data["version"], reason)
            else:
                check_vault(data, args.input.resolve().parent, args.vault.resolve(), documents)
        print(json.dumps({"ok": True, "action": args.action, "projects": len(data["projects"]), "relations": len(data["relations"]), "documents": len(documents)}, ensure_ascii=False))
        return 0
    except (MapError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
