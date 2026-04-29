"""Tests for philiprehberger_changelog_gen."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from philiprehberger_changelog_gen import (
    Changelog,
    CommitEntry,
    generate_changelog,
)


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env={
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
            "PATH": "/usr/bin:/usr/local/bin",
        },
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(["init", "-q", "-b", "main"], cwd=tmp_path)
    (tmp_path / "f.txt").write_text("a")
    _git(["add", "."], cwd=tmp_path)
    _git(["commit", "-q", "-m", "feat: first feature"], cwd=tmp_path)
    (tmp_path / "f.txt").write_text("b")
    _git(["commit", "-q", "-am", "fix(api): a bug"], cwd=tmp_path)
    (tmp_path / "f.txt").write_text("c")
    _git(["commit", "-q", "-am", "feat(api)!: breaking change"], cwd=tmp_path)
    (tmp_path / "f.txt").write_text("d")
    _git(["commit", "-q", "-am", "chore: bump deps"], cwd=tmp_path)
    (tmp_path / "f.txt").write_text("e")
    _git(["commit", "-q", "-am", "non-conventional message"], cwd=tmp_path)
    return tmp_path


def test_generate_groups_by_type(repo: Path) -> None:
    cl = generate_changelog(repo_path=str(repo), version="1.0.0")
    assert "feat" in cl.entries
    assert "fix" in cl.entries
    assert "chore" in cl.entries
    assert "other" in cl.entries
    assert len(cl.entries["feat"]) == 2


def test_breaking_changes_collected(repo: Path) -> None:
    cl = generate_changelog(repo_path=str(repo), version="1.0.0")
    assert len(cl.breaking_changes) == 1
    assert cl.breaking_changes[0].scope == "api"
    assert cl.breaking_changes[0].breaking is True


def test_include_types_filter(repo: Path) -> None:
    cl = generate_changelog(repo_path=str(repo), include_types=["feat"])
    assert set(cl.entries.keys()) == {"feat"}


def test_exclude_types_filter(repo: Path) -> None:
    cl = generate_changelog(repo_path=str(repo), exclude_types=["chore", "other"])
    assert "chore" not in cl.entries
    assert "other" not in cl.entries
    assert "feat" in cl.entries


def test_scope_filter(repo: Path) -> None:
    cl = generate_changelog(repo_path=str(repo), scope="api")
    all_entries = [e for entries in cl.entries.values() for e in entries]
    assert all(e.scope == "api" for e in all_entries)
    assert len(all_entries) == 2


def test_scope_filter_no_match(repo: Path) -> None:
    cl = generate_changelog(repo_path=str(repo), scope="nonexistent")
    all_entries = [e for entries in cl.entries.values() for e in entries]
    assert all_entries == []


def test_to_markdown_renders_sections(repo: Path) -> None:
    cl = generate_changelog(repo_path=str(repo), version="1.0.0")
    md = cl.to_markdown()
    assert md.startswith("## 1.0.0")
    assert "### Breaking Changes" in md
    assert "### Features" in md
    assert "### Bug Fixes" in md
    assert "**api:** breaking change" in md


def test_to_markdown_unreleased_when_no_version() -> None:
    cl = Changelog(version=None, date="2026-04-29")
    md = cl.to_markdown()
    assert md.startswith("## Unreleased (2026-04-29)")


def test_write_prepends_to_existing_changelog(repo: Path, tmp_path: Path) -> None:
    target = tmp_path / "CHANGELOG.md"
    target.write_text("# Changelog\n\n## 0.1.0 (2026-01-01)\n\n- old entry\n")
    cl = generate_changelog(repo_path=str(repo), version="1.0.0")
    cl.write(target, mode="prepend")
    content = target.read_text()
    assert content.startswith("# Changelog")
    assert content.index("## 1.0.0") < content.index("## 0.1.0")


def test_commit_entry_dataclass() -> None:
    entry = CommitEntry(
        hash="abc1234",
        type="feat",
        scope=None,
        message="hello",
        breaking=False,
        date="2026-04-29",
        author="Test",
        raw="feat: hello",
    )
    assert entry.type == "feat"
    assert not entry.breaking
