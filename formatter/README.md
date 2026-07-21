# yngmin Python Formatter

`docs/agents/python-style-guide.ko.md`에서 안전하게 자동화할 수 있는 규칙을 적용하는 Python formatter입니다.

Black을 기본 포맷팅 엔진으로 사용하고, Black이 표현할 수 없는 개인 규칙은 LibCST 기반 후처리로 적용합니다.

## 적용 규칙

- 4 spaces 들여쓰기 및 tab 제거
- 일반 문자열의 큰따옴표 사용
- docstring의 큰따옴표 3개 사용
- dictionary key access의 작은따옴표 사용
- 비어 있지 않은 single-line dictionary literal 내부 양쪽 1 space
- 빈 dictionary literal의 `{}` 형태
- Black이 안정적으로 처리하는 기본 spacing, 줄바꿈, trailing comma 및 blank line 규칙

```python
message = "hello"
user = { "name": "test", "enabled": True }
name = user['name']
empty_data = {}
```

## 의도적으로 자동화하지 않는 규칙

다음 규칙은 의미 또는 프로젝트 구조를 판단해야 하므로 formatter가 수정하지 않습니다.

- logical stage에 따른 body 내부 blank line
- 반복되는 독립 작업 사이의 blank line
- named argument 사용 여부
- type hint 필요 여부
- naming 및 result object convention
- architecture boundary
- first-party package와 내부 segment를 판단해야 하는 import grouping

이 항목은 향후 별도 linter 또는 checker로 검증하는 편이 안전합니다.

## 설치

```bash
cd formatter
python -m pip install -e .
```

개발 의존성까지 설치하려면 다음 명령을 사용합니다.

```bash
python -m pip install -e ".[dev]"
```

## 사용

파일 또는 디렉터리를 전달합니다.

```bash
yngfmt path/to/file.py src tests
```

변경 여부만 검사하려면 `--check`를 사용합니다.

```bash
yngfmt --check src tests
```

기본 Black line length는 88이며 필요한 경우 변경할 수 있습니다.

```bash
yngfmt --line-length 100 src
```

## 테스트

```bash
cd formatter
pytest
```

## 처리 순서

1. Black으로 문법적으로 안전한 기본 포맷팅을 수행합니다.
2. LibCST로 syntax tree와 주석을 보존하면서 개인 규칙을 적용합니다.
3. `--check`가 아니면 변경된 파일만 UTF-8로 저장합니다.

Formatter는 같은 입력에 반복 실행해도 결과가 더 이상 바뀌지 않는 idempotent 동작을 목표로 합니다.
