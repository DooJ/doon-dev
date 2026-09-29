---
name: sentry-observability
description: "Use when 프로젝트에 Sentry 관측을 새로 연결하거나 기존 연결을 기준선화할 때, 릴리스 후보·staging·production에서 반복 또는 회귀한 오류와 성능 문제를 사용자 상호작용 근거로 분류할 때, Sentry 사건을 중복 없는 Linear 이슈·Git 수정·릴리스 검증으로 이어갈 때. 단순 로컬 개발 오류 수정이나 일반 로그 분석만 요청한 경우는 제외합니다."
---

# Sentry 관측 운영

## 목적

Sentry를 릴리스 이후 실제 동작을 관측하는 원본으로 사용하고, Gate를 통과한 사건만 Linear의 `Triage` 후보로 기록한 뒤 사람이 처리하기로 판정한 사건만 수정 업무로 승격한다. 이벤트 수와 업무 수를 분리해 개발 중 오류마다 운영 리포트를 만들지 않는다.

프로젝트 업무의 원본 책임은 다음과 같다.

| 시스템 | 원본 책임 |
|---|---|
| Sentry | runtime event, Sentry issue/group, trace, 성능, release·environment·deploy, 개인정보 보호가 확인된 사용자 상호작용 근거 |
| Linear | Gate를 통과한 `Triage` 후보 기록과 사용자가 확인한 수정 업무, 원인·상태·담당·수정·재검증 이력 |
| Git | 계측 설정, 코드, 테스트, source map·debug symbol, branch·commit·PR, 릴리스 산출물 |
| Notion | 프로젝트 허브의 목표·범위·일정·버전 이력, 릴리스 판단, 사용자·사업 영향과 주요 운영 결정 |

원시 event, stack trace, breadcrumb, Session Replay를 Linear·Notion·Git 문서에 복제하지 않는다. 정제된 요약과 권한이 제한된 Sentry 링크만 연결한다.

## 발동과 제외

- 신규 또는 기존 프로젝트에서 Sentry 도입·연결·릴리스 관측 운영을 사용자가 승인한 경우 발동한다.
- 릴리스 후보(RC), staging, production에서 의도하지 않은 오류·크래시·성능 저하가 반복되거나 회귀했을 때 발동한다.
- 릴리스별 오류율, 영향 사용자, 사용자 상호작용 흐름을 확인해 수정 업무로 판정하려 할 때 발동한다.
- 단순 로컬 개발 중 컴파일 오류, 테스트 실패, 구현 중 바로 고친 실수에는 `error-responder` 또는 일반 구현 루프를 사용한다. 개발 중 오류마다 운영 리포트를 만들지 않는다.
- `development` event는 로컬 진단에 사용할 수 있지만, 사용자가 별도 승인하지 않은 한 운영 incident 후보·알림·Linear 생성 입력에서 제외한다.

아래 실행 계약만으로 독립 동작하며, DooN Core가 연결되어 있으면 공통 Sentry 추적 워크플로우를 추가로 적용한다. 구조화된 사건 본문이 필요할 때만 `references/sentry-incident-template.md`를 읽는다.

## 활성화 Gate

Notion·Git·Linear 연결형 전달 승인과 Sentry telemetry 승인을 분리한다. Sentry SDK는 외부 전송과 개인정보 검토가 수반되므로 기존 전달 승인을 근거로 자동 활성화하지 않는다.

1. 실제 배포되는 runtime 표면을 식별한다. 독립적으로 릴리스되는 웹 frontend, backend, Android, iOS, desktop, worker는 별도 Sentry project 후보로 본다.
2. 저장소 하나당 project 하나를 기계적으로 만들지 않는다. 같은 release lifecycle과 접근 권한을 공유하는 표면만 합친다.
3. 기존 Sentry organization·project를 먼저 검색하고, 정확히 일치하면 재사용한다. 여러 후보가 있으면 생성·변경 전에 사용자를 확인한다.
4. SDK 도입, 외부 event 전송, Session Replay, 개인정보 처리 범위를 설명하고 명시 승인을 받는다.
5. 신규 프로젝트는 첫 배포 준비 시점부터, 기존 프로젝트는 활성화 시점의 Git branch·HEAD·release·environment를 기준선으로 삼는다. 과거 event와 해결 이슈를 Linear에 소급 생성하지 않는다.

