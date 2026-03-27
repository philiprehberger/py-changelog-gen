# philiprehberger-changelog-gen

[![Tests](https://github.com/philiprehberger/py-changelog-gen/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-changelog-gen/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-changelog-gen.svg)](https://pypi.org/project/philiprehberger-changelog-gen/)
[![License](https://img.shields.io/github/license/philiprehberger/py-changelog-gen)](LICENSE)
[![Sponsor](https://img.shields.io/badge/sponsor-GitHub%20Sponsors-ec6cb9)](https://github.com/sponsors/philiprehberger)

Git-based changelog generator from conventional commits.

## Installation

```bash
pip install philiprehberger-changelog-gen
```

## Usage

### Python API

```python
from philiprehberger_changelog_gen import generate_changelog

changelog = generate_changelog(
    repo_path=".",
    from_tag="v0.1.0",
    version="0.2.0",
)

# Print markdown
print(changelog.to_markdown())

# Write to file (prepend to existing)
changelog.write("CHANGELOG.md", mode="prepend")
```

### CLI

```bash
# Print to stdout
changelog-gen

# From a specific tag
changelog-gen --from v0.1.0 --version 0.2.0

# Write to file
changelog-gen --output CHANGELOG.md --prepend
```

## Conventional Commits

The generator parses conventional commit messages:

```
feat: add user authentication
fix(auth): handle expired tokens
feat!: redesign API (breaking change)
chore: update dependencies
```

Commits are grouped by type: Features, Bug Fixes, Performance, Refactoring, Documentation, Tests, Chores, CI/CD, Build, Style.

## Output Example

```markdown
## 0.2.0 (2026-03-10)

### Breaking Changes

- **api:** redesign authentication flow

### Features

- add user dashboard
- **auth:** add OAuth2 support

### Bug Fixes

- **db:** fix connection pool leak
```


## API

| Function / Class | Description |
|------------------|-------------|
| `generate_changelog(repo_path, from_tag, to_ref, version, include_types, exclude_types)` | Generate a changelog from git history between tags/refs |
| `Changelog` | Generated changelog content with `to_markdown()` and `write(path, mode)` methods |
| `CommitEntry` | A parsed conventional commit (hash, type, scope, message, breaking, date, author) |
| `main()` | CLI entrypoint for command-line usage |

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## License

MIT
