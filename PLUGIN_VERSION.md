# DooN Development 플러그인 버전

현재 버전: `v3.0.0`

## 출처

| ID | 분류 | 자료 | 반영 범위 |
|---|---|---|---|
| `P1` | 자체 생성 | 2026-09-23 사용자 요청과 기존 스킬 저장소 | 저장소별 플러그인 그룹과 기존 독립 스킬 구성 |
| `P2` | 외부 참고 | [OpenAI 플러그인 패키징 문서](https://developers.openai.com/plugins/build/plugins), 2026-09-23 조회 | `.codex-plugin/plugin.json`, `skills/` 패키징과 마켓플레이스 호환 구조 |
| `P3` | 자체 생성 | 2026-09-23 사용자 요청 | 스킬 버전 관리에서 전역 AGENTIC_ROOT를 사용하는 경로 기준 |
| `P4` | 자체 생성 | 2026-09-23 사용자 요청 | DooN 브랜드, DO:ON 로고와 개발 플러그인 README 구성 |
| `P5` | 자체 생성 | 2026-09-24 사용자 승인 DooN 기술 이름 전환 | plugin ID, 저장소와 core source 식별자의 DooN 전환 |

| `P6` | 자체 생성 | 2026-09-24 사용자 승인 DooN 기술 이름 전환 | 플러그인 사용자 노출명과 기본 프롬프트를 DooN으로 통일 |

| `P7` | 자체 생성 | 2026-09-28 사용자 요청 | canonical 내부 폴더를 `.doon`으로 전환하고 이전 경로 폴백을 제거 |
| `P8` | 외부 참고 | [Claude Code 플러그인 문서](https://code.claude.com/docs/en/plugins), 2026-09-28 조회 | `.claude-plugin/plugin.json`, `skills/` 기반 Claude 네이티브 패키징 |

## 버전 이력

| 버전 | 날짜 | 변경 요약 | 출처 ID |
|---|---|---|---|
| `v3.0.0` | 2026-09-28 | canonical 내부 경로를 `.doon`으로 전환하고 Claude Code 네이티브 플러그인 manifest를 추가했다. | `P7`, `P8` |
| `v2.0.1` | 2026-09-24 | 플러그인 설명과 포함 스킬의 사용자 노출 제품명을 DooN으로 통일했다. | `P6` |
| `v2.0.0` | 2026-09-24 | plugin ID와 저장소 식별자를 `doon-dev`와 `DooJ/doon-core` 체계로 전환했다. 기존 설치와 구분되는 breaking 변경이다. | `P5` |
| `v1.0.2` | 2026-09-23 | 사용자 표시명을 DooN Development로 바꾸고 DO:ON 로고, 상징 이미지, 역할 중심 README를 추가했다. 기술 plugin ID와 저장소명은 유지했다. | `P4` |
| `v1.0.1` | 2026-09-23 | skill-versioning이 플러그인 공용 전역 AGENTIC_ROOT를 기준으로 원본 위치를 찾도록 문서를 보정했다. | `P3` |
| `v1.0.0` | 2026-09-23 | 기존 스킬 모음을 하나의 설치·활성화 단위로 묶고 내부 스킬을 개별적으로 노출하는 플러그인 구조를 처음 등록했다. | `P1`, `P2` |
