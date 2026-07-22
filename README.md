# AGENTS

개인 개발 철학과 Python 스타일 가이드를 실제 저장소 작업 흐름에 적용하기 위한 문서 및 도구 모음입니다.

## Repository tools

`yng-agents-tools`는 기본 기능을 외부 의존성 없이 제공하고, 필요할 때 로컬 분석기를 선택적으로 연결하는 Python 저장소 분석 CLI입니다.

### 설치

기본 AST 분석만 사용할 경우:

```bash
python -m pip install -e .
```

선택적 분석기를 함께 설치할 경우:

```bash
python -m pip install -e ".[imports,types,patterns]"
```

또는 모든 선택 기능을 설치합니다.

```bash
python -m pip install -e ".[full]"
```

Python 3.11 이상이 필요합니다.

### 분석 구조

외부 도구는 최종 판단자가 아니라 저장소 근거를 제공하는 adapter로만 동작합니다.

- built-in AST: 항상 실행 가능한 core 분석
- Grimp: import graph 근거 보강
- Pyright: 타입 진단 근거 보강
- Semgrep: 저장소가 소유한 로컬 규칙 결과 보강

외부 도구의 타입과 결과 형식은 core에 노출하지 않습니다. 모든 결과는 `Evidence`, `Reference`, `AdapterReport`로 정규화하며, adapter가 설치되지 않았거나 실패해도 built-in 분석은 계속 실행됩니다.

Semgrep은 원격 `auto` 규칙을 사용하지 않습니다. `.semgrep.yml`, `.semgrep.yaml`, `semgrep.yml`, `semgrep.yaml` 중 저장소에 존재하는 로컬 설정만 실행합니다.

지원 adapter 목록:

```bash
agents-tools adapters list
```

### 변경 영향 분석

파일, 함수, 클래스 또는 `path::symbol` 형식의 대상을 분석합니다.

```bash
agents-tools --root . impact src/example/service.py::process
```

선택적 adapter를 추가할 수 있습니다.

```bash
agents-tools --root . --adapter grimp --adapter pyright impact src/example/service.py::process
```

모든 adapter를 시도할 수도 있습니다.

```bash
agents-tools --root . --adapter all impact src/example/service.py::process
```

다음 근거를 수집합니다.

- Python 정의와 호출 참조
- import 관계
- 관련 테스트 파일
- JSON, TOML, YAML 리소스 참조
- Markdown 및 reStructuredText 문서 참조
- adapter가 제공한 import, 타입, 규칙 위반 근거
- adapter별 실행 상태와 버전
- 정적 분석이 확인한 관계의 신뢰 수준

결과는 `confirmed`, `probable`, `textual`, `unresolved`로 구분합니다. 동적 import, `getattr`, 런타임 의존성 주입처럼 정적으로 확정할 수 없는 관계를 완전한 호출 그래프로 표현하지 않습니다.

adapter 상태는 다음으로 구분합니다.

- `available`: 분석 완료
- `skipped`: 실행 조건이 없어 의도적으로 생략
- `unavailable`: 도구가 설치되지 않음
- `failed`: 도구 실행 또는 결과 해석 실패

### 문서 동기화 검사

현재 브랜치와 기준 브랜치의 diff를 분석해 업데이트가 필요할 가능성이 있는 문서를 찾습니다.

```bash
agents-tools --root . docs check --base main
```

현재 MVP는 다음 변경을 탐지합니다.

- 설정 및 환경변수
- 배포와 운영 파일
- Python 공개 구조와 callable
- 데이터 구조와 데이터베이스 관련 코드

도구는 문서를 자동 수정하지 않습니다. 변경 근거와 신뢰 수준을 제시해 개발자가 수정 범위를 결정하도록 합니다.

## 검증

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```

## Required agent documents

모든 작업 전 다음 문서를 전문으로 읽고 적용해야 합니다.

- `docs/agents/python-style-guide.ko.md`
- `docs/agents/decision-making-principles.ko.md`
