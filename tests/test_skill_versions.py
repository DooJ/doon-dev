from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills/skill-versioning/scripts/skill_versions.py"


def load_module():
    spec = importlib.util.spec_from_file_location("plugin_skill_versions", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"모듈을 불러올 수 없습니다: {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()

    def write_skill(self, root: Path, name: str = "sample-skill") -> Path:
        skill = root / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Use when testing.\n---\n\n# Sample\n",
            encoding="utf-8",
        )
        return skill

    def write_plugin_metadata(self, root: Path, version: str, skill_name: str) -> None:
        manifests = [
            root / "plugin.json",
            root / ".codex-plugin/plugin.json",
            root / ".claude-plugin/plugin.json",
        ]
        for path in manifests:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"name": "sample", "version": version}), encoding="utf-8")
        (root / "catalog.json").write_text(
            json.dumps(
                {
                    "repository": "owner/sample",
                    "skills": [{"name": skill_name, "path": f"skills/{skill_name}"}],
                    "plugin": {"name": "sample", "version": version, "display_name": "Sample"},
                }
            ),
            encoding="utf-8",
        )
        (root / "PLUGIN_VERSION.md").write_text(
            f"# Sample 플러그인 버전\n\n현재 버전: `v{version}`\n",
            encoding="utf-8",
        )

    def write_record(self, skill: Path, version: str = "v1.0.0") -> None:
        digest = self.module.fingerprint(skill)
        (skill / "VERSION.md").write_text(
            "\n".join(
                [
                    f"# {skill.name} 버전·출처",
                    "",
                    f"현재 버전: `{version}`",
                    f"내용 SHA-256: `sha256:{digest}`",
                    "",
                    "## 출처",
                    "",
                    "| ID | 분류 | 자료 | 반영 범위 |",
                    "|---|---|---|---|",
                    "| `S1` | 자체 생성 | 테스트 | 검증 동작 |",
                    "",
                    "## 버전 이력",
                    "",
                    "| 버전 | 날짜 | 변경 요약 | 출처 ID |",
                    "|---|---|---|---|",
                    f"| `{version}` | 2026-09-29 | 독립 저장소 검증 동작을 등록했다. | `S1` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def test_fingerprint_ignores_version_record_and_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self.write_skill(Path(temporary))
            before = self.module.fingerprint(skill)
            (skill / "VERSION.md").write_text("ignored", encoding="utf-8")
            (skill / ".DS_Store").write_text("ignored", encoding="utf-8")
            cache = skill / "__pycache__"
            cache.mkdir()
            (cache / "cache.pyc").write_bytes(b"ignored")
            self.assertEqual(before, self.module.fingerprint(skill))

    def test_check_accepts_complete_skill_and_aligned_plugin_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = self.write_skill(root)
            self.write_record(skill)
            self.write_plugin_metadata(root, "1.2.3", skill.name)
            self.assertEqual([], self.module.validate_repository(root))

    def test_check_rejects_stale_fingerprint_and_plugin_version_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = self.write_skill(root)
            self.write_record(skill)
            self.write_plugin_metadata(root, "1.2.3", skill.name)
            (skill / "SKILL.md").write_text("changed", encoding="utf-8")
            manifest = root / ".codex-plugin/plugin.json"
            manifest.write_text(json.dumps({"name": "sample", "version": "9.9.9"}), encoding="utf-8")

            errors = self.module.validate_repository(root)

            self.assertTrue(any("내용 지문" in error for error in errors))
            self.assertTrue(any("플러그인 버전" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
