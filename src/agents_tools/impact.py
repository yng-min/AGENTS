"""
Resolve repository evidence related to a target file or Python symbol.
"""

from dataclasses import dataclass, field
from pathlib import Path

from agents_tools.models import AdapterReport, Confidence, Evidence, ProjectIndex, Reference, Symbol


RESOURCE_SUFFIXES = { ".json", ".toml", ".yaml", ".yml" }
DOCUMENT_SUFFIXES = { ".md", ".rst" }


@dataclass
class ImpactReport:
    """
    Store the evidence collected for one impact-analysis target.
    """
    target: str
    symbols: list[Symbol] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)
    importing_files: list[Path] = field(default_factory=list)
    related_tests: list[Path] = field(default_factory=list)
    related_resources: list[Path] = field(default_factory=list)
    related_documents: list[Path] = field(default_factory=list)
    supporting_evidence: list[Evidence] = field(default_factory=list)
    adapter_reports: list[AdapterReport] = field(default_factory=list)


def analyze_impact(index: ProjectIndex, target: str) -> ImpactReport:
    """
    Analyze repository evidence for a file path or symbol name.
    """
    normalized_target = target.replace("\\", "/")
    target_path = Path(normalized_target)
    symbol_query = normalized_target.split("::")[-1].split(".")[-1]

    matching_symbols = [
        symbol
        for symbol in index.symbols
        if _symbol_matches(symbol=symbol, target=normalized_target, symbol_query=symbol_query)
    ]
    names = { symbol.name for symbol in matching_symbols }
    if not names and "::" in normalized_target:
        names.add(symbol_query)

    references = [
        reference
        for reference in index.references
        if _reference_matches(reference=reference, names=names, target=normalized_target)
    ]

    module_name = target_path.with_suffix("").as_posix().replace("/", ".")
    importing_files = sorted(
        path
        for path, imports in index.imports.items()
        if any(_import_matches(import_name=import_name, module_name=module_name) for import_name in imports)
    )
    search_terms = _search_terms(target=target_path, names=names)
    supporting_evidence = [
        evidence
        for evidence in index.evidence
        if _evidence_matches(evidence=evidence, search_terms=search_terms, target=normalized_target)
    ]
    related_tests = _find_related_files(
        root=index.root,
        target=target_path,
        directories=("tests", "test"),
        suffixes={ ".py" }
    )
    related_resources = _find_text_relations(
        root=index.root,
        search_terms=search_terms,
        suffixes=RESOURCE_SUFFIXES
    )
    related_documents = _find_text_relations(
        root=index.root,
        search_terms=search_terms,
        suffixes=DOCUMENT_SUFFIXES
    )

    return ImpactReport(
        target=target,
        symbols=matching_symbols,
        references=sorted(references, key=lambda item: (str(item.location.path), item.location.line)),
        importing_files=importing_files,
        related_tests=related_tests,
        related_resources=related_resources,
        related_documents=related_documents,
        supporting_evidence=sorted(
            supporting_evidence,
            key=lambda item: (
                item.source,
                str(item.location.path) if item.location else "",
                item.location.line if item.location else 0
            )
        ),
        adapter_reports=index.adapter_reports
    )


def render_impact_report(report: ImpactReport) -> str:
    """
    Render an impact report as readable plain text.
    """
    sections = [f"Impact analysis: {report.target}"]
    sections.append(_render_symbols(symbols=report.symbols))
    sections.append(_render_references(references=report.references))
    sections.append(_render_paths(title="Importing files", paths=report.importing_files))
    sections.append(_render_paths(title="Related tests", paths=report.related_tests))
    sections.append(_render_paths(title="Related resources", paths=report.related_resources))
    sections.append(_render_paths(title="Related documents", paths=report.related_documents))
    sections.append(_render_evidence(evidence_items=report.supporting_evidence))
    sections.append(_render_adapters(reports=report.adapter_reports))
    return "\n\n".join(section for section in sections if section)


def _symbol_matches(symbol: Symbol, target: str, symbol_query: str) -> bool:
    path = symbol.location.path.as_posix()
    if target == path or target == path.removesuffix(".py"):
        return True

    if "::" in target:
        target_path, requested_symbol = target.split("::", maxsplit=1)
        return path == target_path and (symbol.name == requested_symbol or symbol.qualified_name.endswith(requested_symbol))

    return symbol.name == symbol_query or symbol.qualified_name.endswith(target)


