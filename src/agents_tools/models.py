"""
Shared data models for repository analysis.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class Confidence(StrEnum):
    """
    Describe how strongly repository evidence supports a relation.
    """
    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    TEXTUAL = "textual"
    UNRESOLVED = "unresolved"


class AdapterState(StrEnum):
    """
    Describe whether an optional analysis adapter completed successfully.
    """
    AVAILABLE = "available"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True)
class Location:
    """
    Identify a location in a repository file.
    """
    path: Path
    line: int


@dataclass(frozen=True)
class Symbol:
    """
    Describe a Python symbol definition.
    """
    name: str
    qualified_name: str
    kind: str
    location: Location


@dataclass(frozen=True)
class Reference:
    """
    Describe a relation to a Python symbol or textual resource.
    """
    name: str
    kind: str
    location: Location
    confidence: Confidence
    source: str = "builtin_ast"


@dataclass(frozen=True)
class Evidence:
    """
    Store normalized evidence collected by any analysis adapter.
    """
    source: str
    category: str
    message: str
    confidence: Confidence
    location: Location | None = None


@dataclass(frozen=True)
class AdapterReport:
    """
    Record one adapter execution without exposing adapter-specific types.
    """
    name: str
    state: AdapterState
    version: str | None = None
    detail: str | None = None


@dataclass
class ProjectIndex:
    """
    Store repository evidence collected by scanners and optional adapters.
    """
    root: Path
    symbols: list[Symbol] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)
    imports: dict[Path, set[str]] = field(default_factory=dict)
    syntax_errors: dict[Path, str] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)
    adapter_reports: list[AdapterReport] = field(default_factory=list)
