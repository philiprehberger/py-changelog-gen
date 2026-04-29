"""Git-based changelog generator from conventional commits."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

__all__ = ["generate_changelog", "Changelog", "CommitEntry", "main"]

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>\w+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?:\s*(?P<message>.+)$"
)

DEFAULT_TYPE_HEADINGS: dict[str, str] = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "perf": "Performance",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "test": "Tests",
    "chore": "Chores",
    "ci": "CI/CD",
    "build": "Build",
    "style": "Style",
}


@dataclass
class CommitEntry:
    """A parsed conventional commit."""

    hash: str
    type: str
    scope: str | None
    message: str
    breaking: bool
    date: str
    author: str
    raw: str


@dataclass
class Changelog:
    """Generated changelog content."""

    version: str | None
    date: str
    entries: dict[str, list[CommitEntry]] = field(default_factory=dict)
    breaking_changes: list[CommitEntry] = field(default_factory=list)

    def to_markdown(
        self,
        type_headings: dict[str, str] | None = None,
    ) -> str:
        headings = type_headings or DEFAULT_TYPE_HEADINGS
        lines: list[str] = []

        header = f"## {self.version}" if self.version else "## Unreleased"
        header += f" ({self.date})"
        lines.append(header)
        lines.append("")

        if self.breaking_changes:
            lines.append("### Breaking Changes")
            lines.append("")
            for entry in self.breaking_changes:
                scope = f"**{entry.scope}:** " if entry.scope else ""
                lines.append(f"- {scope}{entry.message}")
            lines.append("")

        for commit_type, entries in self.entries.items():
            if not entries:
                continue
            heading = headings.get(commit_type, commit_type.title())
            lines.append(f"### {heading}")
            lines.append("")
            for entry in entries:
                scope = f"**{entry.scope}:** " if entry.scope else ""
                lines.append(f"- {scope}{entry.message}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def write(
        self,
        path: str | Path = "CHANGELOG.md",
        mode: Literal["overwrite", "prepend"] = "prepend",
    ) -> None:
        path = Path(path)
        content = self.to_markdown()

        if mode == "prepend" and path.exists():
            existing = path.read_text()
            # Insert after the first heading line if it exists
            if existing.startswith("# "):
                first_newline = existing.index("\n")
                header = existing[:first_newline + 1]
                rest = existing[first_newline + 1:]
                content = header + "\n" + content + "\n" + rest
            else:
                content = content + "\n" + existing
        elif mode == "prepend":
            content = "# Changelog\n\n" + content

        path.write_text(content)


def _git(args: list[str], repo_path: str = ".") -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _get_latest_tag(repo_path: str = ".") -> str | None:
    try:
        return _git(["describe", "--tags", "--abbrev=0"], repo_path)
    except RuntimeError:
        return None


def generate_changelog(
    repo_path: str = ".",
    from_tag: str | None = None,
    to_ref: str = "HEAD",
    version: str | None = None,
    include_types: list[str] | None = None,
    exclude_types: list[str] | None = None,
    scope: str | None = None,
) -> Changelog:
    """Generate a changelog from git history.

    Args:
        repo_path: Path to the git repository.
        from_tag: Start tag (exclusive). Defaults to latest tag.
        to_ref: End ref (inclusive). Defaults to HEAD.
        version: Version label for the changelog section.
        include_types: Only include these commit types.
        exclude_types: Exclude these commit types.
        scope: When set, only include commits whose conventional-commit
            scope equals this value (e.g. ``scope="api"``).

    Returns:
        Changelog object with parsed entries.
    """
    if from_tag is None:
        from_tag = _get_latest_tag(repo_path)

    range_spec = f"{from_tag}..{to_ref}" if from_tag else to_ref

    log_format = "%H|%ad|%an|%s"
    raw_log = _git(
        ["log", range_spec, f"--pretty=format:{log_format}", "--date=short"],
        repo_path,
    )

    entries: dict[str, list[CommitEntry]] = {}
    breaking: list[CommitEntry] = []
    today = datetime.now().strftime("%Y-%m-%d")

    for line in raw_log.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        commit_hash, date, author, subject = parts

        match = CONVENTIONAL_RE.match(subject)
        if not match:
            # Non-conventional commit — put under "other"
            entry = CommitEntry(
                hash=commit_hash[:7],
                type="other",
                scope=None,
                message=subject,
                breaking=False,
                date=date,
                author=author,
                raw=subject,
            )
        else:
            entry = CommitEntry(
                hash=commit_hash[:7],
                type=match.group("type"),
                scope=match.group("scope"),
                message=match.group("message"),
                breaking=bool(match.group("breaking")),
                date=date,
                author=author,
                raw=subject,
            )

        if include_types and entry.type not in include_types:
            continue
        if exclude_types and entry.type in exclude_types:
            continue
        if scope is not None and entry.scope != scope:
            continue

        if entry.breaking:
            breaking.append(entry)

        entries.setdefault(entry.type, []).append(entry)

    return Changelog(
        version=version,
        date=today,
        entries=entries,
        breaking_changes=breaking,
    )


def main() -> None:
    """CLI entrypoint."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate changelog from git history")
    parser.add_argument("--repo", default=".", help="Repository path")
    parser.add_argument("--from", dest="from_tag", help="Start tag")
    parser.add_argument("--to", default="HEAD", help="End ref")
    parser.add_argument("--version", help="Version label")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--prepend", action="store_true", help="Prepend to existing file")
    parser.add_argument("--scope", help="Only include commits with this scope")
    args = parser.parse_args()

    changelog = generate_changelog(
        repo_path=args.repo,
        from_tag=args.from_tag,
        to_ref=args.to,
        version=args.version,
        scope=args.scope,
    )

    if args.output:
        mode = "prepend" if args.prepend else "overwrite"
        changelog.write(args.output, mode=mode)
        print(f"Wrote changelog to {args.output}")
    else:
        print(changelog.to_markdown())
