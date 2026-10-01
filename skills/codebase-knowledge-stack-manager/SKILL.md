---
name: codebase-knowledge-stack-manager
description: "Graphify·Archify 원본 스킬의 출처와 전역 설치를 관리하거나, 한 프로젝트의 코드 그래프·아키텍처 다이어그램·Obsidian 볼트를 codebase-map/에 구성하고 갱신할 때 사용합니다. 일반 docs·publish 문서 작성에는 적용하지 않습니다."
---

# 코드베이스 지식 스택 관리

이 스킬은 두 범위를 구분한다. DooN의 `Sources`는 외부 **원본**을 보관하고, 각 프로젝트의 `codebase-map/`은 분석 **결과**를 보관한다. Graphify와 Archify의 원본 `SKILL.md`는 수정하지 않는다. 별도의 DooN External 플러그인을 만들지 않는다.

## 외부 원본과 에이전트 배포

사용자가 원본 연결·설치·업데이트를 요청한 경우에만 수행한다.

1. 현재 환경의 `AGENTIC_ROOT`를 확인한다. 공식 원본은 [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify)와 [tt-a1i/archify](https://github.com/tt-a1i/archify)에서 재확인한다. 동명 프로젝트를 추측해 선택하지 않는다.
2. 원본을 `<AGENTIC_ROOT>/Sources/external/graphify`, `<AGENTIC_ROOT>/Sources/external/archify`에 별도 checkout으로 받거나 기존 checkout을 갱신한다. 출처 URL·commit·라이선스·검토일을 로컬 목록에 남긴다. `Sources/selection.json`은 DooN 소유 플러그인 선택 상태이므로 외부 저장소를 끼워 넣지 않는다.
3. 실행·설치 전에 대상 스킬과 스크립트, 의존성을 `skill-inspector` 또는 같은 수준의 읽기 전용 검토로 확인한다. 검토가 끝나기 전에는 원본 설치 스크립트를 실행하지 않는다.
4. 검토한 원본에서 Codex·Claude·Antigravity의 **사용자 전역** 설치 경로와 명령을 확인해 각각 적용한다. 원본 checkout과 설치본의 버전·내용이 일치하는지 확인하고, 설치 명령이 최신 원격 버전을 다시 받는다면 고정된 원본을 설치할 수 있는 방법을 먼저 찾는다. DooN Dev 플러그인은 이 **관리 스킬**을 배포하며, 외부 스킬·CLI의 플랫폼별 설치는 이 스킬이 관리하는 별도 상태다. Graphify의 프로젝트 설치나 `AGENTS.md`·`CLAUDE.md`를 고치는 상시 지침 명령은 실행하지 않는다. DooN 생성 어댑터의 소유권을 보존한다.
5. 각 에이전트에서 설치된 스킬·도구의 실제 경로와 버전을 확인한다. 지원되지 않는 플랫폼이나 실패한 설치는 성공으로 표시하지 않는다. DooN Dev 관리 스킬 자체의 변경은 이 저장소의 버전 관리와 플러그인 배포 절차를 따른다.

## 프로젝트 산출물

프로젝트 안에는 아래 **실제 폴더 하나**를 사용한다. 루트의 `graphify-out`은 원본 Graphify 지침과 CLI가 기대하는 경로를 유지하기 위한 상대 심볼릭 링크다.

```text
<project>/
├── codebase-map/
│   ├── graphify-out/  # 그래프·보고서·작업 캐시
│   ├── archify/       # 다이어그램 JSON·HTML·검증 결과
│   └── vault/         # Obsidian 볼트
└── graphify-out -> codebase-map/graphify-out
```

1. 프로젝트 루트와 기존 `graphify-out`, `.archify`, Obsidian 볼트의 존재를 먼저 확인한다. 이 스킬 폴더의 `scripts/project_layout.py`에 `--project <project> status`를 전달해 배치를 점검하고 `prepare`로 빈 구조와 호환 링크를 만든다. 기존 `graphify-out` 실폴더는 충돌이 없을 때만 `prepare --migrate-existing`으로 옮긴다. 다른 경로를 가리키는 링크나 내용이 있는 대상 폴더를 덮어쓰지 않는다.
2. Graphify는 **프로젝트 루트**에서 실행한다. 실행 후 `graphify-out`을 다시 옮기지 않는다. 링크 경유 생성·조회·증분 갱신을 확인한다. Graphify 원본 스킬이 링크와 맞지 않으면 해당 실행을 중단하고 원래 경로를 유지한 채 원인을 보고한다.
3. Archify에는 출력 경로를 `codebase-map/archify/<유형>-<이름>-<시각>/`로 처음부터 지정한다. 기존 `.archify` 산출물은 내부 참조와 검증 결과를 확인하기 전에는 자동 이동하지 않는다.
4. Graphify의 Obsidian 내보내기는 `--obsidian-dir <project>/codebase-map/vault`로 지정한다. 기존 볼트의 직접 작성 노트와 `.obsidian` 설정은 보존한다. 볼트를 전체 소스 분석 대상에 다시 포함하지 않는다.
5. `.graphifyignore`에 `codebase-map/` 등 생성물 제외가 필요한지 확인해 재귀 분석을 막는다. Git에는 그래프의 공유할 데이터와 확정 다이어그램·볼트 노트만 프로젝트 정책에 따라 포함한다. 기기 절대경로, AST 캐시, 개인별 볼트 UI 상태는 제외한다.

## 완료 단계

별도의 애프터 스킬이 자동 발동하기를 기다리지 않는다. 이 스킬의 같은 실행에서 그래프 조회, 다이어그램 열기, 볼트 링크, 경로·제외 설정을 확인하고 실제 산출 위치와 미완료 항목을 보고한다. `docs/`와 `publish/`로 자동 복사하지 않는다.
