import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/codegraph/scripts/check_multi_vault.py"
SPEC = importlib.util.spec_from_file_location("check_multi_vault", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MultiVaultCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.version = Path(self.temp.name) / "scope/v1.0.0"
        data = self.version / "data"
        data.mkdir(parents=True)
        capabilities = data / "capability-map.json"
        capabilities.write_text(json.dumps({"projects": [{"id": "client"}, {"id": "server"}]}))
        (data / "catalog.json").write_text(json.dumps({
            "schema_version": 1,
            "sources": {"capabilities": {"path": "capability-map.json", "sha256": sha(capabilities)}},
            "vault_registry": "../vaults/registry.json", "counts": {"solutions": 2},
        }))
        vaults = [
            {"id": "system", "kind": "hub", "path": "vaults/system", "vault_name": "system", "home": "00_HOME.md"},
            {"id": "client", "kind": "solution", "path": "vaults/client", "vault_name": "client", "home": "00_HOME.md"},
            {"id": "server", "kind": "solution", "path": "vaults/server", "vault_name": "server", "home": "00_HOME.md"},
        ]
        root = self.version / "vaults"
        root.mkdir()
        (root / "registry.json").write_text(json.dumps({"vaults": vaults}))
        for name in ("system", "client", "server"):
            vault = root / name
            (vault / ".obsidian").mkdir(parents=True)
            (vault / "00_HOME.md").write_text("[[DETAIL]]\n")
            (vault / "DETAIL.md").write_text("# Detail\n")
        self.refresh_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def refresh_manifest(self):
        files = sorted(self.version.glob("vaults/*/*.md"))
        (self.version / "generation-manifest.json").write_text(json.dumps({
            "inputs": {"capabilities": sha(self.version / "data/capability-map.json")},
            "generated": [{"path": str(p.relative_to(self.version)), "sha256": sha(p)} for p in files],
        }))

    def test_valid_independent_vaults(self):
        self.assertEqual(module.check(self.version)["vaults"], 3)

    def test_broken_internal_link_fails_after_manifest_update(self):
        (self.version / "vaults/client/00_HOME.md").write_text("[[MISSING]]\n")
        self.refresh_manifest()
        with self.assertRaisesRegex(module.VaultError, "내부 링크"):
            module.check(self.version)

    def test_hash_only_generated_note_name_fails(self):
        vault = self.version / "vaults/client"
        (vault / "00_HOME.md").write_text("[[DETAIL]]\n[[3fe5a3b3e624]]\n")
        (vault / "3fe5a3b3e624.md").write_text("# POST /lite/displayOff.do\n")
        self.refresh_manifest()
        with self.assertRaisesRegex(module.VaultError, "해시 전용 생성 노트명"):
            module.check(self.version)

    def test_edited_generated_file_fails(self):
        (self.version / "vaults/client/DETAIL.md").write_text("사용자 편집\n")
        with self.assertRaisesRegex(module.VaultError, "지문 불일치"):
            module.check(self.version)

    def test_missing_solution_vault_fails(self):
        registry = self.version / "vaults/registry.json"
        value = json.loads(registry.read_text())
        value["vaults"] = [x for x in value["vaults"] if x["id"] != "server"]
        registry.write_text(json.dumps(value))
        with self.assertRaisesRegex(module.VaultError, "솔루션 볼트"):
            module.check(self.version)

    def test_cross_vault_uri_fails_for_missing_target(self):
        (self.version / "vaults/client/DETAIL.md").write_text("[서버](obsidian://open?vault=server&file=NOPE.md)\n")
        self.refresh_manifest()
        with self.assertRaisesRegex(module.VaultError, "이동 대상"):
            module.check(self.version)


if __name__ == "__main__":
    unittest.main()
