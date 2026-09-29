"""모든 에이전트 어댑터가 같은 플러그인 계약을 가리키는지 검증한다."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"


class CrossAgentContractTest(unittest.TestCase):
    def test_manifests_share_one_canonical_contract(self) -> None:
        portable = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        openai = portable["extensions"]["com.openai"]
        interface = openai["interface"]

        self.assertEqual(SCHEMA, portable["$schema"])
        for key in ("name", "version", "description", "author"):
            self.assertEqual(portable[key], codex[key])
            self.assertEqual(portable[key], claude[key])
        self.assertEqual(interface, codex["interface"])
        self.assertLessEqual(len(interface.get("defaultPrompt", [])), 3)
        self.assertNotIn("hooks", codex)
        if "hooks" in openai:
            self.assertTrue((ROOT / openai["hooks"]).is_file())

    def test_agent_marketplace_points_to_portable_plugin(self) -> None:
        portable = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        interface = portable["extensions"]["com.openai"]["interface"]
        marketplace = json.loads(
            (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(portable["name"], marketplace["name"])
        self.assertEqual(interface["displayName"], marketplace["interface"]["displayName"])
        self.assertEqual(1, len(marketplace["plugins"]))
        entry = marketplace["plugins"][0]
        self.assertEqual(portable["name"], entry["name"])
        self.assertEqual({"source": "local", "path": "."}, entry["source"])
        self.assertEqual(
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            entry["policy"],
        )
        self.assertEqual(interface["category"], entry["category"])


if __name__ == "__main__":
    unittest.main()
