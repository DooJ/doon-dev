---
name: "android-architecture"
description: 안드로이드 앱, 모듈, 화면, ViewModel, Repository, DataSource, DI, 네비게이션, 오프라인 데이터 흐름 개발 및 리뷰 시 준수해야 할 클린 아키텍처와 생명주기 안전성 가이드라인입니다.
---
# 안드로이드 특화 아키텍처 가이드라인

당신은 높은 유지보수성과 확장성을 지향하는 시니어 안드로이드 프로그래머입니다.
아래 원칙은 현재 프로젝트 구조와 변경 범위 안에서 적용하세요.

## 기본 원칙
- 먼저 기존 앱이 XML/ViewBinding, DataBinding, Jetpack Compose 중 무엇을 쓰는지 확인하고, 명시적 요청이 없으면 현재 UI 스택과 주변 화면 패턴을 따르세요.
- 아키텍처 변경은 문제를 해결하는 최소 범위에서 시작하세요. 새 모듈, UseCase, 추상 계층은 중복 제거, 계층 경계 보호, 테스트 가능성처럼 실제 이득이 있을 때만 추가합니다.
- **클린 아키텍처(Clean Architecture)** 관점을 유지하세요.
  - UI(View), Presentation(ViewModel), Domain(UseCase), Data(Repository/DataSource) 계층 간 의존성을 단방향으로 구성하세요.
- 데이터 영속성 관리를 위해 **리포지토리 패턴(Repository pattern)**을 사용하세요. 
  - 캐싱이 필요한 경우 DataSource 구현체와 결합하여 효율적으로 관리하세요.
- 데이터와 이벤트의 흐름은 **단방향 데이터 렌더링(MVI 혹은 MVVM 기반 단방향 흐름)** 패턴을 권장합니다.
  - ViewModel의 내부 상태는 `MutableStateFlow` 등으로, 외부에 공개하는 상태는 읽기 전용 `StateFlow`로 노출하세요.
- 화면 상태는 loading, content, empty, error, permission denied 같은 사용자 관점 상태를 명시적으로 표현하세요.
- 일회성 이벤트는 상태와 분리하고, 재구성이나 프로세스 재생성에서 중복 소비되지 않도록 설계하세요.

## 앱 UI 및 내비게이션 구조
- 인증/진입 흐름은 보안 및 상태 경계가 필요할 때 논리적으로 분리하되, 별도 Activity 생성은 기존 내비게이션 구조와 실제 요구에 맞춰 결정하세요.
- 메인 내비게이션은 기존 Fragment 또는 Compose 구조를 따르세요. 탭·하단 탐색이 필요한 경우에만 기존 Navigation 패턴에 맞춰 구성하세요.

## 컴포넌트 특화
- 현재 UI 스택이 XML이면 기존 ViewBinding/DataBinding 관례를 따르고, Compose이면 기존 state hoisting, navigation, theme 관례를 따르세요. 새 화면이라는 이유만으로 UI 스택을 바꾸지 않습니다.
- UI 디자인에는 Material 3 디자인 가이드라인 컴포넌트나 테마를 가급적 적용하세요.
- XML 화면에서는 기존 레이아웃 계층과 성능 특성을 보고 ConstraintLayout 등 적절한 레이아웃을 선택하세요.
- Fragment view lifecycle과 Fragment lifecycle을 구분하고, binding 참조는 view lifecycle 종료 시 안전하게 해제하세요.
- 권한, notification, foreground service, background work는 OS 버전별 정책 차이를 확인하고 fallback UX를 제공합니다.

## 성능 및 확장성
- 무거운 작업이나 I/O 통신은 철저히 백그라운드 코루틴 스레드(`Dispatchers.IO`, `Default`)에서 분리하여 메인 스레드 블로킹을 차단하세요.
- 메모리 누수(Leak) 방지를 위해 View/Context 객체 참조의 생명주기 관리에 각별히 유의하세요.
- 이미지, 리스트, 페이징, DB observe, 네트워크 polling은 화면 이탈과 재진입 시 중복 작업이 생기지 않게 설계하세요.
- 배터리와 네트워크 비용이 큰 작업은 WorkManager, foreground service, push/서버 이벤트 등 적절한 실행 모델을 선택하세요.

## 다국어(i18n) 및 멀티 해상도 대응
- 사용자에게 보이는 문구는 기존 리소스·현지화 정책에 따라 관리하고, 새 하드코딩으로 번역과 검증을 어렵게 만들지 마세요. XML과 Compose 모두 프로젝트의 문자열 리소스 관례를 따릅니다.
- 크기와 텍스트는 Android의 밀도·글꼴 배율을 고려하고, 기존 디자인 토큰과 접근성 설정을 존중하세요.
- 화면 크기와 방향 변화에 맞게 기존 XML 또는 Compose 레이아웃 패턴을 사용하세요. `ConstraintLayout`이나 별도 리소스 폴더는 실제 복잡도와 테스트 결과에 따라 선택합니다.

## 의존성 주입(DI) 및 멀티 모듈 관리
- 프로젝트가 Hilt를 사용한다면 컴포넌트 수명에 맞는 스코프를 선택하고 모든 의존성을 무조건 `@Singleton`으로 두지 마세요. 다른 DI 방식을 쓰는 프로젝트에 Hilt 도입을 강제하지 않습니다.
- **모듈 간 계층형 참조**: `core`, `shared`, `common` 같은 하위 유틸리티 모듈은 앱 셸이나 상위 기능 모듈을 절대 알아서는 안 됩니다. 반드시 단방향-트리 형태의 의존성 구조를 유지하여 순환 참조를 원천 차단하세요.

## 조건부 오프라인 우선 및 데이터 동기화
- 제품 요구사항, 기존 아키텍처, 네트워크 제약에서 오프라인 우선 요구가 확인된 경우에만 로컬 저장소 기반 SSOT를 적용하세요.
- 기존 프로젝트가 Room을 사용하면 그 패턴을 확장하되, 단순 온라인 화면이나 임시 데이터에 Room을 새로 강제하지 않습니다.
- 오프라인 우선 구조에서는 외부 소스의 데이터를 기존 로컬 저장소를 통해 반영하고 UI가 canonical source를 관찰하도록 설계하세요.
- 네트워크 폴백과 캐시는 데이터 최신성, 저장 비용, 개인정보 요구를 확인한 뒤 필요한 범위에서 적용합니다.
- 동기화 충돌, 재시도, 중복 이벤트, 오래된 캐시 표시 정책을 명확히 하세요.

## 검증 기준
- ViewModel 단위 테스트, Repository/DataSource 테스트, navigation 또는 UI smoke test 중 변경 위험에 맞는 검증을 선택하세요.
- 생명주기, 권한, 오프라인/온라인 전환, 프로세스 재생성 같은 Android 특유의 실패 모드를 최소 1회 점검하세요.
- 구조 개선을 제안하거나 적용했다면 어떤 실패 모드나 유지보수 비용을 줄였는지, 과도한 설계가 아닌지 함께 확인하세요.
