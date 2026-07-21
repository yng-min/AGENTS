"""
Tests for project-aware import rules.
"""

from textwrap import dedent

from yngfmt.imports import ImportConfig, check_imports, sort_imports


_CONFIG = ImportConfig(first_party=("project",))


def test_sorts_standard_third_party_and_first_party_groups() -> None:
    source = dedent(
        """
        from project.domain.article import Article
        import requests
        import json
        from pathlib import Path

        value = 1
        """
    ).lstrip()

    assert sort_imports(source=source, config=_CONFIG) == dedent(
        """
        from pathlib import Path
        import json

        import requests

        from project.domain.article import Article

        value = 1
        """
    ).lstrip()


def test_sorts_first_party_segments_with_reserved_positions() -> None:
    source = dedent(
        """
        from project.config.runtime import runtime_config
        from project.infrastructure.database import Database
        from project.language.i18n import translate
        from project.application.service import Service
        from project.domain.article import Article
        """
    ).lstrip()

    assert sort_imports(source=source, config=_CONFIG) == dedent(
        """
        from project.language.i18n import translate

        from project.application.service import Service

        from project.domain.article import Article

        from project.infrastructure.database import Database


        from project.config.runtime import runtime_config
        """
    ).lstrip()


def test_sorts_same_root_by_depth() -> None:
    source = dedent(
        """
        from package.deep.module import C
        from package.module import B
        from package import A
        """
    ).lstrip()

    assert sort_imports(source=source) == dedent(
        """
        from package import A
        from package.module import B
        from package.deep.module import C
        """
    ).lstrip()


def test_preserves_inline_comments_and_multiline_imports() -> None:
    source = dedent(
        """
        from project.domain import (
            Article,
            Author,
        )  # domain models
        from project.language import translate  # public translation helper
        """
    ).lstrip()

    formatted = sort_imports(source=source, config=_CONFIG)

    assert "# domain models" in formatted
    assert "# public translation helper" in formatted
    assert formatted.startswith("from project.language")


def test_skips_explicit_keep_imports_directive() -> None:
    source = dedent(
        """
        # yngfmt: keep-imports
        import requests
        import json
        """
    ).lstrip()

    assert sort_imports(source=source, config=_CONFIG) == source


def test_checker_uses_same_canonical_sorting() -> None:
    source = "import requests\nimport json\n"

    issues = check_imports(source=source, config=_CONFIG)

    assert [issue.code for issue in issues] == ["YNG400"]
