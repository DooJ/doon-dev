# 재실행 가능한 프로젝트 기능 지도 입력

`codebase-map/<범위>/<버전>/capability-map.json`이 프로젝트 역할·주요 기능·교차 관계의 저작 원본이다. Graphify·Archify의 기계 산출물을 그대로 변환한 파일이 아니다. 분석 에이전트가 현재 코드·설정·배포 아카이브를 읽고 **사용자·운영 목적**으로 기능을 묶어 작성한다. 다음 실행에서는 이 파일을 새 근거와 비교해 수정한 뒤 같은 지도를 확장한다.

## 최소 형식

```json
{
  "schema_version": 1,
  "scope": "예시 생태계",
  "version": "v1.0.0",
  "requested_projects": ["client", "server"],
  "projects": [
    {
      "id": "client",
      "name": "장비 앱",
      "role": "서버에서 일정을 받아 장비 화면에 콘텐츠를 재생한다",
      "capabilities": [
        {
          "id": "playback",
          "name": "일정 기반 재생",
          "description": "장비의 일정 응답을 해석해 재생 대상을 선택하고 화면을 갱신한다",
          "evidence": [{"path": "client/src/Player.kt", "locator": "Player.refreshSchedule", "basis": "source"}]
        }
      ],
      "unknowns": ["현장 장비에서 서버 연결 성공 여부"]
    },
    {
      "id": "server",
      "name": "웹서버",
      "role": "장비 일정과 콘텐츠 조회 계약을 앱에 제공한다",
      "capabilities": [
        {
          "id": "schedule-api",
          "name": "장비 일정 제공",
          "description": "장비 식별자를 받아 해당 장비의 재생 일정을 응답한다",
          "evidence": [{"path": "server/app.war", "locator": "WEB-INF/classes/.../ScheduleController.class", "basis": "archive"}]
        }
      ],
      "unknowns": ["운영 DB의 실제 일정 데이터"]
    }
  ],
  "relations": [
    {
      "id": "schedule-sync",
      "function": "장비 일정 동기화",
      "kind": "cooperation",
      "status": "static_confirmed",
      "participants": [
        {"project": "server", "responsibility": "장비별 일정 조회 계약과 응답을 제공한다", "evidence": [{"path": "server/app.war", "locator": "ScheduleController.class", "basis": "archive"}]},
        {"project": "client", "responsibility": "일정을 요청하고 화면 재생 상태에 반영한다", "evidence": [{"path": "client/src/Player.kt", "locator": "Player.refreshSchedule", "basis": "source"}]}
      ],
      "contract": "장비 ID를 사용한 일정 HTTP 요청과 응답",
      "result": "서버 일정이 장비의 재생 대상 선택에 반영된다",
      "unknowns": ["운영 중 네트워크 전달과 DB 값은 미확인"]
    }
  ]
}
```

`path`는 `--project-root` 기준 상대경로이며 실제 파일이어야 한다. 형제 저장소의 WAR/JAR도 `../Web/...`처럼 상대경로로 쓴다. `locator`는 코드의 메서드·행이나 아카이브 내부 클래스·설정 위치다. `basis`는 `source`, `archive`, `config` 중 하나다. 파일·위치를 기록해도 실제 런타임 성공은 입증되지 않는다.

프로젝트 `id`는 관계에서 쓰는 안정적인 영문 식별자다. 기존 볼트의 프로젝트 노트 파일명을 보존해야 하면 프로젝트 객체에 `"note": "기존 노트 이름"`을 추가한다. 새 이름으로 바꾸려면 기존 노트·링크의 이전을 별도로 검토한다.

관계 `kind`는 `cooperation`, `shared_implementation`, `duplicate_implementation`, `similar_distinct`, `unverified` 중 하나다. 공통 구현·중복 구현·목적이 다른 유사 기능에는 `comparison`으로 판단 이유를 추가한다. `status`는 `static_confirmed`, `inferred`, `runtime_required` 중 하나다. 연결이 없는 프로젝트는 `isolated_reason`으로 근거를 설명한다. 단일 프로젝트의 `relations`는 빈 목록일 수 있다.

## 실행

`capability_map.py validate`는 새 멀티 볼트에서도 필수다. 아래 `render/check`는 기존 단일 `vault/` 산출물의 호환 경로다. 새 `vaults/`는 프로젝트별 생성기와 `check_multi_vault.py`를 사용한다.

```bash
python3 "$CODEGRAPH_SKILL/scripts/capability_map.py" validate \
  --project-root "$PROJECT_ROOT" --input "$VERSION_DIR/capability-map.json" \
  --expected-project client --expected-project server
python3 "$CODEGRAPH_SKILL/scripts/capability_map.py" render \
  --project-root "$PROJECT_ROOT" --input "$VERSION_DIR/capability-map.json" \
  --vault "$VERSION_DIR/vault" \
  --expected-project client --expected-project server
python3 "$CODEGRAPH_SKILL/scripts/capability_map.py" check \
  --project-root "$PROJECT_ROOT" --input "$VERSION_DIR/capability-map.json" \
  --vault "$VERSION_DIR/vault" \
  --expected-project client --expected-project server
```

기존 단일 볼트에서 `validate`는 요청 프로젝트 누락, 근거 파일 부재, 역할·기능 설명 부재, 관계 양쪽의 책임·근거 부재를 실패로 처리한다. `render`는 검증 후 프로젝트별 노트와 기능·관계 지도를 만든다. 이전 생성 노트의 지문이 달라졌으면 사용자 편집으로 보고 덮어쓰지 않는다. 기존 노트보다 짧아지면 실패하며, 의도적 통합일 때만 검토 이유를 `--shortening-reason`으로 기록한다. `check`는 생성 노트와 입력의 일치, `00_HOME.md` 진입점, 위키링크, 통합 개요의 요청 프로젝트 포함, 새 버전의 변경 보고서를 검사한다. `00_HOME.md`, 수동 흐름 노트, `.obsidian/`은 자동 수정하지 않으므로 새 지도로 이어지는 시작 링크와 대표 흐름의 코드 근거는 실행자가 별도로 검증한다.

검증 통과는 **구조와 근거 위치의 최소 조건**이다. 사용자·운영 관점의 기능 분류와 중복 판정이 올바른지는 대표 기능을 코드와 아카이브에서 다시 따라가 확인한다. 버전이 바뀌면 [프로젝트 버전 관리 기준](project-versioning.md)의 `CHANGE_REPORT.md`로 실제 전후 차이도 기록한다.

새 출력의 `data/catalog.json`·`vaults/registry.json`·`generation-manifest.json` 계약과 검사 명령은 [분석 데이터와 멀티 볼트 계약](data-vault-model.md)을 따른다.
