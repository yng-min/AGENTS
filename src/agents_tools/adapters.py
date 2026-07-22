"""
Run optional local analyzers behind stable repository evidence models.
"""

import importlib.metadata
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from agents_tools.models import AdapterReport, AdapterState, Confidence, Evidence, Location, ProjectIndex


class AnalysisAdapter(Protocol):
    """
    Define the boundary implemented by optional analysis integrations.
    """
    name: str

    def enrich(self, index: ProjectIndex) -> AdapterReport:
        """
        Add normalized evidence to an existing project index.
        """
        ...


@dataclass(frozen=True)
class AdapterSelection:
    """
    Describe which optional adapters should run.
    """
    names: tuple[str, ...]


def enrich_project(index: ProjectIndex, selection: AdapterSelection) -> ProjectIndex:
    """
    Run selected adapters without allowing one failure to stop core analysis.
    """
    adapters = _build_adapters(selection=selection)
    for adapter in adapters:
        try:
            report = adapter.enrich(index=index)
        except Exception as error:
            report = AdapterReport(
                name=adapter.name,
                state=AdapterState.FAILED,
                detail=str(error)
            )
        index.adapter_reports.append(report)
    return index


def available_adapter_names() -> tuple[str, ...]:
    """
    Return supported optional adapter names.
    """
    return ("grimp", "pyright", "semgrep")


def _build_adapters(selection: AdapterSelection) -> list[AnalysisAdapter]:
    selected = set(selection.names)
    if "all" in selected:
        selected = set(available_adapter_names())

    adapters: list[AnalysisAdapter] = []
    if "grimp" in selected:
        adapters.append(GrimpAdapter())
    if "pyright" in selected:
        adapters.append(PyrightAdapter())
    if "semgrep" in selected:
        adapters.append(SemgrepAdapter())
    return adapters


class GrimpAdapter:
    """
    Collect import graph evidence when Grimp is installed locally.
    """
    name = "grimp"

    def enrich(self, index: ProjectIndex) -> AdapterReport:
        try:
            import grimp
        except ImportError:
            return AdapterReport(name=self.name, state=AdapterState.UNAVAILABLE, detail="grimp is not installed")

        package_names = _discover_package_names(root=index.root)
        if not package_names:
            return AdapterReport(name=self.name, state=AdapterState.SKIPPED, detail="no importable package roots found")

        edge_count = 0
        for package_name in package_names:
            graph = grimp.build_graph(package_name, include_external_packages=False)
            for importer in sorted(graph.modules):
                imported_modules = graph.find_modules_directly_imported_by(importer)
                importer_path = _module_to_path(root=index.root, module_name=importer)
                if importer_path is None:
                    continue

                for imported in imported_modules:
                    index.imports.setdefault(importer_path, set()).add(imported)
                    index.evidence.append(
                        Evidence(
                            source=self.name,
                            category="import_edge",
                            message=f"{importer} imports {imported}",
                            confidence=Confidence.CONFIRMED,
                            location=Location(path=importer_path, line=1)
                        )
                    )
                    edge_count += 1

        return AdapterReport(
            name=self.name,
            state=AdapterState.AVAILABLE,
            version=_package_version(name="grimp"),
            detail=f"collected {edge_count} import edges"
        )


