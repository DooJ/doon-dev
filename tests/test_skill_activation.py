from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/skill_activation.py"
SPEC = importlib.util.spec_from_file_location("skill_activation", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SkillActivationTests(unittest.TestCase):
    def test_existing_other_marketplace_is_detected(self) -> None:
        plugin, _, _ = MODULE.catalog()
        codex_listing = {"installed": [{"pluginId": f"{plugin}@shared", "installed": True}]}
        claude_listing = [{"id": f"{plugin}@shared"}]
        with patch.object(MODULE.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps(codex_listing)
            self.assertEqual([f"{plugin}@shared"], MODULE.other_marketplace_installs("codex", plugin, plugin))
            self.assertEqual([], MODULE.other_marketplace_installs("codex", plugin, "shared"))
            run.return_value.stdout = json.dumps(claude_listing)
            self.assertEqual([f"{plugin}@shared"], MODULE.other_marketplace_installs("claude", plugin, plugin))

    def test_cli_keeps_child_choice_when_parent_toggles(self) -> None:
        plugin, names, parents = MODULE.catalog()
        if not parents:
            self.skipTest("no hierarchy")
        child, parent = next(iter(parents.items()))
        with tempfile.TemporaryDirectory() as temporary:
            env = {**os.environ, "XDG_CONFIG_HOME": temporary}

            def run(*args: str) -> dict:
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), *args, "--skip-codex", "--skip-claude"],
                    env=env, capture_output=True, text=True, check=True,
                )
                return json.loads(result.stdout)

            run("disable", child)
            state = run("disable", parent)
            self.assertIn(child, state["effective_disabled"])
            state = run("enable", parent)
            self.assertEqual([child], state["effective_disabled"])
            self.assertEqual([child], state["disabled_skills"])
            self.assertEqual(plugin, state["plugin"])

    def test_parent_off_cascades_and_child_choice_survives(self) -> None:
        plugin, names, parents = MODULE.catalog()
        self.assertTrue(plugin.startswith("doon-"))
        if not parents:
            self.assertEqual([names[0]], MODULE.effective_disabled(names, parents, {names[0]}))
            return
        child, parent = next(iter(parents.items()))
        self.assertIn(child, MODULE.effective_disabled(names, parents, {parent}))
        self.assertIn(parent, MODULE.effective_disabled(names, parents, {parent}))
        self.assertEqual([child], MODULE.effective_disabled(names, parents, {child}))
        self.assertIn(child, MODULE.effective_disabled(names, parents, {parent, child}))
        self.assertIn(child, MODULE.effective_disabled(names, parents, {child}))

    def test_codex_block_preserves_other_configuration(self) -> None:
        plugin, names, _ = MODULE.catalog()
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.toml"
            config.write_text('model = "gpt-6-sol"\n', encoding="utf-8")
            original = MODULE.codex_skill_paths
            MODULE.codex_skill_paths = lambda _plugin, _disabled: [MODULE.ROOT / "skills" / names[0]] if _disabled else []
            try:
                self.assertTrue(MODULE.apply_codex(plugin, [names[0]], config))
                self.assertIn("enabled = false", config.read_text(encoding="utf-8"))
                self.assertTrue(MODULE.apply_codex(plugin, [], config))
                self.assertEqual('model = "gpt-6-sol"\n', config.read_text(encoding="utf-8"))
            finally:
                MODULE.codex_skill_paths = original

    def test_codex_paths_include_source_and_installed_cache(self) -> None:
        plugin, names, _ = MODULE.catalog()
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {"CODEX_HOME": temporary}):
            cached = Path(temporary) / "plugins/cache/independent" / plugin / "1.0.0/skills" / names[0]
            cached.mkdir(parents=True)
            (cached / "SKILL.md").write_text("---\nname: test\n---\n", encoding="utf-8")
            paths = MODULE.codex_skill_paths(plugin, [names[0]])
            self.assertIn((MODULE.ROOT / "skills" / names[0]).resolve(), paths)
            self.assertIn(cached.resolve(), paths)

    def test_claude_denies_only_managed_skill_rules(self) -> None:
        plugin, names, _ = MODULE.catalog()
        with tempfile.TemporaryDirectory() as temporary:
            settings = Path(temporary) / "settings.json"
            settings.write_text(json.dumps({"permissions": {"deny": ["Bash(rm *)"]}}), encoding="utf-8")
            state = {"managed_claude_denies": []}
            self.assertTrue(MODULE.apply_claude(plugin, [names[0]], state, settings))
            denied = json.loads(settings.read_text(encoding="utf-8"))["permissions"]["deny"]
            self.assertIn(f"Skill({plugin}:{names[0]})", denied)
            self.assertTrue(MODULE.apply_claude(plugin, [], state, settings))
            self.assertEqual(["Bash(rm *)"], json.loads(settings.read_text(encoding="utf-8"))["permissions"]["deny"])


if __name__ == "__main__":
    unittest.main()
