# yngmin Python Tooling

`docs/agents/python-style-guide.ko.md`를 기준으로 동작하는 Python formatter와 linter입니다.

- `yngfmt`: 안전하게 자동 수정 가능한 기계적 규칙 적용
- `ynglint`: 자동 수정이 부적절하지만 정적으로 판별 가능한 규칙 검사

## 설치

```bash
cd formatter
python -m pip install -e ".[dev]"
```

## 프로젝트 설정

프로젝트의 `pyproject.toml`에 first-party root package를 지정합니다.

```toml
[tool.yngfmt.imports]
first-party = ["helpmate"]
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
- Black이 안정적으로 처리하는 줄바꿈, trailing comma, blank line
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
```

Import 정렬 예시:

```python
from pathlib import Path
import json

from pydantic import BaseModel

from helpmate.language.i18n import translate

from helpmate.application.service import Service

from helpmate.domain.article import Article

from helpmate.infrastructure.database import Database


from helpmate.config.runtime import runtime_config


class Application:
    ...
```

multiline import와 inline comment는 원문과 함께 이동합니다. 다음 코드는 자동 재배치하지 않습니다.

- 함수 또는 class 내부 import
- `if`, `try`, `TYPE_CHECKING` 등 조건부 block 내부 import
- 처음 나타나는 연속 top-level import section 이후의 지연 import

import 순서 자체가 runtime 동작에 영향을 주는 파일은 다음 directive로 제외할 수 있습니다.

```python
# yngfmt: keep-imports
import plugin_b
import plugin_a
```

파일 전체 formatter 제외 구간에 `# yngfmt: off`가 존재하는 경우에도 import 자동 정렬을 수행하지 않습니다.

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
| `YNG400` | 전체 import section이 canonical project import ordering과 다름 |

Formatter와 linter는 같은 canonical import sorter를 사용하므로 서로 다른 정렬 결과를 만들지 않습니다.

## 의도적으로 자동 판정하지 않는 규칙

다음 규칙은 실행 의미, 외부 API 관례 또는 프로젝트 책임 구조를 이해해야 하므로 자동 오류로 처리하지 않습니다.

- logical stage에 따른 body 내부 blank line
- 반복되는 독립 작업 사이의 blank line
- positional argument를 named argument로 바꿀지 여부
- 지역 변수 type hint가 실제로 필요한지 여부
- 설명적인 이름인지에 대한 의미 평가
- `dataclass`, `TypedDict`, `StrEnum`, dictionary 중 적절한 result object 선택
- architecture boundary와 변경 이유
- dictionary key 5개 이상에서 multi-line을 선택할지 여부

이 항목을 억지로 자동화하면 오탐이나 위험한 코드 변경이 발생하므로 code review 또는 프로젝트별 checker로 관리해야 합니다.

## 테스트

```bash
cd formatter
pytest
```

GitHub Actions에서도 formatter와 linter 테스트를 실행합니다.
