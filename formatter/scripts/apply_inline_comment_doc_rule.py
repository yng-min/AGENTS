from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs/agents/python-style-guide.ko.md"
SUPPLEMENT = ROOT / "docs/agents/python-style-guide.inline-comment-spacing.ko.md"
SCRIPT = ROOT / "formatter/scripts/apply_inline_comment_doc_rule.py"
WORKFLOW = ROOT / ".github/workflows/apply-inline-comment-doc-rule.yml"


def main() -> None:
    content = GUIDE.read_text(encoding="utf-8")

    table_marker = (
        "| Dictionary literal spacing | 비어 있지 않은 single-line dictionary literal은 "
        "여는 중괄호 뒤와 닫는 중괄호 앞에 각각 **1 space**를 두며, "
        "빈 dictionary literal은 `{}`로 작성 |\n"
    )
    table_rule = (
        "| Inline comment spacing | 코드와 같은 줄에 작성하는 inline comment 앞에는 "
        "**1 space**를 둔다 |\n"
    )
    if table_rule not in content:
        content = content.replace(table_marker, table_marker + table_rule, 1)

    section_marker = "### 3.7 줄바꿈\n"
    inline_section = '''### 3.7 Inline Comment Spacing

코드와 같은 줄에 작성하는 inline comment 앞에는 **1 space**를 둔다.

이 규칙은 일반 설명 주석뿐 아니라 `# type: ignore`, `# noqa`, formatter directive처럼 코드 뒤에 붙는 모든 inline comment에 동일하게 적용한다.

Standalone comment는 코드와 같은 줄에 작성된 주석이 아니므로 이 spacing 규칙의 대상이 아니다.

> **설계 의도**
> 

> Inline comment와 코드 사이에 필요한 최소한의 경계만 유지하여 한 줄의 흐름을 지나치게 벌리지 않는다.
> 

> Black과 PEP 8의 일반적인 기본값은 inline comment 앞 2 spaces이지만, 본 스타일 가이드에서는 프로젝트 일관성을 위해 1 space를 우선한다.
> 

예시:

```python
value = 1 # 설명
result = process(data=data) # type: ignore[arg-type]
import plugin_b # yngfmt: keep-imports
```

Standalone comment는 기존 형태를 유지한다.

```python
# 처리할 데이터를 불러온다.
data = load_data()
```

### 3.8 줄바꿈
'''
    if "### 3.7 Inline Comment Spacing" not in content:
        content = content.replace(section_marker, inline_section, 1)

    automation_marker = (
        "| Basic Style | string quote style | formatter | Error | possible | Low |\n"
    )
    automation_rule = (
        "| Basic Style | inline comment spacing | formatter / linter | Error | possible | Low |\n"
    )
    if automation_rule not in content:
        content = content.replace(
            automation_marker,
            automation_marker + automation_rule,
            1,
        )

    GUIDE.write_text(content, encoding="utf-8")

    for path in (SUPPLEMENT, SCRIPT, WORKFLOW):
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    main()
