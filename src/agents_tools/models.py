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


@dataclass
class ProjectIndex:
    """
    Store repository symbols and references collected by scanners.
    """
    root: Path
    symbols: list[Symbol] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)
    imports: dict[Path, set[str]] = field(default_factory=dict)
    syntax_errors: dict[Path, str] = field(default_factory=dict)
