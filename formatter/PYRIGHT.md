# Pyright Integration

Pyright는 `yngfmt`와 `ynglint`가 직접 구현하지 않는 프로젝트 수준의 타입 관계를 검사합니다.

## 역할 분리

- **Pyright**
  - 함수와 method의 반환 타입 검증
  - `TypedDict` field 누락 및 알 수 없는 field 검증
  - `dataclass` 기반 result object 생성 인자 검증
  - generic type 전달과 함수 간 반환 타입 추적
  - branch별 반환 타입 일관성 검증
- **ynglint**
  - raw result dictionary의 표준 field 구성 검사
  - 문서 고유 naming, blank line, import 규칙 검사
  - 타입만으로 표현할 수 없는 정적 코드 패턴 검사
- **Code review**
  - result와 exception의 책임 경계
  - logical stage 구분
  - architecture boundary와 semantic naming

## 기본 설정

formatter 패키지는 다음 설정으로 자체 코드를 검사합니다.

```toml
[tool.pyright]
include = ["src", "tests"]
pythonVersion = "3.11"
typeCheckingMode = "standard"
reportMissingTypeStubs = "none"
```

프로젝트에서는 include 경로와 Python version을 프로젝트 환경에 맞게 조정합니다.

## Result Object

구조화된 result object를 사용하면 Pyright가 field와 반환 타입을 검증할 수 있습니다.

```python
from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, TypeVar

T = TypeVar("T")


class ResultCode(StrEnum):
    SUCCESS = "SUCCESS"
    IGNORED = "IGNORED"
    FAILED = "FAILED"


@dataclass(slots=True)
class Result(Generic[T]):
    error: bool
    code: ResultCode
    message: str
    data: T | None = None
```

```python
def process() -> Result[str]:
    return Result(
        error=False,
        code=ResultCode.SUCCESS,
        message="Completed",
        data="value"
    )
```

Dictionary 호환이 필요하면 `TypedDict`를 사용합니다.

```python
from typing import Generic, TypeVar, TypedDict

T = TypeVar("T")


class ResultDict(TypedDict, Generic[T]):
    error: bool
    code: ResultCode
    message: str
    data: T | None
```

함수 반환 타입을 `Result[T]` 또는 `ResultDict[T]`로 명시해야 Pyright가 함수 간 타입 관계까지 추적할 수 있습니다. `dict[str, Any]`는 field 구성을 표현하지 못하므로 result object의 기본 반환 타입으로 사용하지 않습니다.

## 실행

```bash
cd formatter
python -m pip install -e ".[dev]"
pytest
pyright
```

GitHub Actions는 `pytest`와 `pyright`를 모두 실행하며 어느 하나라도 실패하면 CI를 실패시킵니다.
