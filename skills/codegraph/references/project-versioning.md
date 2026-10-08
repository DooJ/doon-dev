# 분석 범위별 코드그래프 버전 관리

각 분석 범위는 `codebase-map/<범위 이름>/`에 독립적으로 둔다. 예를 들어 `보이미 생태계`와 `보이미 메뉴`는 같은 프로젝트 루트에서도 각각 `v1.0.0`부터 시작한다. 범위 폴더의 `version-ledger.json`이 원본 이력이고 `VERSION.md`는 사람이 읽는 전체 요약이다. 각 `vX.Y.Z/`에는 **그 버전에서 생성한 실제 산출물**과 버전 요약을 둔다. DooN Dev 플러그인·스킬 버전과는 별개다.

## 범위와 버전 판단

- 범위 이름은 사용자의 분석 목적과 대상이 드러나게 정한다. 같은 저장소 전체를 다루는 지도와 그 안의 특정 앱 지도는 별도 범위다. 이미 같은 이름의 범위가 있으면 요청 범위가 같은지 먼저 확인한다. 이름이 같다는 이유로 다른 목적의 지도를 덮어쓰지 않는다.
- Graphify, Archify, Obsidian 중 하나를 보강하고 지도 전체의 기준이 같으면 **현재 범위의 현재 버전**에 검증된 산출물의 실행 시각·요약·상대경로·SHA-256을 누적한다. 실패·미검증 시도와 지문이 같은 재실행은 기록하지 않는다.
- 전체 기준이나 해석을 새로 정할 때만 해당 범위의 버전을 올린다. `patch`는 소규모 보정, `minor`는 호환되는 핵심 흐름·구성요소 확장, `major`는 기존 지도 해석이나 산출물 계약을 깨는 재정의다. 다른 범위의 번호는 그대로 둔다.
- `bump`는 이전 버전을 닫고 새 `vX.Y.Z/` 폴더를 연다. 새 폴더는 비어 있으며 이전 산출물을 자동 복사하지 않는다. 새 버전에서 다시 실행하지 않은 구성요소는 `VERSION.md`에 이전 버전 결과의 **승계**로 표시한다. 해당 파일을 열 때는 실제 이전 버전 경로를 사용한다.
- 새 버전의 `CHANGE_REPORT.md`에는 이전·현재 산출물의 실제 차이를 기록한다. 최소한 상세·개요 그래프의 지문과 노드·관계, Archify 생성·승계 여부, 볼트 노트·내부 링크의 증감, 요청한 프로젝트와 주요 기능·중복·공유·연결 관계의 포괄 여부를 대조한다. 상세 그래프를 재추출했어도 내용 지문이 같다면 **변경 없음**으로 적는다. 기능 목록 행이나 노트 수만 늘어난 것을 깊이 확장으로 주장하지 않는다.
- 이전 버전의 노트·기능 관계가 새 버전에서 빠졌으면 `CHANGE_REPORT.md`에 삭제·통합 이유와 이전 자료의 접근 경로를 적는다. 의도하지 않은 축소나 요청한 프로젝트별 기능 지도의 누락은 새 버전 완료 전에 복구한다. 버전 번호를 먼저 올렸다는 사실은 내용 변경이나 완료를 증명하지 않는다.
- 예상보다 변경 규모가 달라지면 `reclassify`로 **열린 최신 버전만** 재분류한다. 예를 들어 `v1.0.1` → `v1.1.0`은 해당 폴더를 함께 바꾼다. 작업 중 산출물의 내부·외부 링크, 생성기 설정에 옛 버전 경로가 박혀 있지 않은지 확인하고 다시 검증한다. 닫힌 버전의 번호와 기록은 바꾸지 않는다.
- 실행 시각은 현지 UTC 오프셋을 포함한다. 지문은 변경 확인용이고 같은 버전 안의 이전 시각별 파일 백업을 만들지 않는다. 과거 산출물의 시각이나 버전은 추정해 소급 등록하지 않는다.

## 실행 순서

`LAYOUT`과 `LEDGER`는 설치된 `codegraph/scripts/` 안의 실제 스크립트 경로다. `PROJECT_ROOT`는 분석 결과를 보관할 프로젝트 루트다. 셸 변수는 예시이며 범위 이름에 공백이 있어도 모두 따옴표로 감싼다.

