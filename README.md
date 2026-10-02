<p align="center">
  <img src="./assets/brand/doon-logo.svg" alt="DooN — DO:ON" width="720">
</p>

<p align="center"><strong>Understand the system. Change it with confidence.</strong></p>

<p align="center">
  <img src="./assets/brand/doon-hero.png" alt="DooN Development skill network" width="100%">
</p>

# DooN Development

**DooN Development**는 코드베이스 이해부터 구현, 리뷰, 오류 대응, 배포 관측까지 개발의 전체 흐름을 연결하는 공개 Codex·Claude Code·Antigravity 플러그인입니다. 설치 시 모든 스킬을 포함하며, 설치 후 사용하지 않을 스킬을 개별적으로 끌 수 있습니다.

스킬 묶음, 대표 개발 흐름과 운영 경계는 [플러그인 운영 안내](docs/README.md)에 정리했습니다.

`DO:ON`의 두 원은 개발자의 판단과 에이전트의 실행을 뜻합니다. 코드 변경은 분석에서 시작해 검증과 운영 관측으로 닫히며, 각 스킬은 이 흐름의 한 단계를 명확하게 담당합니다.

## 포함된 스킬

| 스킬 | 설명 |
|---|---|
| `development-orchestrator` | 앱·웹·백엔드·디자인·QA가 섞인 복합 개발을 분리하고 통합합니다. |
| `feature-analyzer` | 코드에서 기능의 진입점, 상태, 데이터 흐름과 외부 연동을 역기획합니다. |
| `error-responder` | 크래시, 빌드·테스트 실패와 운영 장애의 원인과 재발 방지를 분석합니다. |
| `code-reviewer` | 변경 코드의 버그, 회귀, 보안·성능 위험과 테스트 누락을 리뷰합니다. |
| `interface-contract` | 공개 API·모듈 경계의 소비자, 오류와 호환성 계약을 설계합니다. |
| `quality-constraints` | 큰 작업에서 기존 품질 기준선을 확인하고 검사 우회를 막습니다. |
| `deprecation-migration` | 소비자를 단계적으로 옮기고 옛 구현의 제거 조건을 확인합니다. |
| `performance-diagnostics` | 측정으로 병목을 찾고 같은 조건에서 개선 효과를 확인합니다. |
| `codegraph` | “코드그래프 세팅해”로 Graphify·Archify를 설치하고, “코드그래프 분석해/진행해”로 프로젝트의 그래프·다이어그램·Obsidian 볼트와 전체 버전·구성요소별 이력을 관리합니다. |
| `runtime-observability` | 운영 장애를 이해할 최소 로그·지표·트레이스를 설계합니다. |
| `code-commenting` | 공개 API와 복잡한 도메인 계약에 필요한 주석과 KDoc을 작성합니다. |
| `android-architecture` | Android 계층 구조, 생명주기, 상태와 데이터 흐름 기준을 제공합니다. |
| `kotlin-basics` | Kotlin의 타입, null-safety, 코루틴, 컬렉션과 네이밍 관례를 안내합니다. |
| `linear-qa` | Linear에서 테스트 케이스, 회귀 실행과 버그 재검증 흐름을 운영합니다. |
| `sentry-observability` | Sentry 릴리스 관측을 오류 분류, 이슈화와 수정 검증으로 연결합니다. |
| `skill-inspector` | 외부 에이전트 스킬의 권한, 출처와 악성 동작 위험을 설치 전에 점검합니다. |
| `dev-skill-versioning` | Development 저장소의 스킬 버전, 출처, 내용 지문과 플러그인 버전을 검증합니다. |

## 동작 방식

스킬은 설치 후 다음 명령으로 개별적으로 끄거나 다시 켭니다. 꺼진 스킬이 필요하면 같은 목적의 사용 가능한 스킬이나 도구를 선택합니다.

```bash
bash scripts/plugin.sh skills status
bash scripts/plugin.sh skills disable code-reviewer
bash scripts/plugin.sh skills enable code-reviewer
```

이 명령은 Codex와 Claude Code의 사용 설정을 갱신하며 새 세션에서 적용됩니다. Antigravity의 개별 스킬 차단은 검증 전입니다.

1. 요청에 맞는 스킬이 코드와 프로젝트 상태를 읽습니다.
2. 분석, 구현, 리뷰, 오류 대응을 서로 독립된 책임으로 수행합니다.
3. 테스트와 검증 결과를 Linear, Sentry, Git 이력과 연결합니다.
4. 스킬 변경은 `VERSION.md`에 버전과 출처를 남깁니다.

모든 포함 스킬은 이 저장소 안의 지침과 자료만으로 동작합니다. 버전과 출처는 포함된 `dev-skill-versioning`이 관리합니다.

## 설치와 설정

```bash
git clone https://github.com/DooJ/doon-dev.git
cd doon-dev
bash scripts/plugin.sh install
```

관리 스크립트가 컴퓨터에 설치된 Codex, Claude Code, Antigravity를 자동으로 찾아 각각 필요한 형식으로 설치합니다. 설치되지 않은 에이전트는 건너뜁니다. 같은 플러그인이 다른 마켓플레이스로 이미 설치되어 있으면 중복 설치하지 않습니다.

### 관리 명령

| 목적 | 명령 |
|---|---|
| 설치·에이전트 설정 | `bash scripts/plugin.sh install` |
| 설정 다시 적용 | `bash scripts/plugin.sh setup` |
| Git과 모든 에이전트 최신화 | `bash scripts/plugin.sh update` |
| 현재 파일로 설치 복구 | `bash scripts/plugin.sh repair` |
| 패키지·버전·테스트 검증 | `bash scripts/plugin.sh test` |
| Git·에이전트 상태 확인 | `bash scripts/plugin.sh status` |

특정 에이전트를 제외하려면 설치·설정·최신화·복구 명령에 `--skip-codex`, `--skip-claude`, `--skip-antigravity`를 붙입니다. 적용 후에는 해당 에이전트의 새 세션을 시작합니다.

## 구조

- `.codex-plugin/plugin.json`: 플러그인 메타데이터와 `skills/` 등록
- `.claude-plugin/plugin.json`: Claude Code 네이티브 플러그인 메타데이터
- `antigravity/plugin.json`: Antigravity 전용 manifest
- `scripts/build_antigravity_plugin.py`: 설치 가능한 Antigravity 패키지 생성기
- `scripts/plugin.sh`: 설치, 설정, 최신화, 복구, 테스트 통합 명령
- `skills/<이름>/`: 실제 스킬 원본, 버전, references, scripts, assets
- `catalog.json`: 저장소와 스킬 소유권을 확인하는 카탈로그
- `PLUGIN_VERSION.md`: 플러그인 단위 변경 이력과 출처
- `.agents/plugins/marketplace.json`: Codex 로컬 marketplace
- `.claude-plugin/marketplace.json`: Claude Code 로컬 marketplace

각 스킬의 구체적인 버전과 출처는 해당 폴더의 `VERSION.md`에서 확인할 수 있습니다. 이 저장소는 설치 대상 프로젝트에 별도 런타임 폴더를 생성하지 않습니다.
