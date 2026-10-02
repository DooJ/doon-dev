"""프로젝트 코드그래프 버전과 구성요소 실행 이력의 회귀 검사."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/codegraph/scripts/version_ledger.py"
SPEC = importlib.util.spec_from_file_location("version_ledger", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CodegraphVersionLedgerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.hub = self.project / "codebase-map"
        self.root = self.hub / "보이미 생태계"
        self.root.mkdir(parents=True)
        self.scope = "보이미 생태계"
        self.version_root = self.root / "v1.0.0"
        MODULE.init(self.project, scope=self.scope)
        (self.version_root / "graphify-out").mkdir()
        (self.version_root / "graphify-out/graph.json").write_text('{"version":1}', encoding="utf-8")

    def test_component_runs_accumulate_without_bumping_overall_version(self) -> None:
        first, changed = MODULE.record(self.project, "graphify", ["graphify-out/graph.json"], "첫 그래프", self.scope)
        self.assertTrue(changed)
        self.assertEqual(first["versions"][-1]["version"], "v1.0.0")
        (self.version_root / "graphify-out/graph.json").write_text('{"version":2}', encoding="utf-8")
        second, changed = MODULE.record(self.project, "graphify", ["graphify-out/graph.json"], "그래프 보강", self.scope)
        self.assertTrue(changed)
        self.assertEqual(len(second["versions"][-1]["revisions"]["graphify"]), 2)
        self.assertIn("+", second["versions"][-1]["revisions"]["graphify"][0]["at"])
        self.assertEqual(second["versions"][-1]["version"], "v1.0.0")
        _, changed = MODULE.record(self.project, "graphify", ["graphify-out/graph.json"], "같은 결과", self.scope)
        self.assertFalse(changed)
        self.assertEqual(len(MODULE.load(self.root)["versions"][-1]["revisions"]["graphify"]), 2)

    def test_reclassifies_only_open_version_and_keeps_prior_history(self) -> None:
        MODULE.record(self.project, "graphify", ["graphify-out/graph.json"], "기준선", self.scope)
        MODULE.bump(self.project, "patch", "전체 지도 보강", self.scope)
        (self.root / "v1.0.1/archify").mkdir()
        (self.root / "v1.0.1/archify/diagram.json").write_text("{}", encoding="utf-8")
        MODULE.record(self.project, "archify", ["archify/diagram.json"], "구조도 추가", self.scope)
        result = MODULE.reclassify(self.project, "minor", "핵심 흐름 확장", self.scope)
        self.assertEqual([item["version"] for item in result["versions"]], ["v1.0.0", "v1.1.0"])
        self.assertEqual(result["versions"][0]["state"], "closed")
        self.assertEqual(len(result["versions"][1]["revisions"]["archify"]), 1)
        self.assertFalse((self.root / "v1.0.1").exists())
        self.assertTrue((self.root / "v1.1.0/archify/diagram.json").is_file())
        summary = (self.root / "VERSION.md").read_text(encoding="utf-8")
        self.assertIn("이전 결과 승계: v1.0.0", summary)
        self.assertIn("현재 버전: `v1.1.0`", summary)

    def test_rejects_unsafe_paths_and_preserves_existing_ledger(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.init(self.project, scope=self.scope)
        for path in ("../outside", "/tmp/outside"):
            with self.assertRaises(ValueError):
                MODULE.record(self.project, "graphify", [path], "잘못된 경로", self.scope)
        (self.version_root / "linked").symlink_to(self.version_root / "graphify-out", target_is_directory=True)
        with self.assertRaises(ValueError):
            MODULE.record(self.project, "graphify", ["linked/graph.json"], "링크 경유", self.scope)
        self.assertEqual(len(MODULE.load(self.root)["versions"][-1]["revisions"]["graphify"]), 0)

    def test_two_scopes_start_at_v1_independently(self) -> None:
        other = self.hub / "보이미 메뉴"
        other.mkdir()
        MODULE.init(self.project, scope="보이미 메뉴")
        MODULE.bump(self.project, "minor", "생태계 지도 확장", self.scope)
        self.assertEqual(MODULE.load(self.root)["versions"][-1]["version"], "v1.1.0")
        self.assertEqual(MODULE.load(other)["versions"][-1]["version"], "v1.0.0")
        self.assertTrue((other / "v1.0.0/VERSION.md").is_file())

    def test_existing_unscoped_ledger_remains_readable_without_new_init(self) -> None:
        import json

        old_root = self.hub
        (old_root / "graphify-out").mkdir()
        (old_root / "graphify-out/graph.json").write_text("{}", encoding="utf-8")
        old = {
            "schema_version": 1,
            "versions": [{
                "version": "v1.0.0", "state": "open", "opened_at": "2026-10-02T09:00:00+09:00",
                "note": "기존 기준선", "revisions": {name: [] for name in MODULE.COMPONENTS},
            }],
        }
        (old_root / "version-ledger.json").write_text(json.dumps(old), encoding="utf-8")
        result, changed = MODULE.record(self.project, "graphify", ["graphify-out/graph.json"], "기존 기록")
        self.assertTrue(changed)
        self.assertEqual(result["versions"][-1]["version"], "v1.0.0")
        self.assertIn("`graphify-out/graph.json`", (old_root / "VERSION.md").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            MODULE.init(self.project)


if __name__ == "__main__":
    unittest.main()