## 릴리스 계측 계약

다음 항목을 해당 플랫폼과 기존 CI 방식에 맞게 설정하고 실제 값으로 검증한다.

- `environment`: 최소 `development`, `staging`, `production`을 구분한다.
- `release`: 배포 artifact와 Git commit을 역추적할 수 있는 안정적인 식별자를 사용한다.
- `dist` 또는 build number: 같은 release의 artifact가 여러 개면 구분한다.
- commit association과 deploy marker: 어떤 commit이 어느 environment에 언제 배포됐는지 연결한다.
- 웹 source map, Android ProGuard/R8 mapping, Apple dSYM 같은 symbol artifact를 CI에서 업로드한다.
- DSN은 공개 식별자라는 이유로 무제한 취급하지 않고 환경별 설정에 둔다. auth token은 최소 권한 CI secret으로만 관리한다.
- staging의 통제된 test event로 project, environment, release, commit, deploy, symbolication, alert, 개인정보 제거를 확인한다.

프로젝트의 실제 SDK와 공식 문서를 확인하지 않은 채 옵션 이름이나 지원 기능을 추정하지 않는다.

## 사건 후보와 보고 시점

Sentry event 수집과 업무 보고를 같은 것으로 취급하지 않는다.

다음 중 하나가 확인될 때만 canonical incident 후보를 만들거나 갱신한다.

- 릴리스 후보(RC), staging, production에서 같은 의도치 않은 실패가 합의된 횟수·사용자 영향·시간 임계치를 넘겨 반복됨
- 이전에 해결한 문제가 새 release에서 회귀함
- crash, 데이터 손상, 보안·개인정보, 결제, 핵심 기능 중단처럼 단건이어도 영향이 큼
- 성능 저하가 합의한 SLO 또는 release 기준을 벗어남
- 외부 장애가 지속되거나 내부 retry·fallback·오류 UX 개선이 필요함

프로젝트별 임계치와 관찰 시간은 서비스 중요도·트래픽·기존 SLO에서 정하며 임의의 숫자를 만들지 않는다. 임계치가 없으면 영향과 반복 근거를 제시해 사용자 판정을 요청한다.

## 중복 제거와 canonical incident

- 기본 identity는 Sentry issue/group ID와 조직·프로젝트를 합친 `sentry:{organization}:{project}:{issue_id}`다.
- Sentry grouping이 한 원인을 과도하게 나누거나 합친 근거가 있을 때만 fingerprint를 조정한다. exception type, 최상위 first-party frame, 정규화된 error code, provider·operation 같은 안정된 값을 사용한다.
- user ID, request ID, timestamp, 동적 URL, 원문 메시지 같은 휘발 값은 identity에서 제외한다.
- release와 environment는 회귀·영향을 판정하는 관측 차원이지 기본 중복 키가 아니다. 같은 문제가 다른 release나 environment에서 나타나면 같은 사건을 갱신한다.
- 여러 Sentry issue가 하나의 root cause라면 Linear 사건 하나에 관련 group으로 연결할 수 있다. 반대로 한 group 안에 독립 root cause가 확인되면 근거를 남기고 분리한다.
- mobile과 backend처럼 여러 Sentry project의 issue가 한 사용자 실패 체인의 같은 root cause를 가리키면 Linear 사건 하나로 합친다. 가장 오래된 유효 Linear 이슈와 canonical key를 survivor로 두고 나머지 Sentry key를 alias로 보존한다.
- 새 Linear 이슈를 만들기 전에 해당 canonical key, fingerprint, 증상, 관련 open/canceled/done 이슈를 검색한다.
- 같은 사건이면 발생 수, 최신 release·environment, 영향, 분류, 증거, 마지막 관측 시각을 기존 Linear 후보 또는 기존 리포트에 갱신하고 새 Linear 이슈를 만들지 않는다.
- 회귀 또는 과거 `Done` 이슈와 같은 root cause는 새 사건을 만들지 않고 기존 Linear 이슈를 재개하되, root cause가 달라졌다는 증거가 있을 때만 파생 이슈로 분리한다.
- canonical incident root는 Linear 이슈 최대 한 건으로 유지한다. 여러 Sentry group·project·release가 같은 root cause를 가리켜도 root를 추가 생성하지 않는다.
- 외부 장애 추적과 내부 복원력 개선처럼 별도 owner·우선순위·생명주기가 필요한 파생 action 이슈는 허용한다. 각 파생 action 이슈는 독립적인 수정 범위와 commit을 가지며 root의 canonical key를 identity로 재사용하지 않고 parent/related/blocks 관계로 연결한다.

