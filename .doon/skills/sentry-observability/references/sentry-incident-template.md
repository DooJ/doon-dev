# Sentry canonical incident 템플릿

이 템플릿은 임계치 또는 고영향 조건을 충족한 사건을 Linear 후보 이슈 한 건으로 만들거나 기존 이슈를 갱신할 때 사용한다. 모든 Sentry event마다 작성하지 않는다.

## 식별

- canonical incident key: `sentry:{organization}:{project}:{issue_id}`
- alias Sentry keys / survivor Linear issue:
- Sentry issue/group:
- 관련 fingerprint와 group:
- 기존 Linear 이슈 검색 결과:
- 중복 판정: `new | update | merge | reopen | ignore`

같은 사건이면 이 템플릿을 새로 만들지 않고 기존 Linear 이슈 본문·코멘트를 갱신한다. release, environment, 사용자, request ID, timestamp 같은 휘발 값만 다른 경우 새 Linear 이슈를 만들지 않는다.

## 관측

- 최초/최근 관측 시각:
- release / dist / environment / deploy:
- 관련 Git commit / PR:
- 발생 수와 영향 사용자:
- 반복·회귀·고영향 조건:
- 오류·성능 현상:
- 정제된 사용자 상호작용: 화면 → action → 상태 → 실패
- Sentry 근거: issue, trace, breadcrumb, Session Replay 링크

원시 stack trace, breadcrumb, replay 화면, request/response body를 Linear나 Notion에 복사하지 않는다. 개인정보·민감정보 제거와 접근 권한을 확인한 링크만 둔다.

## 원인 분류

- cause: `internal | external | mixed | unknown`
- first-party 근거:
- provider·network 근거:
- 반대 증거와 불확실성:
- 외부 원인도 내부 완화가 가능한 부분:
- 최종 또는 잠정 root cause:

`mixed`면 외부 trigger와 내부 timeout·retry·fallback·오류 UX·데이터 일관성 문제를 나눠 쓴다. 근거가 부족하면 `external`로 추정하지 않고 `unknown`을 유지한다.

## 판정과 영향

- 사용자 판정: `candidate | confirmed | rejected`
- 심각도 / 우선순위:
- 사용자·데이터·매출·SLO 영향:
- 현재 workaround:
- 출시·일정·범위 영향:

## 수정과 연결

- 담당 team / owner:
- Linear 상태:
- parent / related / blocks / blocked by:
- 수정 계획:
- branch / commit / PR:
- 로컬 테스트와 QA 근거:

## 릴리스 검증

- 목표 release / environment:
- deploy marker:
- source map / ProGuard mapping / dSYM symbolication:
- 통제된 재현·회귀 테스트:
- 관찰 시간과 재발 여부:
- Sentry resolved / regressed:
- 완료 또는 재개 판단:

릴리스 관측 근거가 없으면 로컬 수정이 성공했더라도 Sentry-origin Linear 이슈를 `Done`으로 바꾸지 않는다.

## 시간순 갱신

| 시각 | 사건 | 분류·영향 변화 | Linear·Git·release 근거 | 다음 행동 |
|---|---|---|---|---|
|  |  |  |  |  |
