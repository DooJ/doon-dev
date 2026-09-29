<p align="center">
  <img src="./assets/brand/doon-logo.svg" alt="DooN — DO:ON" width="720">
</p>

<p align="center"><strong>Understand the system. Change it with confidence.</strong></p>

<p align="center">
  <img src="./assets/brand/doon-hero.png" alt="DooN Development skill network" width="100%">
</p>

# DooN Development

**DooN Development**는 코드베이스 이해부터 구현, 리뷰, 오류 대응, 배포 관측까지 개발의 전체 흐름을 연결하는 공개 Codex·Claude Code 플러그인입니다. 플러그인 전체를 켜거나 끌 수 있으며, 설치 후 필요한 스킬만 개별적으로 활성화할 수 있습니다.

`DO:ON`의 두 코어는 개발자의 판단과 에이전트의 실행을 뜻합니다. 코드 변경은 분석에서 시작해 검증과 운영 관측으로 닫히며, 각 스킬은 이 흐름의 한 단계를 명확하게 담당합니다.

## 포함된 스킬

| 영역 | 스킬 |
|---|---|
| 개발 오케스트레이션 | `development-orchestrator`, `feature-analyzer` |
| 구현 품질 | `code-commenting`, `code-reviewer`, `error-responder` |
| 플랫폼 | `android-architecture`, `kotlin-basics` |
| 운영 연결 | `linear-qa`, `sentry-observability` |
| 스킬 품질 | `skill-inspector`, `skill-versioning` |

## 동작 방식

1. 요청에 맞는 스킬이 코드와 프로젝트 상태를 읽습니다.
2. 분석, 구현, 리뷰, 오류 대응을 서로 독립된 책임으로 수행합니다.
3. 테스트와 검증 결과를 Linear, Sentry, Git 이력과 연결합니다.
4. 스킬 변경은 `VERSION.md`에 버전과 출처를 남깁니다.

`skill-versioning`을 제외한 스킬은 Core 없이 동작합니다. `skill-versioning`은 DooN 원본·버전·출처 계약과 Core 검증 스크립트를 사용하는 `core-required` 관리 스킬입니다.

## 구조

- `.codex-plugin/plugin.json`: 플러그인 메타데이터와 `skills/` 등록
- `.claude-plugin/plugin.json`: Claude Code 네이티브 플러그인 메타데이터
- `skills/<이름>/`: 실제 스킬 원본, 버전, references, scripts, assets
- `catalog.json`: 저장소와 스킬 소유권을 확인하는 카탈로그
- `PLUGIN_VERSION.md`: 플러그인 단위 변경 이력과 출처

일부 스킬은 DooN의 공통 규칙, 워크플로우 또는 런타임을 참조합니다. 각 스킬의 구체적인 버전과 출처는 해당 폴더의 `VERSION.md`에서 확인할 수 있습니다.

> 이 저장소는 DooN Core 없이 독립 설치할 수 있으며 프로젝트에 `.doon`을 생성하지 않습니다. Core 사용자는 이 플러그인을 동일한 plugin ID로 통합 관리합니다.
