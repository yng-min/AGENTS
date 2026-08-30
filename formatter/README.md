# yngmin Python Tooling

`docs/agents/python-style-guide.ko.md`의 v4 (260726) 규칙을 기준으로 동작하는 Python formatter와 linter입니다.

- `yngfmt`: 안전하게 자동 수정 가능한 기계적 규칙 적용
- `ynglint`: 자동 수정이 부적절하지만 정적으로 확정 가능한 규칙 검사

## 설치

```bash
cd formatter
python -m pip install -e ".[dev]"
```

## 프로젝트 설정

프로젝트의 `pyproject.toml`에 first-party root package를 지정합니다.

```toml
[tool.yngfmt.imports]
first-party = ["project"]
language-segment = "language"
config-segment = "config"
```

`yngfmt`와 `ynglint`는 대상 파일에서 가장 가까운 `pyproject.toml`을 자동 탐색합니다. 다른 설정 파일을 사용하려면 `--pyproject`로 명시합니다.

```bash
yngfmt --pyproject path/to/pyproject.toml src
ynglint --pyproject path/to/pyproject.toml src
```

## Formatter

Black을 기본 엔진으로 사용하고, Black이 표현하지 못하는 개인 규칙은 LibCST와 전용 import sorter로 후처리합니다.

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
- 코드와 같은 줄에 작성하는 inline comment 앞 1 space
- Black이 안정적으로 처리하는 기본 spacing과 trailing comma
- Standard library → third-party → first-party import 그룹 순서
- 각 import 그룹 내부에서 `from` 문을 `import` 문보다 위에 배치
- root module 알파벳순과 같은 root 내부 module depth 정렬
- first-party root 다음 segment를 기준으로 동적 그룹화
- `language` segment를 first-party 그룹 최상단에 배치
- `config` segment를 first-party 그룹 최하단에 배치하고 앞에 blank line 2개 사용
- import 그룹과 본문 사이 blank line 2개 유지

```python
message = "hello"
user = { "name": "test", "enabled": True }
name = user['name']
empty_data = {}
value = 1 # explanation
```

Inline comment spacing은 일반 comment뿐 아니라 `# type: ignore`, `# noqa`, formatter directive에도 동일하게 적용합니다. standalone comment에는 적용하지 않습니다.

```python
result = process(data=data) # type: ignore[arg-type]
import plugin_b # yngfmt: keep-imports

# standalone comment
value = 1
```

### Formatter와 semantic line breaking

260726 가이드는 function call의 줄바꿈을 고정 line length가 아니라 expression 구조와 처리 단계로 판단합니다.

`yngfmt`는 Black을 기본 엔진으로 사용하므로 Black이 수행하는 일반 formatting은 유지하지만, semantic 판단이 필요한 줄바꿈을 formatter가 임의로 강제하는 source of truth로 취급하지 않습니다. 확실하게 판정 가능한 call layout 위반은 `ynglint`가 별도로 검사합니다.

Docstring의 opening/closing delimiter를 각각 독립된 줄에 두는 canonical layout도 formatter가 자동 변환하지 않습니다. `"""Summary."""`를 `"""\nSummary.\n"""`로 바꾸면 런타임 `__doc__` 문자열 자체가 달라질 수 있으므로, 이 규칙은 안전한 자동 수정 대신 linter error로 처리합니다.

Import 정렬 예시:

```python
from pathlib import Path
import json

from pydantic import BaseModel

from project.language.i18n import translate

from project.application.service import Service

from project.domain.article import Article

from project.infrastructure.database import Database


from project.config.runtime import runtime_config


class Application:
    ...
```

multiline import와 inline comment는 원문과 함께 이동합니다. 다음 코드는 자동 재배치하지 않습니다.

- 함수 또는 class 내부 import
- `if`, `try`, `TYPE_CHECKING` 등 조건부 block 내부 import
- 처음 나타나는 연속 top-level import section 이후의 지연 import

### Import 정렬 제외 directive

단독 `# yngfmt: keep-imports`는 blank line 없이 바로 이어지는 import 블록의 순서를 유지합니다.

```python
# yngfmt: keep-imports
import plugin_b
import plugin_a
```

directive와 import 사이에 blank line이 있으면 효과가 종료됩니다.

```python
# yngfmt: keep-imports

import plugin_b
import plugin_a
```

import 문 뒤에 inline으로 작성하면 해당 import 한 줄만 현재 위치에 고정됩니다. 고정된 줄의 앞뒤 import는 각각 독립적으로 정렬합니다.

```python
import requests
import plugin_b # yngfmt: keep-imports
import json
from pathlib import Path
```

`# yngfmt: off`와 `# yngfmt: on` 사이의 import는 원래 순서를 유지합니다.

```python
# yngfmt: off
import plugin_b
import plugin_a
# yngfmt: on
```

파일 전체의 import 정렬을 제외하려면 `# yngfmt: skip-file`을 단독 줄로 사용합니다.

```python
# yngfmt: skip-file
```

## Linter

파일 또는 디렉터리를 전달합니다.

