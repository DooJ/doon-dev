"""Graphify 작업 데이터를 보존하는 프로젝트 배치 검사."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/codebase-knowledge-stack-manager/scripts/project_layout.py"
SPEC = importlib.util.spec_from_file_location("project_layout", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProjectLayoutTest(unittest.TestCase):
    def test_prepare_creates_one_data_folder_and_relative_compatibility_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = MODULE.prepare(root, migrate_existing=False)
            self.assertEqual(result["root_graphify_out"], "managed")
            self.assertEqual((root / "graphify-out").readlink(), Path("codebase-map/graphify-out"))
            self.assertTrue((root / "codebase-map/archify").is_dir())
            self.assertTrue((root / "codebase-map/vault").is_dir())
            MODULE.prepare(root, migrate_existing=False)

    def test_existing_graph_requires_explicit_migration_and_keeps_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / "graphify-out"
            old.mkdir()
            (old / "graph.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.prepare(root, migrate_existing=False)
            self.assertEqual((old / "graph.json").read_text(encoding="utf-8"), "{}")
            MODULE.prepare(root, migrate_existing=True)
            self.assertEqual((root / "codebase-map/graphify-out/graph.json").read_text(encoding="utf-8"), "{}")

    def test_conflicting_destination_or_foreign_link_is_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "graphify-out").mkdir()
            (root / "codebase-map/graphify-out").mkdir(parents=True)
            with self.assertRaises(ValueError):
                MODULE.prepare(root, migrate_existing=True)
            self.assertTrue((root / "graphify-out").is_dir())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "graphify-out").symlink_to("elsewhere")
            with self.assertRaises(ValueError):
                MODULE.prepare(root, migrate_existing=False)
            self.assertEqual((root / "graphify-out").readlink(), Path("elsewhere"))

    def test_data_folder_symlink_cannot_escape_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "codebase-map").mkdir()
            (root / "codebase-map/graphify-out").symlink_to("../outside")
            with self.assertRaises(ValueError):
                MODULE.prepare(root, migrate_existing=False)


if __name__ == "__main__":
    unittest.main()