class PyrightAdapter:
    """
    Collect local Pyright diagnostics as supporting type evidence.
    """
    name = "pyright"

    def enrich(self, index: ProjectIndex) -> AdapterReport:
        executable = shutil.which("pyright")
        if executable is None:
            return AdapterReport(name=self.name, state=AdapterState.UNAVAILABLE, detail="pyright executable not found")

        result = subprocess.run(
            [executable, "--outputjson", str(index.root)],
            cwd=index.root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if not result.stdout.strip():
            detail = result.stderr.strip() or "pyright returned no JSON output"
            return AdapterReport(name=self.name, state=AdapterState.FAILED, detail=detail)

        payload = json.loads(result.stdout)
        diagnostics = payload.get("generalDiagnostics", [])
        for diagnostic in diagnostics:
            file_path = _relative_path(root=index.root, value=diagnostic.get("file"))
            start = diagnostic.get("range", {}).get("start", {})
            line = int(start.get("line", 0)) + 1
            severity = str(diagnostic.get("severity", "information"))
            confidence = Confidence.PROBABLE if severity in {"error", "warning"} else Confidence.TEXTUAL
            index.evidence.append(
                Evidence(
                    source=self.name,
                    category=f"type_{severity}",
                    message=str(diagnostic.get("message", "Pyright diagnostic")),
                    confidence=confidence,
                    location=Location(path=file_path, line=line) if file_path is not None else None
                )
            )

        version = payload.get("version") or _command_version(executable=executable)
        return AdapterReport(
            name=self.name,
            state=AdapterState.AVAILABLE,
            version=str(version) if version else None,
            detail=f"collected {len(diagnostics)} diagnostics"
        )


class SemgrepAdapter:
    """
    Collect findings from repository-owned Semgrep rules only.
    """
    name = "semgrep"

    def enrich(self, index: ProjectIndex) -> AdapterReport:
        executable = shutil.which("semgrep")
        if executable is None:
            return AdapterReport(name=self.name, state=AdapterState.UNAVAILABLE, detail="semgrep executable not found")

        config_path = _find_semgrep_config(root=index.root)
        if config_path is None:
            return AdapterReport(
                name=self.name,
                state=AdapterState.SKIPPED,
                detail="no local Semgrep configuration found"
            )

        result = subprocess.run(
            [executable, "scan", "--config", str(config_path), "--json", str(index.root)],
            cwd=index.root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if not result.stdout.strip():
            detail = result.stderr.strip() or "semgrep returned no JSON output"
            return AdapterReport(name=self.name, state=AdapterState.FAILED, detail=detail)

        payload = json.loads(result.stdout)
        findings = payload.get("results", [])
        for finding in findings:
            extra = finding.get("extra", {})
            path = Path(str(finding.get("path", "")))
            line = int(finding.get("start", {}).get("line", 1))
            rule_id = str(finding.get("check_id", "semgrep-rule"))
            message = str(extra.get("message", rule_id))
            index.evidence.append(
                Evidence(
                    source=self.name,
                    category=rule_id,
                    message=message,
                    confidence=Confidence.PROBABLE,
                    location=Location(path=path, line=line)
                )
            )

        return AdapterReport(
            name=self.name,
            state=AdapterState.AVAILABLE,
            version=_command_version(executable=executable),
            detail=f"collected {len(findings)} findings from {config_path.relative_to(index.root)}"
        )


def _discover_package_names(root: Path) -> tuple[str, ...]:
    source_roots = [root]
    if (root / "src").is_dir():
        source_roots.insert(0, root / "src")

    names: list[str] = []
    for source_root in source_roots:
        for init_path in sorted(source_root.glob("*/__init__.py")):
            names.append(init_path.parent.name)
    return tuple(dict.fromkeys(names))


def _module_to_path(root: Path, module_name: str) -> Path | None:
    candidates = (
        root / Path(*module_name.split(".")).with_suffix(".py"),
        root / Path(*module_name.split(".")) / "__init__.py",
        root / "src" / Path(*module_name.split(".")).with_suffix(".py"),
        root / "src" / Path(*module_name.split(".")) / "__init__.py"
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.relative_to(root)
    return None


def _find_semgrep_config(root: Path) -> Path | None:
    candidates = (
        root / ".semgrep.yml",
        root / ".semgrep.yaml",
        root / "semgrep.yml",
        root / "semgrep.yaml"
    )
    return next((path for path in candidates if path.is_file()), None)


def _relative_path(root: Path, value: object) -> Path | None:
    if not value:
        return None

    path = Path(str(value))
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return path


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _command_version(executable: str) -> str | None:
    result = subprocess.run(
        [executable, "--version"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    value = result.stdout.strip() or result.stderr.strip()
    return value.splitlines()[0] if value else None
