"""
Tests for style guide linter rules.
"""

from pathlib import Path

from yngfmt.linter import lint_code


def _codes(source: str) -> list[str]:
    return [diagnostic.code for diagnostic in lint_code(source=source, path=Path("test.py"))]


def test_accepts_core_style_rules() -> None:
    source = '''"""
Module description.
"""

from pathlib import Path
import json


class ExampleService:
    """
    Example service.
    """
    def get_value(self, data: dict[str, str]) -> str:
        is_enabled: bool = True
        value = data['name']
        return value if is_enabled else ""
'''.lstrip()

    assert _codes(source) == []


def test_reports_quote_and_key_access_rules() -> None:
    source = "message = 'hello'\nvalue = data[\"name\"]\n"

    assert _codes(source) == ["YNG101", "YNG103"]


def test_reports_naming_and_type_annotation_rules() -> None:
    source = "class bad_name:\n    def GetValue(self, value):\n        return value\n"

    assert _codes(source) == ["YNG201", "YNG202", "YNG302", "YNG301"]


def test_reports_boolean_naming_rule() -> None:
    assert _codes("enabled: bool = True\n") == ["YNG203"]


def test_reports_import_order_within_group() -> None:
    source = "import json\nfrom pathlib import Path\n"

    assert _codes(source) == ["YNG401"]


def test_resets_import_order_across_blank_line_groups() -> None:
    source = "import json\n\nfrom package import Item\n"

    assert _codes(source) == []


def test_reports_syntax_error() -> None:
    assert _codes("def broken(:\n") == ["YNG000"]
