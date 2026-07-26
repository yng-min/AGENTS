"""
Tests for style guide linter rules.
"""

from pathlib import Path

from yngfmt.linter import lint_code


def _diagnostics(source: str):
    return lint_code(source=source, path=Path("test.py"))


def _codes(source: str) -> list[str]:
    return [diagnostic.code for diagnostic in _diagnostics(source)]


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


def test_boolean_prefix_is_advisory_and_supports_optional_forms() -> None:
    diagnostics = _diagnostics(
        "from typing import Optional\n\n\n"
        "def execute(enabled: bool, ready: Optional[bool]) -> None:\n"
        "    self.active: bool | None = None\n"
    )

    assert [diagnostic.code for diagnostic in diagnostics] == [
        "YNG203",
        "YNG203",
        "YNG203"
    ]
    assert all(diagnostic.severity == "warning" for diagnostic in diagnostics)


def test_reports_docstring_layout_rules() -> None:
    source = '''"""Module description."""
import json


class Service:
    """Service description."""

    def execute(self) -> None:
        """Execute."""

        return None
'''

    assert _codes(source) == ["YNG104", "YNG105", "YNG106"]


def test_reports_definition_spacing_rules() -> None:
    source = '''def first() -> None:
    return None

def second() -> None:

    return None
'''

    assert _codes(source) == ["YNG401", "YNG403"]


def test_reports_class_method_spacing_rule() -> None:
    source = '''class Service:
    def first(self) -> None:
        return None
    def second(self) -> None:
        return None
'''

    assert _codes(source) == ["YNG402"]


def test_reports_short_wrapper_spacing_rule() -> None:
    source = '''def execute() -> object:
    prepare()

    return handler.execute()
'''

    assert _codes(source) == ["YNG501"]


def test_reports_direct_return_spacing_rule() -> None:
    source = '''def execute() -> object:
    result = handler.execute()

    return result
'''

    assert _codes(source) == ["YNG502"]


def test_allows_return_spacing_after_validation() -> None:
    source = '''def execute(article: object | None) -> object:
    if article is None:
        raise ValueError("missing")

    return article
'''

    assert _codes(source) == []


def test_reports_result_object_field_consistency() -> None:
    missing = '''def execute() -> dict[str, object]:
    return {"error": False, "message": "ok"}
'''
    aliases = '''def execute() -> dict[str, object]:
    return {"success": True, "msg": "ok", "payload": None}
'''

    assert _codes(missing) == ["YNG601"]
    assert _codes(aliases) == ["YNG602"]


def test_reports_import_order_within_group() -> None:
    source = "import json\nfrom pathlib import Path\n"

    assert _codes(source) == ["YNG400"]


def test_reports_syntax_error() -> None:
    assert _codes("def broken(:\n") == ["YNG000"]
