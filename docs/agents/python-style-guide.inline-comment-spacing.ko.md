# Python Style Guide 보충 규칙: Inline Comment Spacing

> `python-style-guide.ko.md`의 기본 스타일 규칙에 포함될 inline comment spacing 규칙

## 규칙

코드와 같은 줄에 작성하는 inline comment 앞에는 **1 space**를 둔다.

```python
value = 1 # 설명
import plugin_b # yngfmt: keep-imports
```

다음처럼 2 spaces 이상을 사용하지 않는다.

```python
value = 1  # 설명
import plugin_b  # yngfmt: keep-imports
```

코드와 분리된 standalone comment에는 이 규칙을 적용하지 않는다.

```python
# 설명
value = 1
```

## 적용 범위

이 규칙은 다음 inline comment에 동일하게 적용한다.

- 일반 설명 comment
- `# yngfmt: keep-imports`
- `# type: ignore`
- `# noqa`
- 그 외 코드 뒤에 작성하는 모든 comment

## Formatter 정책

Black은 기본적으로 inline comment 앞에 2 spaces를 사용하지만, 본 스타일 가이드에서는 개인 컨벤션인 1 space를 우선한다.

따라서 formatter는 Black 적용 후 custom transform 단계에서 inline comment 앞 공백을 1 space로 정규화한다.

## 메인 문서 반영 문구

기본 스타일 표에는 다음 항목을 추가한다.

```markdown
| Inline comment spacing | 코드와 같은 줄에 작성하는 inline comment 앞에는 **1 space**를 둔다 |
```
