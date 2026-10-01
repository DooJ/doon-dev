# DooN Development 플러그인 운영 안내

최종 확인: 2026-10-01 · 대상 버전: 5.0.0

이 문서는 개발 스킬의 역할과 사용 경계를 설명합니다. 최초 설치 명령과 전체 스킬 목록은 [저장소 README](../README.md)에 있습니다. 설치 시 17개 스킬이 모두 포함되며, 이후 필요하지 않은 스킬만 사용 중지할 수 있습니다.

## 스킬 구성

| 묶음 | 스킬 | 언제 쓰는가 |
|---|---|---|
| 개발 루프 | `development-orchestrator`, `feature-analyzer`, `error-responder`, `code-reviewer`, `deprecation-migration` | 복합 개발, 기존 기능 파악, 오류·변경 검토 또는 단계적 전환이 필요할 때 |
| 코드 가이드 | `code-commenting`, `android-architecture`, `kotlin-basics`, `interface-contract` | 주석·언어 관례 또는 공개 경계의 소비자 계약이 필요할 때 |
| 코드베이스 지식 맵 | `codegraph` | Graphify·Archify 원본 배포와 프로젝트별 그래프·다이어그램·Obsidian 볼트를 관리할 때 |
| 운영·품질 | `linear-qa`, `sentry-observability`, `runtime-observability`, `performance-diagnostics`, `quality-constraints` | QA·릴리스 관측, 운영 계측, 성능 진단 또는 큰 작업의 품질 기준선이 필요할 때 |
| 스킬 품질 | `skill-inspector`, `dev-skill-versioning` | 외부 스킬 설치 전 위험 검토 또는 이 저장소의 스킬 수정·배포 점검 |

이 묶음은 탐색을 위한 분류이지 일괄 활성화 스위치가 아닙니다. 각 스킬은 독립적으로 선택합니다. `development-orchestrator`를 사용해도 다른 스킬을 무조건 실행하지 않고, 필요한 역할과 접근 가능한 도구를 확인해 연결합니다.

## 대표 작업 흐름

- 새 기능: `feature-analyzer`로 기존 진입점·상태·데이터 흐름을 확인한 뒤 구현합니다. 다영역 작업이면 `development-orchestrator`로 경계를 정하고, 마지막에 `code-reviewer`로 변경과 테스트 누락을 검토합니다.
- 공개 인터페이스와 교체: `interface-contract`로 소비자·호환성·오류를 정하고, 옛 경로를 없애야 할 때만 `deprecation-migration`으로 전환 단계를 관리합니다.
- 품질과 성능: 큰 작업에서만 `quality-constraints`로 기존 검사 기준선을 정합니다. 성능 문제는 `performance-diagnostics`로 변경 전후를 같은 조건에서 측정합니다.
- 운영 계측: 진단 신호가 부족하면 `runtime-observability`로 최소 계측을 정합니다. Sentry 릴리스 사건 운영은 `sentry-observability`가 맡습니다.
- 장애: `error-responder`로 재현·로그·원인 가설을 분리합니다. 수정은 사용자의 변경 요청 범위에 맞춰 진행하고, 필요하면 Sentry 관측을 통해 실제 재발 여부를 확인합니다.
- 문서·스타일: `code-commenting`은 주석이 필요한 계약에만 적용합니다. Android/Kotlin 가이드는 해당 기술을 쓰는 코드에서만 적용합니다.
- 코드베이스 지식 맵: `codegraph`는 외부 원본 스킬과 에이전트 설치 상태를 구분하고, 각 프로젝트의 생성물을 `codebase-map/`에 모읍니다. Graphify 작업 폴더는 호환 링크를 준비한 뒤 생성하며 실행 후 옮기지 않습니다.
- 외부 연계: `linear-qa`와 `sentry-observability`는 각각 서비스 접근 권한과 프로젝트 구성이 있어야 실제 읽기·쓰기 동작을 합니다. 연결이 없으면 확인된 코드·테스트·로그 범위만 보고하고, 외부 상태를 추정하지 않습니다.

꺼진 스킬은 단순히 사용하지 않습니다. 필요 목적을 수행할 수 있는 다른 활성 스킬이나 일반 도구가 있으면 그 경로를 선택하되, 특정 스킬이 실행된 것처럼 표시하지 않습니다.

## 설치·사용 설정·복구

저장소 루트에서 `bash scripts/plugin.sh install`을 실행하면 감지된 Codex·Claude Code·Antigravity에 맞게 설치합니다. `setup`은 설정 재적용, `repair`는 현재 파일을 기준으로 복구, `update`는 Git 최신화 후 재설정, `test`는 패키지·버전·테스트 검증, `status`는 상태 확인입니다. 설치되지 않은 에이전트는 건너뜁니다.

```bash
bash scripts/plugin.sh skills status
bash scripts/plugin.sh skills disable code-reviewer
bash scripts/plugin.sh skills enable code-reviewer
bash scripts/plugin.sh test
```

사용 중지 선택은 설치 삭제가 아니며 Codex·Claude의 새 세션에서 적용됩니다. Antigravity의 스킬별 차단은 아직 검증되지 않았습니다. Antigravity의 플러그인 단위 켜기·끄기와 구별해야 합니다.

## 원본·갱신 기준

스킬 원본은 `skills/*/SKILL.md`, 동작 분류는 `catalog.json`, 배포 형식은 `plugin.json`·`.claude-plugin/`·`antigravity/`, 설치 동작은 `scripts/plugin.sh`가 소유합니다. 스킬을 바꿀 때는 `dev-skill-versioning`의 버전·출처·검증 계약을 따릅니다. 스킬 추가·제거, 분류, 외부 서비스 요구, 에이전트 지원 또는 설치 명령이 바뀌면 이 문서를 갱신합니다. 이 문서는 실제 Linear/Sentry 계정 연결이나 대상 프로젝트의 테스트 성공을 보증하지 않습니다.