```bash
ynglint src tests
```

위반 사항이 있으면 다음 형식으로 출력하고 error가 하나 이상이면 exit code `1`을 반환합니다.

```text
src/example.py:12:9: YNG103 dictionary key access must use single quotes
```

### 규칙 코드

| 코드 | 검사 내용 |
| --- | --- |
| `YNG000` | Python syntax error |
| `YNG001` | tab 사용 |
| `YNG101` | 일반 문자열 또는 f-string에 작은따옴표 사용 |
| `YNG102` | docstring에 큰따옴표 3개 미사용 |
| `YNG103` | 문자열 key subscript에 작은따옴표 미사용 |
| `YNG104` | module docstring 뒤 blank line이 정확히 1개가 아님 |
| `YNG105` | class docstring과 첫 body 사이에 blank line 존재 |
| `YNG106` | function/method docstring과 body 사이에 blank line 존재 |
| `YNG107` | docstring opening `"""`와 첫 내용이 같은 줄에 존재 |
| `YNG108` | docstring closing `"""`가 독립된 줄에 있지 않음 |
| `YNG109` | single-line dictionary literal의 내부 spacing이 canonical 형태가 아님 |
| `YNG201` | class 이름이 PascalCase가 아님 |
| `YNG202` | function 또는 method 이름이 snake_case가 아님 |
| `YNG301` | parameter type annotation 누락 |
| `YNG302` | return type annotation 누락 |
| `YNG400` | 전체 import section이 canonical project import ordering과 다름 |
| `YNG401` | top-level definition 앞 blank line이 2개가 아님 |
| `YNG402` | class method 사이 blank line이 1개가 아님 |
| `YNG403` | function/method 선언 직후 불필요한 blank line 존재 |
| `YNG501` | 짧은 wrapper의 준비 호출과 delegation return 사이 blank line 존재 |
| `YNG502` | 직전 assignment가 만든 값을 바로 return하면서 blank line 존재 |
| `YNG601` | result object의 required field 누락 |
| `YNG602` | result object에서 비표준 alias field 사용 |
| `YNG603` | 동일 function의 result return branch 간 field set 불일치 |
| `YNG701` | 단순한 단일 인자 call을 불필요하게 multi-line으로 작성 |
| `YNG702` | multi-line call의 마지막 argument 뒤 trailing comma 누락 |
| `YNG703` | single-line call에 trailing comma 사용 |
| `YNG704` | zero-argument call을 multi-line으로 작성 |

Formatter와 linter는 같은 canonical import sorter를 사용하므로 서로 다른 import 정렬 결과를 만들지 않습니다.

### 260726에서 추가로 기계 검증하는 범위

다음 규칙은 의미 판단 없이 source structure만으로 확정할 수 있어 linter error로 처리합니다.

- 모든 docstring의 opening delimiter 뒤에서 내용을 다음 줄에 시작
- 모든 docstring의 closing delimiter를 독립된 줄에 배치
- formatter가 이미 수정하는 single-line dictionary spacing을 lint-only 환경에서도 검증
- 단순 값/참조 하나만 받는 call은 single-line 유지
- nested call, collection, comprehension, conditional/binary/boolean expression, lambda, multi-line string, `*args`, `**kwargs`처럼 자체 구조를 가진 단일 인자는 multi-line 허용
- argument 내부에 설명 comment가 있으면 단순 단일 인자라도 multi-line 허용
- multi-line call은 마지막 argument 뒤 trailing comma 필수
- generator expression 단독 call은 Python 문법 특성상 trailing comma 검사에서 제외
- single-line call은 trailing comma 금지
- zero-argument call은 single-line 유지

## 의도적으로 자동 판정하지 않는 규칙

다음 규칙은 실행 의미, 외부 API 관례 또는 프로젝트 책임 구조를 이해해야 하므로 자동 오류로 처리하지 않습니다.

- logical stage에 따른 body 내부 blank line
- 반복되는 독립 작업 사이의 blank line
- 일반적인 positional argument를 named argument로 바꿀지 여부
- boolean literal positional argument의 named argument 전환 여부: 외부/표준 라이브러리 API 관례 예외가 존재함
- 지역 변수 type hint가 실제로 필요한지 여부
- 설명적인 이름인지에 대한 의미 평가
- `_config` suffix가 실제 설정 데이터 객체에 해당하는지 여부
- `dataclass`, `TypedDict`, `StrEnum`, dictionary 중 적절한 result object 선택
- Result와 exception 중 어떤 실패 표현이 맞는지 여부
- architecture boundary와 변경 이유
- dictionary key 5개 이상에서 multi-line을 선택할지 여부
- 복잡한 expression을 어느 의미 경계에서 줄바꿈할지 여부

이 항목을 억지로 자동화하면 오탐이나 위험한 코드 변경이 발생하므로 agent/code review 또는 프로젝트별 의미 검증으로 관리해야 합니다.

## 테스트

```bash
cd formatter
pytest
pyright
```

GitHub Actions에서도 formatter와 linter 테스트, Pyright를 실행합니다.