def _reference_matches(reference: Reference, names: set[str], target: str) -> bool:
    if reference.name in names:
        return True

    if any(reference.name.endswith(f".{name}") for name in names):
        return True

    normalized_name = reference.name.replace(".", "/")
    normalized_target = target.removesuffix(".py").replace("::", "/")
    return normalized_target in normalized_name or normalized_name in normalized_target


def _evidence_matches(evidence: Evidence, search_terms: set[str], target: str) -> bool:
    haystack = f"{evidence.category} {evidence.message}".lower()
    if evidence.location and target.split("::", maxsplit=1)[0] == evidence.location.path.as_posix():
        return True
    return any(term.lower() in haystack for term in search_terms)


def _import_matches(import_name: str, module_name: str) -> bool:
    normalized_import = import_name.lstrip(".")
    return normalized_import == module_name or normalized_import.endswith(module_name)


def _search_terms(target: Path, names: set[str]) -> set[str]:
    terms = { target.stem, target.with_suffix("").as_posix(), *names }
    return { term for term in terms if len(term) >= 3 }


def _find_related_files(root: Path, target: Path, directories: tuple[str, ...], suffixes: set[str]) -> list[Path]:
    terms = { target.stem.lower(), *[part.lower() for part in target.parts if len(part) >= 3] }
    matches: list[Path] = []

    for absolute_path in root.rglob("*"):
        if not absolute_path.is_file() or absolute_path.suffix not in suffixes:
            continue

        relative_path = absolute_path.relative_to(root)
        if not any(directory in relative_path.parts for directory in directories):
            continue

        path_text = relative_path.as_posix().lower()
        if any(term in path_text for term in terms):
            matches.append(relative_path)

    return sorted(set(matches))


def _find_text_relations(root: Path, search_terms: set[str], suffixes: set[str]) -> list[Path]:
    matches: list[Path] = []

    for absolute_path in root.rglob("*"):
        if not absolute_path.is_file() or absolute_path.suffix.lower() not in suffixes:
            continue

        try:
            content = absolute_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        if any(term in content or term in absolute_path.as_posix() for term in search_terms):
            matches.append(absolute_path.relative_to(root))

    return sorted(set(matches))


def _render_symbols(symbols: list[Symbol]) -> str:
    lines = ["Definitions"]
    if not symbols:
        return "\n".join([*lines, "- None found"])

    for symbol in symbols:
        lines.append(
            f"- [{Confidence.CONFIRMED}] {symbol.kind} {symbol.qualified_name} "
            f"({symbol.location.path}:{symbol.location.line})"
        )
    return "\n".join(lines)


def _render_references(references: list[Reference]) -> str:
    lines = ["References"]
    if not references:
        return "\n".join([*lines, "- None found"])

    for reference in references:
        lines.append(
            f"- [{reference.confidence}] {reference.kind} {reference.name} "
            f"({reference.location.path}:{reference.location.line}, source={reference.source})"
        )
    return "\n".join(lines)


def _render_paths(title: str, paths: list[Path]) -> str:
    lines = [title]
    lines.extend(f"- {path}" for path in paths)
    if len(lines) == 1:
        lines.append("- None found")
    return "\n".join(lines)


def _render_evidence(evidence_items: list[Evidence]) -> str:
    lines = ["Supporting adapter evidence"]
    if not evidence_items:
        return "\n".join([*lines, "- None found"])

    for evidence in evidence_items:
        location = f" ({evidence.location.path}:{evidence.location.line})" if evidence.location else ""
        lines.append(
            f"- [{evidence.confidence}] {evidence.source}/{evidence.category}: "
            f"{evidence.message}{location}"
        )
    return "\n".join(lines)


def _render_adapters(reports: list[AdapterReport]) -> str:
    lines = ["Adapter status"]
    if not reports:
        return "\n".join([*lines, "- Built-in AST analysis only"])

    for report in reports:
        version = f" {report.version}" if report.version else ""
        detail = f": {report.detail}" if report.detail else ""
        lines.append(f"- {report.name}{version} [{report.state}]{detail}")
    return "\n".join(lines)
