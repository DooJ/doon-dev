<p align="center">
  <img src="./assets/brand/doon-logo.svg" alt="DooN — DO:ON" width="720">
</p>

<p align="center"><strong>Understand the system. Change it with confidence.</strong></p>

<p align="center">
  <img src="./assets/brand/doon-hero.png" alt="DooN Development skill network" width="100%">
</p>

# DooN Development

**DooN Development**는 코드베이스 이해부터 구현, 리뷰, 오류 대응, 배포 관측까지 개발의 전체 흐름을 연결하는 공개 Codex·Claude Code 플러그인입니다. 플러그인 전체를 켜거나 끌 수 있으며, 설치 후 필요한 스킬만 개별적으로 활성화할 수 있습니다.

`DO:ON`의 두 원은 개발자의 판단과 에이전트의 실행을 뜻합니다. 코드 변경은 분석에서 시작해 검증과 운영 관측으로 닫히며, 각 스킬은 이 흐름의 한 단계를 명확하게 담당합니다.

## 포함된 스킬

| 스킬 | 설명 |
|---|---|
| `development-orchestrator` | 앱·웹·백엔드·디자인·QA가 섞인 복합 개발을 분리하고 통합합니다. |
| `feature-analyzer` | 코드에서 기능의 진입점, 상태, 데이터 흐름과 외부 연동을 역기획합니다. |
| `error-responder` | 크래시, 빌드·테스트 실패와 운영 장애의 원인과 재발 방지를 분석합니다. |
| `code-reviewer` | 변경 코드의 버그, 회귀, 보안·성능 위험과 테스트 누락을 리뷰합니다. |
| `code-commenting` | 공개 API와 복잡한 도메인 계약에 필요한 주석과 KDoc을 작성합니다. |
| `android-architecture` | Android 계층 구조, 생명주기, 상태와 데이터 흐름 기준을 제공합니다. |
| `kotlin-basics` | Kotlin의 타입, null-safety, 코루틴, 컬렉션과 네이밍 관례를 안내합니다. |
| `linear-qa` | Linear에서 테스트 케이스, 회귀 실행과 버그 재검증 흐름을 운영합니다. |
| `sentry-observability` | Sentry 릴리스 관측을 오류 분류, 이슈화와 수정 검증으로 연결합니다. |
| `skill-inspector` | 외부 에이전트 스킬의 권한, 출처와 악성 동작 위험을 설치 전에 점검합니다. |
| `skill-versioning` | 이 저장소의 스킬 버전, 출처, 내용 지문과 플러그인 버전을 검증합니다. |

## 동작 방식

1. 요청에 맞는 스킬이 코드와 프로젝트 상태를 읽습니다.
2. 분석, 구현, 리뷰, 오류 대응을 서로 독립된 책임으로 수행합니다.
3. 테스트와 검증 결과를 Linear, Sentry, Git 이력과 연결합니다.
4. 스킬 변경은 `VERSION.md`에 버전과 출처를 남깁니다.

모든 포함 스킬은 이 저장소 안의 지침과 자료만으로 동작합니다. 버전과 출처는 포함된 `skill-versioning`이 관리합니다.

## 설치와 설정

### Codex 설치

```bash
git clone https://github.com/DooJ/doon-dev.git
cd doon-dev
codex plugin marketplace add .
codex plugin add doon-dev@doon-dev
```

### Claude Code 설치

```bash
claude plugin marketplace add . --scope user
claude plugin install doon-dev@doon-dev --scope user
```

설치 후에는 새 Codex 또는 Claude Code 세션을 시작합니다.

### 개발·시험

Claude Code에서는 설치하지 않고 현재 checkout을 한 세션에서 바로 시험할 수도 있습니다.

```bash
claude plugin validate .
claude --plugin-dir "$PWD"
```

`--plugin-dir`는 해당 Claude 세션에만 적용됩니다.

### 최신화

```bash
git pull
codex plugin marketplace upgrade doon-dev
codex plugin add doon-dev@doon-dev
claude plugin marketplace update doon-dev
claude plugin update doon-dev@doon-dev --scope user
```

사용하지 않는 CLI의 명령은 생략할 수 있습니다. 갱신 후에는 새 세션을 시작합니다.

## 구조

- `.codex-plugin/plugin.json`: 플러그인 메타데이터와 `skills/` 등록
- `.claude-plugin/plugin.json`: Claude Code 네이티브 플러그인 메타데이터
- `skills/<이름>/`: 실제 스킬 원본, 버전, references, scripts, assets
- `catalog.json`: 저장소와 스킬 소유권을 확인하는 카탈로그
- `PLUGIN_VERSION.md`: 플러그인 단위 변경 이력과 출처
- `.agents/plugins/marketplace.json`: Codex 로컬 marketplace
- `.claude-plugin/marketplace.json`: Claude Code 로컬 marketplace

각 스킬의 구체적인 버전과 출처는 해당 폴더의 `VERSION.md`에서 확인할 수 있습니다. 이 저장소는 설치 대상 프로젝트에 별도 런타임 폴더를 생성하지 않습니다.
