"""통합 플러그인 관리 명령을 검증한다."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANAGER = ROOT / "scripts/plugin.sh"


class PluginManagerTest(unittest.TestCase):
    def run_manager(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["bash", str(MANAGER), *arguments], cwd=ROOT, capture_output=True, text=True, timeout=30)

    def test_help_exposes_lifecycle_and_agent_choices(self) -> None:
        completed = self.run_manager("--help")
        self.assertEqual(0, completed.returncode, completed.stderr)
        for command in ("install", "setup", "update", "repair", "test", "status"):
            self.assertIn(command, completed.stdout)
        for agent in ("Codex", "Claude Code", "Antigravity"):
            self.assertIn(agent, completed.stdout)

    def test_status_is_read_only_and_identifies_plugin(self) -> None:
        completed = self.run_manager("status")
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("doon-dev", completed.stdout)

    def test_install_detects_and_configures_all_available_agents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_bin = Path(temporary) / "bin"
            fake_bin.mkdir()
            log = Path(temporary) / "commands.log"
            for command in ("codex", "claude", "agy"):
                path = fake_bin / command
                path.write_text(f"#!/bin/sh\nprintf '{command}' >> \"$PLUGIN_MANAGER_LOG\"\nfor arg in \"$@\"; do printf ' <%s>' \"$arg\" >> \"$PLUGIN_MANAGER_LOG\"; done\nprintf '\\n' >> \"$PLUGIN_MANAGER_LOG\"\nif [ \"$1\" = plugin ] && [ \"$2\" = list ]; then printf '[]\\n'; fi\n", encoding="utf-8")
                path.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
            env["PLUGIN_MANAGER_LOG"] = str(log)
            env["XDG_CONFIG_HOME"] = str(Path(temporary) / "config")
            env["CODEX_HOME"] = str(Path(temporary) / "codex-home")
            completed = subprocess.run(["bash", str(MANAGER), "install"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, completed.returncode, completed.stderr)
            commands = log.read_text(encoding="utf-8")
            self.assertIn("codex <plugin> <marketplace> <add>", commands)
            self.assertIn("claude <plugin> <install>", commands)
            self.assertIn("agy <plugin> <install>", commands)


if __name__ == "__main__":
    unittest.main()
