# 프로젝트 코드그래프 버전 관리

이 버전은 **프로젝트의 `codebase-map/` 전체**를 가리킨다. DooN Dev 플러그인 버전이나 `codegraph` 스킬 버전과 별개다. `codebase-map/version-ledger.json`이 원본 이력이고 `codebase-map/VERSION.md`는 사람이 읽는 파생 요약이다. 스크립트로만 둘을 함께 갱신한다.

## 판단 기준

- Graphify, Archify, Obsidian 중 하나만 개선하거나 같은 기준 아래 내용을 보강하면 **현재 버전 그대로** 둔다. 검증된 산출물이 바뀐 경우에만 구성요소 아래 실행 시각, 작업 요약, 상대경로와 SHA-256을 추가한다. 실패·미검증 시도와 지문이 같은 재실행은 이력으로 만들지 않는다.
- 세 구성요소가 함께 참조할 **코드그래프의 기준이나 해석을 새로 정할 때** 버전을 올린다. `patch`는 표현·정확도·범위의 소규모 보정, `minor`는 핵심 흐름·구성요소·지도 해석의 호환 확장, `major`는 기존 지도 해석이나 산출물 계약을 깨는 재정의다. 작업 시작 시 잠정 수준을 선택할 수 있다.
- 새 버전 작업을 마치고 실제 변경 규모가 달라졌다면 `reclassify`로 **진행 중인 최신 버전 번호만** 다시 계산한다. 예를 들어 `v1.0.0`에서 `patch`로 시작한 `v1.0.1`은 `minor` 재분류 시 같은 작업 이력을 가진 `v1.1.0`이 된다. 앞 버전의 번호·작업 이력은 수정하지 않는다.
- `bump`는 앞 버전을 종료하고 새 버전을 연다. 이후 종료된 버전은 수정하지 않는다. 현재 버전은 다음 `bump` 전까지 열려 있고 그 안에서 여러 차례 내부 갱신할 수 있다. 새 버전에서 실행하지 않은 구성요소는 요약에 앞 버전의 최신 검증 결과를 **승계**로 표시한다. 승계를 새 실행처럼 기록하지 않는다.
- 이력의 시각은 현지 UTC 오프셋을 포함한다. 과거 산출물이 이미 있는 프로젝트는 현재 확인한 결과만 신규 이력으로 등록한다. 기존 실행 시각을 추정하거나 과거 버전을 소급 생성하지 않는다.
- 이력의 지문은 산출물 변경을 검출한다. **이 스크립트는 산출물 복사본을 보관하지 않는다.** 이전 상태로 되돌려야 한다면 프로젝트 Git 이력과 Archify의 시각별 출력 폴더 등 실제 보존된 자료를 확인한다.

## 실행 순서

`SCRIPT`는 설치된 `codegraph/scripts/version_ledger.py`의 실제 경로다. 명령은 프로젝트 루트를 받으며 `codebase-map` 안에 두 파일을 만든다.

```bash
python3 "$SCRIPT" --project "$PROJECT_ROOT" init --note "현재 코드그래프 기준선"
python3 "$SCRIPT" --project "$PROJECT_ROOT" record --component graphify --artifact graphify-out/graph.json --note "실제 변경 및 조회 검증 요약"
python3 "$SCRIPT" --project "$PROJECT_ROOT" record --component archify --artifact archify/flow-20261002-0900/diagram.json --artifact archify/flow-20261002-0900/index.html --note "다이어그램 검증 요약"
python3 "$SCRIPT" --project "$PROJECT_ROOT" record --component obsidian --artifact vault/00_HOME.md --artifact vault/01_SYSTEM_MAP.md --note "볼트 링크·근거 확인 요약"
python3 "$SCRIPT" --project "$PROJECT_ROOT" bump --level patch --note "전체 코드그래프 기준 보정"
python3 "$SCRIPT" --project "$PROJECT_ROOT" reclassify --level minor --note "핵심 흐름까지 확장한 새 기준"
python3 "$SCRIPT" --project "$PROJECT_ROOT" status
```

위 산출물 경로는 예시다. 실제로 생성하고 검증한 파일 또는 생성물 폴더만 지정한다. Obsidian 볼트는 `.obsidian` 개인 UI 설정이나 수동 노트 대신 이번에 갱신한 설명·색인 노트를 지정한다. 같은 구성요소의 다음 실행에서도 비교 범위가 일정하도록 대표 산출물을 유지하고, 범위가 바뀌면 요약에 이유를 남긴다. 최초 `init` 뒤 기존 산출물을 등록할 때에는 작업 요약에 **기존 결과 기준선 등록**이라고 밝힌다.

## 완료 보고

`VERSION.md`에서 전체 현재 버전과 Graphify·Archify·Obsidian의 최신 실제 실행 시각을 확인한다. 이번에 실행하지 않은 구성요소는 승계로 알리고, 기록이 없는 구성요소는 미완료로 표시한다. 버전 수준을 재분류했다면 처음 선택한 수준과 최종 수준을 함께 알린다.
