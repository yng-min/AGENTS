"""
Scan Python repositories and build an evidence-oriented project index.
"""

import ast
from pathlib import Path

from agents_tools.models import Confidence, Location, ProjectIndex, Reference, Symbol


IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv"
}


class PythonScanner(ast.NodeVisitor):
    """
    Collect definitions, imports, calls, and string references from one module.
    """
    def __init__(self, index: ProjectIndex, path: Path) -> None:
        self.index: ProjectIndex = index
        self.path: Path = path
        self.scope: list[str] = []
        self.imports: set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._add_symbol(name=node.name, kind="class", line=node.lineno)
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node=node, kind="function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node=node, kind="async_function")

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name)
            self._add_reference(
                name=alias.name,
                kind="import",
                line=node.lineno,
                confidence=Confidence.CONFIRMED
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        prefix = "." * node.level
        imported_module = f"{prefix}{module}"
        self.imports.add(imported_module)

        for alias in node.names:
            name = f"{imported_module}.{alias.name}" if imported_module else alias.name
            self._add_reference(
                name=name,
                kind="import",
                line=node.lineno,
                confidence=Confidence.CONFIRMED
            )

    def visit_Call(self, node: ast.Call) -> None:
        name = _resolve_expression_name(node=node.func)
        if name is not None:
            confidence = Confidence.CONFIRMED if isinstance(node.func, ast.Name) else Confidence.PROBABLE
            self._add_reference(
                name=name,
                kind="call",
                line=node.lineno,
                confidence=confidence
            )

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and _is_reference_like(value=node.value):
            self._add_reference(
                name=node.value,
                kind="string",
                line=node.lineno,
                confidence=Confidence.TEXTUAL
            )

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, kind: str) -> None:
        self._add_symbol(name=node.name, kind=kind, line=node.lineno)
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _add_symbol(self, name: str, kind: str, line: int) -> None:
        qualified_parts = [self.path.with_suffix("").as_posix().replace("/", "."), *self.scope, name]
        self.index.symbols.append(
            Symbol(
                name=name,
                qualified_name=".".join(qualified_parts),
                kind=kind,
                location=Location(path=self.path, line=line)
            )
        )

    def _add_reference(self, name: str, kind: str, line: int, confidence: Confidence) -> None:
        self.index.references.append(
            Reference(
                name=name,
                kind=kind,
                location=Location(path=self.path, line=line),
                confidence=confidence
            )
        )


def scan_project(root: Path) -> ProjectIndex:
    """
    Build a project index for all supported Python files below root.
    """
    resolved_root = root.resolve()
    index = ProjectIndex(root=resolved_root)

    for absolute_path in sorted(resolved_root.rglob("*.py")):
        relative_path = absolute_path.relative_to(resolved_root)
        if any(part in IGNORED_DIRECTORY_NAMES for part in relative_path.parts):
            continue

        try:
            source = absolute_path.read_text(encoding="utf-8")
            tree = ast.parse(source=source, filename=str(relative_path))
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            index.syntax_errors[relative_path] = str(error)
            continue

        scanner = PythonScanner(index=index, path=relative_path)
        scanner.visit(tree)
        index.imports[relative_path] = scanner.imports

    return index


def _resolve_expression_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = _resolve_expression_name(node=node.value)
        return f"{parent}.{node.attr}" if parent is not None else node.attr

    return None


def _is_reference_like(value: str) -> bool:
    if len(value) < 3 or len(value) > 160:
        return False

    return any(marker in value for marker in (".", "_", "-", "/")) and " " not in value
