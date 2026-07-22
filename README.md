# AGENTS

개인 개발 철학과 Python 스타일 가이드를 실제 저장소 작업 흐름에 적용하기 위한 문서 및 도구 모음입니다.

## Repository tools

`yng-agents-tools`는 외부 런타임 의존성 없이 Python 저장소를 분석하는 CLI입니다.

### 설치

```bash
python -m pip install -e .
```

Python 3.11 이상이 필요합니다.

### 변경 영향 분석

파일, 함수, 클래스 또는 `path::symbol` 형식의 대상을 분석합니다.

```bash
agents-tools --root . impact src/example/service.py::process
```

다음 근거를 수집합니다.

- Python 정의와 호출 참조
- import 관계
- 관련 테스트 파일
- JSON, TOML, YAML 리소스 참조
- Markdown 및 reStructuredText 문서 참조
- 정적 분석이 확인한 관계의 신뢰 수준

결과는 `confirmed`, `probable`, `textual`, `unresolved`로 구분합니다. 동적 import, `getattr`, 런타임 의존성 주입처럼 정적으로 확정할 수 없는 관계를 완전한 호출 그래프로 표현하지 않습니다.

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