## 원인 분류

증거가 충분해질 때까지 `unknown`을 유지한다. 오류 메시지만으로 외부 책임을 확정하지 않는다.

| 분류 | 판정 근거 | 기본 처리 |
|---|---|---|
| `internal` | first-party stack, 자체 commit 이후 회귀, 계약·validation·serialization·configuration·상태 처리 결함 | 내부 수정 후보로 보고 |
| `external` | provider status·응답·trace로 확인한 외부 429/5xx, DNS·TLS·network·provider outage이며 자체 요청·처리 결함 근거가 없음 | transient면 집계·모니터링, 지속 영향이면 보고 |
| `mixed` | 외부 실패가 trigger지만 자체 timeout·retry·circuit breaker·fallback·오류 UX·데이터 일관성 대응도 부족함 | 외부 상황과 내부 개선을 분리해 한 사건에 기록 |
| `unknown` | stack·trace·재현·provider 근거가 부족하거나 서로 충돌함 | 내부 triage owner를 두고 추가 증거 수집 |

외부 원인도 내부 완화가 가능하면 “우리 문제가 아님”으로 닫지 않는다. provider 복구 추적과 우리 retry·fallback·오류 UX 개선을 각각 action으로 둔다. `mixed` 사건에서 외부 장애 자체와 내부 개선을 별도 Linear 이슈로 나눌 때는 parent/related/blocks 관계로 연결한다.

## 사용자 상호작용 근거

- 개인정보 보호 설정이 확인된 breadcrumb, navigation, 사용자 action, trace, Session Replay로 오류 직전 흐름을 재구성한다.
- “어떤 화면·행동·상태에서 실패했는가”만 정제해 요약한다. 원시 키 입력, request/response body, 토큰, Cookie, 이메일, 전화번호, 결제·건강·위치 같은 개인정보·민감정보는 복사하지 않는다.
- Session Replay와 첨부파일은 기본 수집으로 간주하지 않는다. 별도 승인, 입력 마스킹, 접근 권한, 표본율, 보존 기간을 확인한 뒤 사용한다.
- 사용자 식별이 필요하면 최소한의 가명 ID를 사용하고 재식별 키와 접근 권한을 분리한다.
- client와 server의 event·trace를 연결할 때 correlation ID가 개인정보나 credential을 포함하지 않는지 확인한다.

## Sentry → Linear → Git → 릴리스 상태

1. Sentry 후보를 canonical incident로 dedupe하고 `internal|external|mixed|unknown`으로 분류한다.
2. 임계치 또는 고영향 조건을 충족하면 대상 Linear 프로젝트에 `Triage` 후보 기록을 한 번만 만들거나 기존 후보를 갱신하고 사용자에게 근거와 함께 알린다. 사용자 확인 전에는 수정 업무가 아니다.
3. 사용자가 이슈로 확인하면 수정 업무로 승격해 `Todo`/`Backlog`에서 `In Progress`로 전환하고 수정 계획 코멘트를 남긴다. 아니라고 판단하면 이유를 남기고 `Canceled`로 바꾼다.
4. 수정은 하나의 주 Linear 이슈 단위로 분리해 commit/PR에 연결한다. 로컬 테스트와 QA 결과를 코멘트한다.
5. 로컬 검증만 통과한 Sentry-origin 이슈는 `In Review`, `Ready for Release` 또는 팀의 가까운 상태에 둔다.
6. 목표 release·environment의 deploy marker, symbolication, 통제된 재현/회귀 테스트, 합의한 관찰 시간 동안의 재발 여부라는 릴리스 관측 근거가 생기기 전에는 `Done`으로 바꾸지 않는다.
7. 릴리스 검증이 통과하면 완료 코멘트에 release·commit·deploy·Sentry 근거를 남기고 Linear를 `Done`, Sentry issue를 resolved로 전환한다.
8. Sentry에서 regressed되면 같은 Linear 이슈를 다시 열고 새 release·environment·영향 근거를 추가한다.