```bash
SCOPE_NAME='보이미 생태계'
python3 "$LAYOUT" --project "$PROJECT_ROOT" --scope "$SCOPE_NAME" status
python3 "$LAYOUT" --project "$PROJECT_ROOT" --scope "$SCOPE_NAME" prepare
python3 "$LEDGER" --project "$PROJECT_ROOT" --scope "$SCOPE_NAME" init --note "생태계 전체 코드그래프 기준선"

VERSION='v1.0.0'
GRAPH_DIR="$PROJECT_ROOT/codebase-map/$SCOPE_NAME/$VERSION/graphify-out"
GRAPHIFY_OUT="$GRAPH_DIR" graphify update "$PROJECT_ROOT" --no-cluster
GRAPHIFY_OUT="$GRAPH_DIR" graphify cluster-only "$PROJECT_ROOT" --graph "$GRAPH_DIR/graph.json"

python3 "$LEDGER" --project "$PROJECT_ROOT" --scope "$SCOPE_NAME" record --component graphify --artifact graphify-out/graph.json --artifact graphify-out/overview/graph.json --artifact graphify-out/overview/graph.html --note "상세·개요 그래프 검증"
python3 "$LEDGER" --project "$PROJECT_ROOT" --scope "$SCOPE_NAME" record --component archify --artifact archify/flow-20261002-0900/diagram.json --artifact archify/flow-20261002-0900/index.html --note "다이어그램 검증"
python3 "$LEDGER" --project "$PROJECT_ROOT" --scope "$SCOPE_NAME" record --component obsidian --artifact data/catalog.json --artifact generation-manifest.json --artifact vaults --note "데이터 지문·멀티 볼트 링크·근거 확인"

python3 "$LEDGER" --project "$PROJECT_ROOT" --scope "$SCOPE_NAME" bump --level patch --note "전체 지도 보정"
python3 "$LEDGER" --project "$PROJECT_ROOT" --scope "$SCOPE_NAME" reclassify --level minor --note "핵심 흐름까지 확장"
python3 "$LEDGER" --project "$PROJECT_ROOT" --scope "$SCOPE_NAME" status
```

상세 그래프를 사용자에게 전달할 때는 `cluster-only --no-label`을 쓰지 않는다. 이 옵션은 군집 이름을 `Community N`으로 남긴다. 모델 로그인이 없어도 기본 재군집화의 대표 허브 심볼명을 사용하고, `graph.json`·`GRAPH_REPORT.md`·`graph.html`에서 자리표시자가 없는지 확인한다.

`graphify update`는 기존 Graphify 결과가 있을 때의 예시다. 첫 실행에는 검토한 원본의 `extract --code-only --no-cluster` 등 대상에 맞는 명령을 사용한다. 검토한 Graphify 원본은 `GRAPHIFY_OUT` 절대경로를 추출·갱신에서 지원한다. 실행 때마다 현재 버전의 `GRAPH_DIR`을 다시 설정한다. Archify·볼트·개요 그래프도 같은 버전 폴더를 출력 대상으로 지정한다. 예시 산출물 경로는 실제로 만들고 검증한 파일로 바꾼다. 단일 프로젝트에서 개요가 불필요하면 `overview/` 경로를 넣지 않는다.

## 기존 무범위 결과

옛 `codebase-map/graphify-out`, `archify`, `vault`, 루트 `graphify-out` 호환 링크와 `codebase-map/version-ledger.json`은 자동 이동하지 않는다. 먼저 어느 분석 범위에 속하는지 정하고, 상대 링크·생성기 경로·볼트 소유권·Git 추적을 확인한 뒤 별도 이전 작업으로 옮긴다. 기존 무범위 ledger는 `--scope` 없이 읽고 기록할 수 있지만, **새 무범위 ledger 생성은 허용하지 않는다**. 이전 과정에서 과거 실행 시각이나 버전을 만들어내지 않는다.

## 완료 보고

범위 이름과 현재 버전, Graphify·Archify·Obsidian의 최신 실제 실행 시각을 확인한다. 이번 버전에서 실행하지 않은 구성요소는 이전 버전 경로와 함께 승계로 알리고, 기록이 없는 구성요소는 미완료로 표시한다. 버전 수준을 재분류했다면 처음 수준과 최종 수준을 함께 알린다.
