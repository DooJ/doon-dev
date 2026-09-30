#!/usr/bin/env python3
"""Keep a plugin's installed skills while controlling which ones may run."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


class ActivationError(RuntimeError):
    pass


def catalog() -> tuple[str, list[str], dict[str, str]]:
    data = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    plugin = data["plugin"]["name"]
    names = [item["name"] for item in data["skills"]]
    parents: dict[str, str] = {}
    for group in data.get("activation_groups", []):
        parent = group["parent"]
        if parent not in names:
            raise ActivationError(f"알 수 없는 상위 스킬: {parent}")
        for child in group["children"]:
            if child not in names or child == parent or child in parents:
                raise ActivationError(f"잘못된 하위 스킬: {child}")
            parents[child] = parent
    return plugin, names, parents


def config_dir() -> Path:
    if os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "DooN" / "skill-activation"
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "doon" / "skill-activation"


def state_path(plugin: str) -> Path:
    return config_dir() / f"{plugin}.json"


def read_state(plugin: str, names: list[str]) -> dict[str, Any]:
    path = state_path(plugin)
    if not path.is_file():
        return {"schema_version": 1, "disabled_skills": [], "managed_claude_denies": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ActivationError(f"활성화 설정을 읽을 수 없습니다: {path}: {error}") from error
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ActivationError(f"지원하지 않는 활성화 설정입니다: {path}")
    for key in ("disabled_skills", "managed_claude_denies"):
        if not isinstance(data.get(key), list) or not all(isinstance(x, str) for x in data[key]):
            raise ActivationError(f"잘못된 활성화 설정입니다: {path}: {key}")
    unknown = set(data["disabled_skills"]) - set(names)
    if unknown:
        raise ActivationError("등록되지 않은 비활성 스킬: " + ", ".join(sorted(unknown)))
    return data


def effective_disabled(names: list[str], parents: dict[str, str], disabled: set[str]) -> list[str]:
    return sorted(name for name in names if name in disabled or parents.get(name) in disabled)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    original_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.chmod(temporary, original_mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def codex_skill_paths(plugin: str, disabled: list[str]) -> list[Path]:
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    paths: set[Path] = set()
    for name in disabled:
        source = ROOT / "skills" / name
        if (source / "SKILL.md").is_file():
            paths.add(source.resolve())
        for cached in (home / "plugins" / "cache").glob(f"*/{plugin}/*/skills/{name}"):
            if (cached / "SKILL.md").is_file():
                paths.add(cached.resolve())
    return sorted(paths)


def apply_codex(plugin: str, disabled: list[str], path: Path | None = None) -> bool:
    config = path or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"
    existing = config.read_text(encoding="utf-8") if config.is_file() else ""
    start = f"# >>> DooN skill activation: {plugin} >>>"
    end = f"# <<< DooN skill activation: {plugin} <<<"
    pattern = re.compile(rf"(?m)^{re.escape(start)}\n.*?^{re.escape(end)}\n?", re.DOTALL)
    if existing.count(start) != existing.count(end) or existing.count(start) > 1:
        raise ActivationError(f"Codex 활성화 블록을 안전하게 갱신할 수 없습니다: {config}")
    base = pattern.sub("", existing)
    try:
        parsed = tomllib.loads(base)
    except tomllib.TOMLDecodeError as error:
        raise ActivationError(f"Codex 설정 문법 오류: {config}: {error}") from error
    existing_paths = {
        item.get("path") for item in parsed.get("skills", {}).get("config", [])
        if isinstance(item, dict)
    }
    paths = codex_skill_paths(plugin, disabled)
    if not paths and start not in existing:
        return False
    conflicts = [str(item) for item in paths if str(item) in existing_paths]
    if conflicts:
        raise ActivationError("Codex에 같은 스킬의 수동 설정이 있습니다: " + ", ".join(conflicts))
    block = ""
    if paths:
        lines = [start]
        for skill_path in paths:
            lines.extend(("[[skills.config]]", f"path = {json.dumps(str(skill_path))}", "enabled = false"))
        lines.append(end)
        block = "\n".join(lines) + "\n"
    result = base.rstrip("\n") + ("\n\n" if base.strip() and block else "\n" if base.strip() else "") + block
    tomllib.loads(result)
    if result == existing or (not config.exists() and not block):
        return False
    write_text(config, result)
    return True


def claude_deny_rules(plugin: str, disabled: list[str]) -> list[str]:
    rules = []
    for name in disabled:
        rules.extend((f"Skill({plugin}:{name})", f"Skill({plugin}:{name} *)"))
    return rules


def other_marketplace_installs(agent: str, plugin: str, target_marketplace: str) -> list[str]:
    """Find an already installed copy without relying on a particular marketplace name."""
    if agent not in {"codex", "claude"}:
        raise ActivationError(f"지원하지 않는 에이전트: {agent}")
    result = subprocess.run([agent, "plugin", "list", "--json"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise ActivationError(f"{agent}의 플러그인 설치 목록을 확인할 수 없습니다: {result.stderr.strip()}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ActivationError(f"{agent}의 플러그인 설치 목록이 유효한 JSON이 아닙니다") from error
    entries = data.get("installed", []) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise ActivationError(f"{agent}의 플러그인 설치 목록 형식이 잘못됐습니다")
    conflicts = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("installed", True) is False:
            continue
        identity = entry.get("pluginId", entry.get("id"))
        if not isinstance(identity, str) or "@" not in identity:
            continue
        name, marketplace = identity.split("@", 1)
        if name == plugin and marketplace != target_marketplace:
            conflicts.append(identity)
    return sorted(set(conflicts))


def apply_claude(plugin: str, disabled: list[str], state: dict[str, Any], path: Path | None = None) -> bool:
    settings = path or Path.home() / ".claude" / "settings.json"
    if not settings.is_file() and not disabled and not state["managed_claude_denies"]:
        return False
    try:
        data = json.loads(settings.read_text(encoding="utf-8")) if settings.is_file() else {}
    except (OSError, json.JSONDecodeError) as error:
        raise ActivationError(f"Claude 설정을 읽을 수 없습니다: {settings}: {error}") from error
    if not isinstance(data, dict):
        raise ActivationError(f"Claude 설정은 JSON 객체여야 합니다: {settings}")
    permissions = data.setdefault("permissions", {})
    if not isinstance(permissions, dict) or not isinstance(permissions.get("deny", []), list):
        raise ActivationError(f"Claude 권한 설정 형식이 잘못됐습니다: {settings}")
    current = permissions.get("deny", [])
    managed = set(state["managed_claude_denies"])
    retained = [rule for rule in current if rule not in managed]
    desired = claude_deny_rules(plugin, disabled)
    new_managed = [rule for rule in desired if rule not in retained]
    updated = retained + new_managed
    state["managed_claude_denies"] = new_managed
    if updated == current:
        return False
    permissions["deny"] = updated
    write_text(settings, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="설치된 플러그인 스킬의 사용 상태를 관리합니다.")
    parser.add_argument("command", choices=("status", "enable", "disable", "apply", "conflict"))
    parser.add_argument("skill", nargs="?")
    parser.add_argument("--marketplace")
    parser.add_argument("--skip-codex", action="store_true")
    parser.add_argument("--skip-claude", action="store_true")
    args = parser.parse_args()
    plugin, names, parents = catalog()
    if args.command == "conflict":
        if args.skill not in {"codex", "claude"}:
            parser.error("conflict에는 codex 또는 claude를 지정하세요.")
        conflicts = other_marketplace_installs(args.skill, plugin, args.marketplace or plugin)
        if conflicts:
            print("다른 마켓플레이스에 이미 설치됨: " + ", ".join(conflicts))
            return 0
        return 1
    if args.marketplace:
        parser.error("--marketplace는 conflict에서만 사용합니다.")
    state = read_state(plugin, names)
    disabled = set(state["disabled_skills"])
    if args.command in {"enable", "disable"}:
        if args.skill not in names:
            parser.error("catalog.json에 등록된 스킬 이름을 지정하세요.")
        if args.command == "disable":
            disabled.add(args.skill)
        else:
            disabled.discard(args.skill)
    elif args.skill:
        parser.error("status와 apply에는 스킬 이름을 지정하지 않습니다.")
    state["disabled_skills"] = sorted(disabled)
    unavailable = effective_disabled(names, parents, disabled)
    if args.command != "status":
        if not args.skip_claude and shutil.which("claude"):
            apply_claude(plugin, unavailable, state)
        write_text(state_path(plugin), json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        if not args.skip_codex and shutil.which("codex"):
            apply_codex(plugin, unavailable)
    print(json.dumps({
        "plugin": plugin,
        "disabled_skills": state["disabled_skills"],
        "effective_disabled": unavailable,
        "activation_groups": [
            {"parent": parent, "children": sorted(child for child, owner in parents.items() if owner == parent)}
            for parent in sorted(set(parents.values()))
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ActivationError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from error