상태 이름은 workspace의 실제 상태를 읽고 의미가 가장 가까운 값으로 매핑한다. native integration을 완전한 양방향 동기화로 가정하지 않는다.

## 리포트 원칙

- 기본 incident 리포트 원본은 canonical Linear 이슈 본문과 시간순 코멘트다. event마다 파일이나 Notion 페이지를 만들지 않는다.
- Sentry에는 원시 관측, Linear에는 정제된 원인·action·수정·검증, Notion에는 릴리스·범위·일정·사업 판단만 둔다.
- P0/P1, 보안·개인정보·데이터 손상, 대규모 중단, 출시 판단 변경처럼 별도 회고가 필요할 때만 사용자가 승인한 Notion incident 또는 Git postmortem을 하나 만들고 같은 사건을 계속 갱신한다.
- 사용자가 시점 보고서 파일을 요청한 경우에만 `snapshot-report-writer`를 사용한다. 다음 event마다 새 보고서를 만들지 않는다.
- 문서에는 canonical key, Sentry·Linear·release·commit 링크를 둬 같은 사건을 검색할 수 있게 한다.
- **Sentry → Linear**는 반복·회귀·고영향과 중복 제거를 통과한 사건을 `Triage` 후보로 연결하고, 사용자 판정 뒤 확정 수정 업무로 승격한다. **Sentry → Notion**은 프로젝트 범위·일정·릴리스 판단을 바꾼 사건만 `주요 운영 사건`에 요약한다.
- 동일 사건의 해결·회귀는 기존 Linear canonical incident와 Notion 요약을 갱신하며 새 업무나 페이지를 반복 생성하지 않는다.

## 도구와 실패 대체 경로

- 외부 Sentry 플러그인 또는 connector가 현재 runtime에 연결돼 있으면 실제 제공 기능과 권한을 먼저 확인한 뒤 조회·요약·갱신에 선택적으로 사용한다.
- 외부 Sentry 플러그인이 없어도 스킬은 동작해야 한다. 프로젝트 SDK·CI 설정, Sentry 웹 콘솔, 공식 API·`sentry-cli`, Git/Linear 연동 중 실제로 사용할 수 있는 경로를 선택한다.
- 자동 조회·생성 권한이 없으면 로컬 설정과 사용자 제공 event 링크를 근거로 분석하고, 필요한 Sentry·Linear 수동 절차를 정확히 보고한다.
- 도구가 지원하지 않는 project 생성, integration, alert, issue resolve, replay 확인을 성공했다고 꾸며내지 않는다. 미완료 항목과 검증 방법을 남긴다.
- 이 스킬의 배포 자체는 외부 Sentry 플러그인, MCP server, 특정 SDK 패키지에 의존하지 않는다.

## 완료 출력

필요한 항목만 보고한다.

- Sentry organization/project와 대상 runtime 표면
- environment·release·commit·deploy·symbol artifact 연결 결과
- 개인정보 scrubbing, breadcrumb·Session Replay 승인과 검증 결과
- 새로 만든 사건, 갱신·병합·재개한 canonical incident, 중복 방지 근거
- `internal|external|mixed|unknown` 분류와 증거·불확실성
- Linear 상태와 Git commit/PR, 릴리스 관측 근거
- 외부 Sentry 플러그인 사용 여부와 실제 대체 경로
- 아직 수동으로 해야 하거나 권한 때문에 확인하지 못한 항목
