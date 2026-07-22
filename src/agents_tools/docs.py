"""
Detect documentation that may need updates after repository changes.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentationImpact:
    """
    Describe a documentation update candidate and its repository evidence.
    """
    path: Path
    reason: str
    confidence: str


def check_documentation(root: Path, base: str) -> list[DocumentationImpact]:
    """
    Compare the working branch with base and identify documentation candidates.
    """
    changed_files = _get_changed_files(root=root, base=base)
    diff = _get_diff(root=root, base=base)
    candidates: list[DocumentationImpact] = []

    for path in changed_files:
        candidates.extend(_candidates_for_path(root=root, path=path, diff=diff))

    unique = {
        (candidate.path, candidate.reason): candidate
        for candidate in candidates
    }
    return sorted(unique.values(), key=lambda item: (str(item.path), item.reason))


def render_documentation_impacts(impacts: list[DocumentationImpact]) -> str:
    """
    Render documentation impact candidates as plain text.
    """
    if not impacts:
        return "No documentation impact detected."

    lines = ["Documentation impact detected"]
    current_path: Path | None = None

    for impact in impacts:
        if impact.path != current_path:
            lines.extend(("", str(impact.path)))
            current_path = impact.path
        lines.append(f"- [{impact.confidence}] {impact.reason}")

    return "\n".join(lines)


def _get_changed_files(root: Path, base: str) -> list[Path]:
    output = _run_git(root=root, arguments=("diff", "--name-only", f"{base}...HEAD"))
    return [Path(line) for line in output.splitlines() if line.strip()]


def _get_diff(root: Path, base: str) -> str:
    return _run_git(root=root, arguments=("diff", "--unified=0", f"{base}...HEAD"))


def _run_git(root: Path, arguments: tuple[str, ...]) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "git command failed"
        raise RuntimeError(message)
    return result.stdout


def _candidates_for_path(root: Path, path: Path, diff: str) -> list[DocumentationImpact]:
    path_text = path.as_posix().lower()
    candidates: list[DocumentationImpact] = []

    if path.suffix in {".toml", ".yaml", ".yml", ".json", ".env"} or "config" in path_text:
        candidates.extend(
            _existing_candidates(
                root=root,
                preferred=("docs/configuration.md", ".env.example", "README.md"),
                reason=f"Configuration changed in {path}",
                confidence="high"
            )
        )

    if any(marker in path_text for marker in ("deploy", "workflow", "docker", "compose", "systemd", "scripts/")):
        candidates.extend(
            _existing_candidates(
                root=root,
                preferred=("docs/deployment.md", "docs/operation.md", "README.md"),
                reason=f"Deployment or operation behavior changed in {path}",
                confidence="high"
            )
        )

    if path.suffix == ".py":
        file_diff = _extract_file_diff(diff=diff, path=path)

        if re.search(r"^\+\s*(class|def|async def)\s+", file_diff, flags=re.MULTILINE):
            candidates.extend(
                _existing_candidates(
                    root=root,
                    preferred=("docs/architecture.md", "README.md"),
                    reason=f"Public structure or callable surface may have changed in {path}",
                    confidence="medium"
                )
            )

        if re.search(r"^\+.*(?:os\.environ|getenv|BaseSettings|env\()", file_diff, flags=re.MULTILINE):
            candidates.extend(
                _existing_candidates(
                    root=root,
                    preferred=("docs/configuration.md", ".env.example", "README.md"),
                    reason=f"Environment configuration may have changed in {path}",
                    confidence="high"
                )
            )

        if re.search(r"^\+.*(?:dataclass|TypedDict|BaseModel|CREATE TABLE|ALTER TABLE)", file_diff, flags=re.MULTILINE):
            candidates.extend(
                _existing_candidates(
                    root=root,
                    preferred=("docs/database.md", "docs/architecture.md", "README.md"),
                    reason=f"Data structure may have changed in {path}",
                    confidence="medium"
                )
            )

    return candidates


def _existing_candidates(
    root: Path,
    preferred: tuple[str, ...],
    reason: str,
    confidence: str
) -> list[DocumentationImpact]:
    existing = [Path(path) for path in preferred if (root / path).exists()]
    if not existing:
        existing = [Path(preferred[0])]

    return [
        DocumentationImpact(path=path, reason=reason, confidence=confidence)
        for path in existing
    ]


def _extract_file_diff(diff: str, path: Path) -> str:
    header = f"diff --git a/{path.as_posix()} b/{path.as_posix()}"
    start = diff.find(header)
    if start == -1:
        return ""

    next_start = diff.find("\ndiff --git ", start + len(header))
    return diff[start:] if next_start == -1 else diff[start:next_start]
