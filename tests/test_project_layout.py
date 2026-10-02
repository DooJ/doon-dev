"""범위별 Graphify 데이터를 보존하는 프로젝트 배치 검사."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/codegraph/scripts/project_layout.py"
SPEC = importlib.util.spec_from_file_location("project_layout", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProjectLayoutTest(unittest.TestCase):
    def test_prepare_creates_independent_named_scopes_without_switching_root_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = MODULE.prepare(root, scope="보이미 생태계")
            second = MODULE.prepare(root, scope="보이미 메뉴")
            self.assertTrue(first["scope_exists"])
            self.assertTrue(second["scope_exists"])
            self.assertTrue((root / "codebase-map/보이미 생태계").is_dir())
            self.assertTrue((root / "codebase-map/보이미 메뉴").is_dir())
            self.assertFalse((root / "graphify-out").exists())
            self.assertEqual(MODULE.status(root)["scopes"], [])
            MODULE.prepare(root, scope="보이미 생태계")

    def test_existing_legacy_graph_is_preserved_when_named_scope_is_prepared(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / "graphify-out"
            old.mkdir()
            (old / "graph.json").write_text("{}", encoding="utf-8")
            MODULE.prepare(root, scope="보이미 생태계")
            self.assertEqual((old / "graph.json").read_text(encoding="utf-8"), "{}")
            self.assertTrue((root / "codebase-map/보이미 생태계").is_dir())
            with self.assertRaises(ValueError):
                MODULE.prepare(root, scope="보이미 생태계", migrate_existing=True)

    def test_conflicting_scope_or_unsafe_name_is_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "codebase-map").mkdir()
            (root / "codebase-map/보이미 메뉴").write_text("owned", encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.prepare(root, scope="보이미 메뉴")
            self.assertEqual((root / "codebase-map/보이미 메뉴").read_text(encoding="utf-8"), "owned")
            for name in ("../escape", "v1.0.0", "graphify-out", "bad/name"):
                with self.assertRaises(ValueError):
                    MODULE.prepare(root, scope=name)

    def test_foreign_legacy_link_remains_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "graphify-out").symlink_to("elsewhere")
            MODULE.prepare(root, scope="보이미 메뉴")
            self.assertEqual((root / "graphify-out").readlink(), Path("elsewhere"))
            self.assertEqual(MODULE.status(root, "보이미 메뉴")["legacy_unscoped_exists"], False)

    def test_scope_folder_symlink_cannot_escape_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "codebase-map").mkdir()
            (root / "codebase-map/보이미 메뉴").symlink_to("../outside")
            with self.assertRaises(ValueError):
                MODULE.prepare(root, scope="보이미 메뉴")


if __name__ == "__main__":
    unittest.main()
