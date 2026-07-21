# yngmin Python Tooling

`docs/agents/python-style-guide.ko.md`를 기준으로 동작하는 Python formatter와 linter입니다.

- `yngfmt`: 안전하게 자동 수정 가능한 기계적 규칙 적용
- `ynglint`: 자동 수정이 부적절하지만 정적으로 판별 가능한 규칙 검사

## 설치

```bash
cd formatter
python -m pip install -e ".[dev]"
```

## Formatter

Black을 기본 엔진으로 사용하고, Black이 표현하지 못하는 개인 규칙은 LibCST로 후처리합니다.

```bash
yngfmt src tests
yngfmt --check src tests
yngfmt --line-length 100 src
```

자동 적용 규칙:

- 4 spaces 들여쓰기와 기본 spacing
- 일반 문자열의 큰따옴표
- docstring의 큰따옴표 3개
- dictionary key access의 작은따옴표
- 비어 있지 않은 single-line dictionary literal 내부 양쪽 1 space
- 빈 dictionary literal의 `{}` 형태
- Black이 안정적으로 처리하는 줄바꿈, trailing comma, blank line

```python
message = "hello"
user = { "name": "test", "enabled": True }
name = user['name']
empty_data = {}
```

## Linter

파일 또는 디렉터리를 전달합니다.

```bash
ynglint src tests
```

위반 사항이 있으면 다음 형식으로 출력하고 exit code `1`을 반환합니다.

```text
src/example.py:12:9: YNG103 dictionary key access must use single quotes
```

### 규칙 코드

| 코드 | 검사 내용 |
| --- | --- |
| `YNG000` | Python syntax error |
| `YNG001` | tab 사용 |
| `YNG101` | 일반 문자열에 작은따옴표 사용 |
| `YNG102` | docstring에 큰따옴표 3개 미사용 |
| `YNG103` | 문자열 key subscript에 작은따옴표 미사용 |
| `YNG201` | class 이름이 PascalCase가 아님 |
| `YNG202` | function 또는 method 이름이 snake_case가 아님 |
| `YNG203` | 명시적 bool 변수명에 상태 prefix가 없음 |
| `YNG301` | parameter type annotation 누락 |
| `YNG302` | return type annotation 누락 |
| `YNG401` | 같은 import 그룹에서 `import` 뒤에 `from` 사용 |
| `YNG402` | 같은 import 유형에서 root module 알파벳 정렬 위반 |

Import 검사는 빈 줄로 구분된 각 그룹 내부만 검사합니다. Standard library, third-party, first-party 판별과 내부 package segment grouping은 프로젝트 설정 없이는 정확하게 판별할 수 있으므로 현재 버전에서 강제하지 않습니다.

## 의도적으로 자동 판정하지 않는 규칙

다음 규칙은 실행 의미, 외부 API 관례 또는 프로젝트 책임 구조를 이해해야 하므로 자동 오류로 처리하지 않습니다.

- logical stage에 따른 body 내부 blank line
- 반복되는 독립 작업 사이의 blank line
- positional argument를 named argument로 바꿀지 여부
- 지역 변수 type hint가 실제로 필요한지 여부
- 설명적인 이름인지에 대한 의미 평가
- `dataclass`, `TypedDict`, `StrEnum`, dictionary 중 적절한 result object 선택
- architecture boundary와 변경 이유
- first-party root package 및 내부 segment grouping
- dictionary key 5개 이상에서 multi-line을 선택할지 여부

이 항목을 억지로 자동화하면 오탐이나 위험한 코드 변경이 발생하므로 code review 또는 프로젝트별 checker로 관리해야 합니다.

## 테스트

```bash
cd formatter
pytest
```

GitHub Actions에서도 formatter와 linter 테스트를 실행합니다.
