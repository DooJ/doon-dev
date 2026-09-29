---
name: skill-versioning
description: Use when 이 플러그인 저장소의 스킬을 새로 만들거나 SKILL.md, reference, script, asset을 수정·가져온 뒤 버전·출처·내용 지문을 기록하고 검증해야 할 때 사용합니다. 일반적인 스킬 실행에는 사용하지 않습니다.
---

# 스킬 버전·출처 관리

현재 플러그인 저장소의 `skills/`만 관리한다. 상위 폴더, 다른 저장소, 설치 캐시를 원본으로 간주하지 않는다.

## 관리 계약

- 각 `skills/<skill-name>/VERSION.md`가 해당 스킬의 버전·출처 원본이다.
- 내용 지문은 `VERSION.md`, `.DS_Store`, `__pycache__`, `*.pyc`, 심볼릭 링크를 제외한 스킬 패키지의 상대경로와 파일 바이트로 계산한다.
- 스킬 변경은 patch, 호환 기능 추가는 minor, 호출·입출력 계약 파괴는 major를 올린다.
- 출처는 `자체 생성`, `외부 참고`, `외부 원문 도입`, `기원 미확인` 중 하나로 기록한다. 외부 자료는 URL, 버전이나 commit, 조회일, 실제 반영 범위를 가능한 만큼 남긴다.
- 새 스킬은 `v1.0.0` 기준선으로 시작한다. 미완성 초안만 `v0.1.0`을 사용할 수 있다.
- 플러그인 구성, 배포 manifest, catalog, 포함 스킬 목록이 바뀌면 `PLUGIN_VERSION.md`, `plugin.json`, `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `catalog.json`의 플러그인 버전도 함께 맞춘다.

## 변경 후 절차

1. 실제 변경 범위와 기존 `VERSION.md`를 확인한다.
2. 출처 표에 새 근거가 필요하면 새 ID를 추가한다.
3. 현재 버전과 버전 이력의 첫 행을 같은 새 버전으로 갱신한다.
4. 저장소 루트에서 지문을 계산해 `내용 SHA-256`에 기록한다.

```bash
python3 skills/skill-versioning/scripts/skill_versions.py fingerprint <skill-name> --root .
```

5. 저장소 전체의 스킬 기록, catalog 등록, 플러그인 버전 정합성을 검사한다.

```bash
python3 skills/skill-versioning/scripts/skill_versions.py check --root .
```

6. 플러그인 manifest 자체도 검증하고 변경 파일을 검토한다.

```bash
claude plugin validate .
git diff --check
```

## VERSION.md 형식

```markdown
# <skill-name> 버전·출처

현재 버전: `v1.0.0`
내용 SHA-256: `sha256:<64자리 지문>`

## 출처

| ID | 분류 | 자료 | 반영 범위 |
|---|---|---|---|
| `S1` | 자체 생성 | 사용자 요청과 현재 작업 | 스킬의 작업 절차 |

## 버전 이력

| 버전 | 날짜 | 변경 요약 | 출처 ID |
|---|---|---|---|
| `v1.0.0` | YYYY-MM-DD | 처음 생성한 작업 절차를 등록했다. | `S1` |
```

기록이 없는 과거 변경에 임의의 버전을 소급하지 않는다. 검증 오류가 남아 있으면 버전 관리 작업을 완료로 보고하지 않는다.
