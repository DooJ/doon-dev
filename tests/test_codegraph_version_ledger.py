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
        self.root = self.project / "codebase-map"
        self.root.mkdir()
        (self.root / "graphify-out").mkdir()
        (self.root / "graphify-out/graph.json").write_text('{"version":1}', encoding="utf-8")

    def test_component_runs_accumulate_without_bumping_overall_version(self) -> None:
        MODULE.init(self.project)
        first, changed = MODULE.record(self.project, "graphify", ["graphify-out/graph.json"], "첫 그래프")
        self.assertTrue(changed)
        self.assertEqual(first["versions"][-1]["version"], "v1.0.0")
        (self.root / "graphify-out/graph.json").write_text('{"version":2}', encoding="utf-8")
        second, changed = MODULE.record(self.project, "graphify", ["graphify-out/graph.json"], "그래프 보강")
        self.assertTrue(changed)
        self.assertEqual(len(second["versions"][-1]["revisions"]["graphify"]), 2)
        self.assertIn("+", second["versions"][-1]["revisions"]["graphify"][0]["at"])
        self.assertEqual(second["versions"][-1]["version"], "v1.0.0")
        _, changed = MODULE.record(self.project, "graphify", ["graphify-out/graph.json"], "같은 결과")
        self.assertFalse(changed)
        self.assertEqual(len(MODULE.load(self.root)["versions"][-1]["revisions"]["graphify"]), 2)

    def test_reclassifies_only_open_version_and_keeps_prior_history(self) -> None:
        MODULE.init(self.project)
        MODULE.record(self.project, "graphify", ["graphify-out/graph.json"], "기준선")
        MODULE.bump(self.project, "patch", "전체 지도 보강")
        (self.root / "archify").mkdir()
        (self.root / "archify/diagram.json").write_text("{}", encoding="utf-8")
        MODULE.record(self.project, "archify", ["archify/diagram.json"], "구조도 추가")
        result = MODULE.reclassify(self.project, "minor", "핵심 흐름 확장")
        self.assertEqual([item["version"] for item in result["versions"]], ["v1.0.0", "v1.1.0"])
        self.assertEqual(result["versions"][0]["state"], "closed")
        self.assertEqual(len(result["versions"][1]["revisions"]["archify"]), 1)
        summary = (self.root / "VERSION.md").read_text(encoding="utf-8")
        self.assertIn("이전 결과 승계: v1.0.0", summary)
        self.assertIn("현재 버전: `v1.1.0`", summary)

    def test_rejects_unsafe_paths_and_preserves_existing_ledger(self) -> None:
        MODULE.init(self.project)
        with self.assertRaises(ValueError):
            MODULE.init(self.project)
        for path in ("../outside", "/tmp/outside"):
            with self.assertRaises(ValueError):
                MODULE.record(self.project, "graphify", [path], "잘못된 경로")
        (self.root / "linked").symlink_to(self.root / "graphify-out", target_is_directory=True)
        with self.assertRaises(ValueError):
            MODULE.record(self.project, "graphify", ["linked/graph.json"], "링크 경유")
        self.assertEqual(len(MODULE.load(self.root)["versions"][-1]["revisions"]["graphify"]), 0)


if __name__ == "__main__":
    unittest.main()
