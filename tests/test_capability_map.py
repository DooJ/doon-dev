import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/codegraph/scripts/capability_map.py"
SPEC = importlib.util.spec_from_file_location("capability_map", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class CapabilityMapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "client.py").write_text("def refresh_schedule(): pass\n")
        (self.root / "server.py").write_text("def get_schedule(): pass\n")
        self.data = {
            "schema_version": 1,
            "scope": "테스트 생태계",
            "version": "v1.0.0",
            "requested_projects": ["client", "server"],
            "projects": [
                {
                    "id": "client", "name": "장비 앱",
                    "role": "서버 일정을 받아 장비 화면에 콘텐츠를 재생한다",
                    "capabilities": [{
                        "id": "playback", "name": "일정 재생",
                        "description": "일정 응답을 해석해서 장비 화면의 재생 대상을 변경한다",
                        "evidence": [{"path": "client.py", "locator": "refresh_schedule", "basis": "source"}],
                    }], "unknowns": ["실제 장비 연결 성공 여부"],
                },
                {
                    "id": "server", "name": "웹서버",
                    "role": "장비별 재생 일정을 API 응답으로 제공한다",
                    "capabilities": [{
                        "id": "schedule", "name": "일정 제공",
                        "description": "장비 식별자를 받아 재생 일정을 응답으로 제공한다",
                        "evidence": [{"path": "server.py", "locator": "get_schedule", "basis": "source"}],
                    }], "unknowns": ["운영 데이터의 실제 값"],
                },
            ],
            "relations": [{
                "id": "schedule-sync", "function": "장비 일정 동기화",
                "kind": "cooperation", "status": "static_confirmed",
                "participants": [
                    {"project": "server", "responsibility": "장비별 일정 조회 응답을 제공한다", "evidence": [{"path": "server.py", "locator": "get_schedule", "basis": "source"}]},
                    {"project": "client", "responsibility": "일정을 요청하고 재생 상태에 반영한다", "evidence": [{"path": "client.py", "locator": "refresh_schedule", "basis": "source"}]},
                ],
                "contract": "장비 ID를 사용한 일정 HTTP 요청과 응답",
                "result": "서버 일정에 따라 장비 재생 대상이 바뀐다",
                "unknowns": ["운영 서버 전달 성공은 미확인"],
            }],
        }

    def tearDown(self):
        self.temporary.cleanup()

    def test_valid_input_renders_reusable_project_notes(self):
        module.validate(self.data, self.root, ["client", "server"])
        documents = module.render_documents(self.data)
        self.assertEqual(len(documents), 4)
        vault = self.root / "v1.0.0/vault"
        module.write_documents(vault, documents, "테스트 생태계", "v1.0.0", None)
        self.assertIn("[[10_Projects/server|웹서버]]", (vault / "10_Projects/client.md").read_text())
        self.assertIn("장비 일정 동기화", (vault / "03_FUNCTION_RELATIONS.md").read_text())
        self.assertTrue((vault / module.MANIFEST_NAME).exists())
        module.write_documents(vault, documents, "테스트 생태계", "v1.0.0", None)

    def test_requested_project_list_is_checked_independently(self):
        with self.assertRaisesRegex(module.MapError, "요청 범위 불일치"):
            module.validate(self.data, self.root, ["client", "other"])

    def test_unsafe_note_name_is_rejected(self):
        self.data["projects"][0]["note"] = "../outside"
        with self.assertRaisesRegex(module.MapError, "안전한 노트 파일명"):
            module.validate(self.data, self.root, ["client", "server"])

    def test_missing_evidence_file_and_relation_are_rejected(self):
        self.data["projects"][0]["capabilities"][0]["evidence"][0]["path"] = "missing.py"
        with self.assertRaisesRegex(module.MapError, "파일을 찾을 수 없습니다"):
            module.validate(self.data, self.root, ["client", "server"])
        self.data["projects"][0]["capabilities"][0]["evidence"][0]["path"] = "client.py"
        self.data["relations"] = []
        with self.assertRaisesRegex(module.MapError, "relations"):
            module.validate(self.data, self.root, ["client", "server"])

    def test_duplicate_claim_needs_comparison(self):
        self.data["relations"][0]["kind"] = "duplicate_implementation"
        with self.assertRaisesRegex(module.MapError, "comparison"):
            module.validate(self.data, self.root, ["client", "server"])

    def test_manual_edit_and_unexplained_shrink_are_rejected(self):
        documents = module.render_documents(self.data)
        vault = self.root / "v1.0.0/vault"
        module.write_documents(vault, documents, "테스트 생태계", "v1.0.0", None)
        path = vault / "10_Projects/client.md"
        path.write_text(path.read_text() + "사용자 추가 메모\n")
        with self.assertRaisesRegex(module.MapError, "사용자가 수정"):
            module.write_documents(vault, documents, "테스트 생태계", "v1.0.0", None)
        path.write_text(documents["10_Projects/client.md"])
        shorter = dict(documents)
        shorter["10_Projects/client.md"] = "# 장비 앱\n"
        with self.assertRaisesRegex(module.MapError, "짧아졌습니다"):
            module.write_documents(vault, shorter, "테스트 생태계", "v1.0.0", None)
        removed = dict(documents)
        del removed["10_Projects/client.md"]
        with self.assertRaisesRegex(module.MapError, "기존 생성 노트"):
            module.write_documents(vault, removed, "테스트 생태계", "v1.0.0", None)

    def test_legacy_manifest_can_be_adopted_without_erasing_other_files(self):
        documents = module.render_documents(self.data)
        vault = self.root / "v1.0.0/vault"
        vault.mkdir(parents=True)
        legacy = vault / module.LEGACY_MANIFEST_NAME
        legacy.parent.mkdir(parents=True)
        path = vault / "02_PROJECT_CAPABILITIES.md"
        path.write_text(documents["02_PROJECT_CAPABILITIES.md"])
        (vault / "00_HOME.md").write_text("사용자 시작 문서\n")
        legacy.write_text(json.dumps({"files": [{"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]}))
        module.write_documents(vault, documents, "테스트 생태계", "v1.0.0", None)
        self.assertEqual((vault / "00_HOME.md").read_text(), "사용자 시작 문서\n")
        self.assertEqual(len(json.loads(legacy.read_text())["files"]), 4)

    def test_completion_check_requires_home_and_overview_coverage(self):
        documents = module.render_documents(self.data)
        version = self.root / "v1.0.0"
        vault = version / "vault"
        module.write_documents(vault, documents, "테스트 생태계", "v1.0.0", None)
        home = vault / "00_HOME.md"
        home.write_text("[[02_PROJECT_CAPABILITIES]] → [[03_FUNCTION_RELATIONS]]\n")
        (vault / "01_SYSTEM_MAP.md").write_text("# 시스템 지도\n")
        (version / "graphify-out/graph.json").parent.mkdir(parents=True)
        (version / "graphify-out/graph.json").write_text('{"nodes": [], "links": []}')
        diagram = version / "archify/overview/index.html"
        diagram.parent.mkdir(parents=True)
        diagram.write_text("<html></html>")
        overview = version / "graphify-out/overview/graph.json"
        overview.parent.mkdir(parents=True)
        overview.write_text(json.dumps({"nodes": [{"id": "client"}, {"id": "server"}], "links": []}))
        module.check_vault(self.data, version, vault, documents)
        overview.write_text(json.dumps({"nodes": [{"id": "client"}], "links": []}))
        with self.assertRaisesRegex(module.MapError, "요청 프로젝트가 빠졌습니다"):
            module.check_vault(self.data, version, vault, documents)
        overview.write_text(json.dumps({"nodes": [{"id": "client"}, {"id": "server"}], "links": []}))
        home.write_text("[[02_PROJECT_CAPABILITIES]]\n")
        with self.assertRaisesRegex(module.MapError, "관계 지도로 이동"):
            module.check_vault(self.data, version, vault, documents)


if __name__ == "__main__":
    unittest.main()
