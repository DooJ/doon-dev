# 코드 역기획 리빙독 브리지
`feature-analyzer` 분석 결과를 `living-doc-writer`가 갱신할 상시 문서로 넘길 때 사용한다.

## 원칙
- 분석 결과 자체는 코드 근거가 있는 사실과 추론을 분리한다.
- 리빙독에는 현재 프로젝트의 최신 기준으로 믿을 수 있는 사실만 반영한다.
- 코드에 없는 제품 의도, 정책, 사용자 니즈는 `추론` 또는 `사용자 확인 필요`로 둔다.
- 기능 분석 원문을 문서에 그대로 복사하지 말고, 문서 목적에 맞게 압축한다.

## 기능 역기획 -> 리빙독 매핑
| 분석 결과 | 갱신 후보 문서 |
|---|---|
| 기능 목적과 사용자 행동 | `docs/planning/requirements.md`, `docs/planning/user-scenarios.md` |
| 화면 상태와 전환 | `docs/planning/screen-spec.md` |
| API request/response, 에러 | `docs/interfaces/api-spec.md` |
| 엔티티, 저장소, 상태값 | `docs/data/data-model.md`, `docs/data/data-dictionary.md` |
| 레이어, 모듈, 데이터 흐름 | `docs/architecture/technical-design.md`, `docs/onboarding/code-map.md` |
| 실패 흐름, 권한, 경계 조건 | `docs/qa/qa-checklist.md`, `docs/qa/regression-matrix.md` |
| 배치, 배포, 운영 단서 | `docs/operations/runbook.md`, `docs/operations/monitoring.md` |

## 프로젝트 전체 역기획 -> 리빙독 기본 세트
| 순서 | 문서 | 목적 |
|---|---|---|
| 1 | `docs/onboarding/project-overview.md` | 코드에서 확인한 프로젝트 목적과 주요 기능을 설명한다. |
| 2 | `docs/onboarding/code-map.md` | 모듈, 진입점, 데이터 흐름, 변경 포인트를 정리한다. |
| 3 | `docs/planning/feature-catalog.md` | 코드에서 확인한 기능군과 기능별 상태를 목록화한다. |
| 4 | `docs/project/current-status.md` | 구현되어 있는 것, 확인 필요한 것, 문서 갭을 정리한다. |
| 5 | `docs/planning/requirements.md` | 코드에서 복원한 현재 기능 요구사항과 예외를 정리한다. |
| 6 | `docs/planning/screen-spec.md` | 실제 화면과 상태를 기준으로 화면 명세를 정리한다. |
| 7 | `docs/architecture/technical-design.md` | 현재 아키텍처와 모듈 책임을 설명한다. |
| 8 | `docs/data/data-model.md` | 실제 엔티티, 저장소, 상태값을 정리한다. |
| 9 | `docs/interfaces/api-spec.md` | 실제 API, 메시지, 외부 연동을 정리한다. |
| 10 | `docs/qa/test-strategy.md` | 현재 테스트 단서와 누락된 검증 범위를 정리한다. |

## living-doc-writer 입력 패킷
```yaml
source_type: "code_reverse_engineering"
analysis_scope: "feature|project|onboarding|documentation"
source_project_root: "<project-root>"
analysis_target: "<feature-or-project>"
evidence:
  - file: "<path>"
    reason: "<why this file proves the behavior>"
confirmed_facts:
  - "<code-supported fact>"
inferences:
  - "<weak or product-intent inference>"
target_living_docs:
  - "docs/onboarding/code-map.md"
  - "docs/planning/requirements.md"
do_not_promote:
  - "<items that require user/product confirmation>"
```

## 완료 기준
- 각 문서 후보에 코드 근거가 연결되어 있다.
- 사용자가 전체 프로젝트 분석을 요청했으면 기능 하나만 깊게 파고들고 끝내지 않는다.
- 사용자가 특정 기능 분석을 요청했으면 프로젝트 전체 리빙독 세트를 불필요하게 만들지 않는다.
- 리빙독 반영 후보에는 `반영할 사실`, `추론`, `사용자 확인 필요`가 분리되어 있다.
