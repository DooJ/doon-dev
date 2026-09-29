from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class SkillRelationTests(unittest.TestCase):
    def read_skill(self, name: str) -> str:
        return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")

    def test_design_build_has_capability_fallbacks(self) -> None:
        skill = self.read_skill("development-orchestrator")
        for capability in (
            "design.concept-direction",
            "design.screen-handoff",
            "design.system-governance",
            "content.ux-copy",
        ):
            with self.subTest(capability=capability):
                self.assertIn(f"`{capability}`", skill)
        self.assertIn("provider_mode: preferred|equivalent|inline|handoff", skill)

    def test_document_links_do_not_silently_fallback_to_markdown(self) -> None:
        analyzer = self.read_skill("feature-analyzer")
        self.assertIn("`document.living-current-state`", analyzer)
        self.assertIn("`living_doc_handoff`", analyzer)
        self.assertIn("단순 Markdown 생성", analyzer)

        sentry = self.read_skill("sentry-observability")
        self.assertIn("`document.snapshot-report`", sentry)
        self.assertIn("`snapshot_report_handoff`", sentry)
        self.assertIn("일반 Markdown 파일로 조용히 대체하지 않는다", sentry)


if __name__ == "__main__":
    unittest.main()
