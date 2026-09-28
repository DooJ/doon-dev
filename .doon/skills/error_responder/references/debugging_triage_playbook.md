# Debugging Triage Playbook

크래시, 빌드 실패, 테스트 실패, 런타임 오류, 배포 후 장애를 빠르게 좁히기 위한 triage 절차다. 로그가 길거나 원인 후보가 여러 개이거나 수정까지 이어지는 장애 대응에서 읽는다.

## 1. 실패 유형 분류

| 유형 | 첫 확인 |
|---|---|
| Build | 실패 task, compiler error, dependency/plugin/version change |
| Test | 첫 실패 테스트, expected/actual, seed/time/order 의존성 |
| Runtime | exception type, first app frame, user action, device/env |
| Integration | upstream/downstream status, request/response, timeout, auth |
| Deploy | release version, rollout %, config/env, migration, feature flag |

## 2. 로그 압축 순서

1. 가장 이른 실패 시각을 찾는다.
2. `FATAL`, `Exception`, `Caused by`, exit code, failed assertion을 찾는다.
3. 외부 프레임보다 코드베이스 내부 첫 실패 프레임을 우선한다.
4. 같은 에러가 반복되면 첫 발생과 마지막 발생만 비교한다.
5. 직전 변경사항, 설정 변경, 데이터 변경, 배포 버전을 연결한다.

## 3. 원인 후보 분리

| 후보 | 확인 방법 |
|---|---|
| 입력 데이터 문제 | 실패 입력, null/empty/invalid, 특정 계정/권한 |
| 상태 전이 문제 | lifecycle, async callback, cancellation, stale state |
| 의존성 문제 | SDK/library/plugin version, API contract, env variable |
| 인프라 문제 | network, DB, queue, rate limit, timeout |
| 배포 문제 | migration, feature flag, config, rollback 가능성 |
| 테스트 문제 | test isolation, clock, random seed, fixture, order dependency |

## 4. Hotfix 와 Solid Fix

| 구분 | 기준 |
|---|---|
| Hotfix | 장애 확산 차단, null/invalid 방어, feature flag off, retry 제한, rollback |
| Solid fix | 상태 소유권 정리, 계약 명확화, migration 보강, 테스트 추가, 계측 추가 |

Hotfix는 원인을 가리지 않아야 한다. catch-all, 무한 재시도, 로그만 추가, 실패 무시는 마지막 수단으로만 쓴다.

## 5. 재현과 검증

| 단계 | 확인 |
|---|---|
| Reproduce | 같은 입력/환경/버전에서 실패가 재현되는가? |
| Narrow | 가장 작은 테스트, 파일, 설정으로 실패가 유지되는가? |
| Patch | 실패 조건을 직접 막는가, 아니면 증상만 숨기는가? |
| Verify | 같은 경로로 재검증했는가? |
| Regression | 인접 경로와 edge case가 깨지지 않는가? |

## 6. 추가 정보가 필요한 경우

재현 불가능하거나 로그가 부족하면 아래를 요청한다.

- 전체 stacktrace의 첫 발생 구간
- 실패 직전 사용자 행동 또는 command
- 앱/서버 버전, OS, device, runtime, env
- request id, correlation id, user/session id의 비식별 값
- 최근 배포, feature flag, config, migration 변경
- 실패 입력의 민감정보 제거 샘플

## 7. 출력 템플릿

- 실패 유형:
- 실패 위치:
- 가장 가능성 높은 원인:
- 근거:
- 즉시 조치:
- 영구 수정:
- 검증 방법:
- 남은 불확실성:
- 재발 방지:
