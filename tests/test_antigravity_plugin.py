"""Antigravity 플러그인 패키징 계약을 검증한다."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts/build_antigravity_plugin.py"


class AntigravityPluginTest(unittest.TestCase):
    def test_builds_installable_package_with_all_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            for _ in range(2):
                completed = subprocess.run(
                    ["python3", str(BUILD), "--output", temporary], capture_output=True, text=True, check=True
                )
            package = Path(completed.stdout.strip())
            manifest = json.loads((package / "plugin.json").read_text(encoding="utf-8"))
            self.assertEqual({"$schema", "name", "description"}, set(manifest))
            self.assertEqual("doon-dev", manifest["name"])
            expected = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
            actual = {path.parent.name for path in (package / "skills").glob("*/SKILL.md")}
            self.assertEqual(expected, actual)
            self.assertTrue((package / ".doon-antigravity-package").is_file())


if __name__ == "__main__":
    unittest.main()
