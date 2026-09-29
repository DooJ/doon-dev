<p align="center">
  <img src="./assets/brand/doon-logo.svg" alt="DooN — DO:ON" width="720">
</p>

<p align="center"><strong>Understand the system. Change it with confidence.</strong></p>

<p align="center">
  <img src="./assets/brand/doon-hero.png" alt="DooN Development skill network" width="100%">
</p>

# DooN Development

**DooN Development**는 코드베이스 이해부터 구현, 리뷰, 오류 대응, 배포 관측까지 개발의 전체 흐름을 연결하는 공개 Codex·Claude Code 플러그인입니다. 플러그인 전체를 켜거나 끌 수 있으며, 설치 후 필요한 스킬만 개별적으로 활성화할 수 있습니다.

`DO:ON`의 두 코어는 개발자의 판단과 에이전트의 실행을 뜻합니다. 코드 변경은 분석에서 시작해 검증과 운영 관측으로 닫히며, 각 스킬은 이 흐름의 한 단계를 명확하게 담당합니다.

## 포함된 스킬

| 영역 | 스킬 |
|---|---|
| 개발 오케스트레이션 | `development-orchestrator`, `feature-analyzer` |
| 구현 품질 | `code-commenting`, `code-reviewer`, `error-responder` |
| 플랫폼 | `android-architecture`, `kotlin-basics` |
| 운영 연결 | `linear-qa`, `sentry-observability` |
| 스킬 품질 | `skill-inspector` |

## 동작 방식

1. 요청에 맞는 스킬이 코드와 프로젝트 상태를 읽습니다.
2. 분석, 구현, 리뷰, 오류 대응을 서로 독립된 책임으로 수행합니다.
3. 테스트와 검증 결과를 Linear, Sentry, Git 이력과 연결합니다.
4. 스킬 변경은 `VERSION.md`에 버전과 출처를 남깁니다.

모든 포함 스킬은 Core 없이 동작합니다. DooN 원본의 버전·출처 관리는 Core 플러그인이 소유하는 `skill-versioning`이 담당합니다.

## 설치와 설정

### DooN Core와 함께 설치

여러 DooN 플러그인을 함께 사용할 때 권장하는 방식입니다. GitHub CLI에 로그인한 뒤 Core를 clone하고 bootstrap을 한 번 실행합니다.

```bash
gh auth login
git clone https://github.com/DooJ/doon-core.git DooN
cd DooN
bash scripts/bootstrap_doon.sh
```

처음 설치하면서 `doon-dev`만 고르려면 마지막 명령에 `--interactive`를 붙이고, 이 저장소는 전체 선택하고 나머지는 건너뜁니다. bootstrap은 Codex에 플러그인을 설치하고 Claude Code가 있으면 Claude에도 설치합니다. 완료 후 새 Codex 또는 Claude 세션을 시작하면 되며, 작업 프로젝트에 `.doon`을 복사할 필요는 없습니다.

이후 소스와 Codex·Claude 설치 상태를 함께 최신화하려면 Core에서 bootstrap을 다시 실행합니다. 기존 플러그인 선택은 그대로 유지됩니다.

```bash
cd /path/to/DooN
bash scripts/bootstrap_doon.sh
```

### 이 저장소만 개발·시험

Core 없이 소스만 확인하거나 Claude Code에서 바로 시험할 수 있습니다.

```bash
git clone https://github.com/DooJ/doon-dev.git
cd doon-dev
claude plugin validate .
claude --plugin-dir "$PWD"
```

`--plugin-dir`는 해당 Claude 세션에만 적용됩니다. Codex에 지속 설치하려면 이 저장소를 가리키는 marketplace 항목이 필요하며, DooN 사용 환경에서는 위 Core bootstrap이 그 항목과 설치 상태를 자동으로 관리합니다. 별도 환경에서는 조직 또는 개인 marketplace에 `doon-dev`를 등록한 뒤 `codex plugin add doon-dev@your-marketplace`로 설치합니다.

## 구조

- `.codex-plugin/plugin.json`: 플러그인 메타데이터와 `skills/` 등록
- `.claude-plugin/plugin.json`: Claude Code 네이티브 플러그인 메타데이터
- `skills/<이름>/`: 실제 스킬 원본, 버전, references, scripts, assets
- `catalog.json`: 저장소와 스킬 소유권을 확인하는 카탈로그
- `PLUGIN_VERSION.md`: 플러그인 단위 변경 이력과 출처

일부 스킬은 DooN의 공통 규칙, 워크플로우 또는 런타임을 참조합니다. 각 스킬의 구체적인 버전과 출처는 해당 폴더의 `VERSION.md`에서 확인할 수 있습니다.

> 이 저장소는 DooN Core 없이 독립 실행할 수 있으며 프로젝트에 `.doon`을 생성하지 않습니다. Core 사용자는 이 플러그인을 동일한 plugin ID로 통합 관리합니다.
