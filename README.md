# bumpwright

![Coverage](https://lewis-morris.github.io/bumpwright/_static/badges/coverage.svg)
![Version](https://lewis-morris.github.io/bumpwright/_static/badges/version.svg)
![Python Versions](https://lewis-morris.github.io/bumpwright/_static/badges/python.svg)
![License](https://lewis-morris.github.io/bumpwright/_static/badges/license.svg)


## Introduction

Bumpwright inspects your project's public API to recommend the correct semantic
version bump. It compares two Git references, reports the impact of their
differences, and can update version files for you.

### Comparison with similar tools

- **bump2version** – manually increments version strings without analysing code.
- **python-semantic-release** – infers releases from commit messages rather than
  the exported API.

Bumpwright focuses on the code itself, making it a good fit for libraries and
services that expose stable interfaces.

### Benefits

- **Simplicity** – run one command to review API changes.
- **Flexibility** – pluggable analysers and configuration overrides.
- **Accuracy** – highlights breaking changes commit messages may miss.

### Trade-offs

- Requires a baseline reference to compare against.
- Static analysis cannot detect runtime-only behaviour.

### Primary use cases

- Library maintainers checking semantic versioning.
- CI systems gating releases on API changes.
- Release managers reviewing change impact.

## Quickstart

Requires Python 3.11 or later.

```bash
pip install bumpwright
bumpwright init
bumpwright bump --decide
bumpwright bump --commit --tag
```

> **Note**
> Omitting `--base` compares against the last release commit or the previous commit (`HEAD^`). Using `--commit` or `--tag` requires a clean working tree.

Example output from `bumpwright bump --decide`:

```text
Suggested bump: minor
- [MINOR] demo:greet: Added public symbol
```

See the [Quickstart guide](docs/quickstart.rst) for a full walk-through and the
[documentation](docs/index.rst) for detailed guides.

## Changelog generation

Bumpwright can append release notes to a changelog using a Jinja2 template. The
default context provides additional fields sourced from git:

- ``release_datetime_iso`` – ISO-8601 timestamp of the tag's commit.
- ``compare_url`` – GitHub compare link between the previous and new tags.
- ``contributors`` – unique authors from ``git shortlog -sne`` linking to
  profiles when ``users.noreply.github.com`` emails are detected.
- ``breaking_changes`` – commits marked with a ``!`` type or a
  ``BREAKING CHANGE:`` footer.

Example output using the built-in template:

```markdown
## [v1.2.4] - 2024-04-01 (2024-04-01T12:00:00+00:00)
[Diff since v1.2.3](https://github.com/me/project/compare/v1.2.3...v1.2.4)
- [abc123](https://github.com/me/project/commit/abc123) feat!: drop old API

### Breaking changes
- feat!: drop old API

### Contributors
- [alice](https://github.com/alice)
```

Compare links let readers explore the full diff, while contributor names are
auto-detected from the commit history.

## Badges

The badges above are generated with
[`docs/scripts/generate_badges.py`](docs/scripts/generate_badges.py).
Run it in CI after tests to reuse the existing coverage result:

```bash
python docs/scripts/generate_badges.py <coverage> <version> <license> <python_versions>
```

Publish the resulting SVGs to any static host such as GitHub Pages and update
the badge URLs accordingly. Hosted services like [shields.io](https://shields.io)
are viable alternatives.

## Development

This project uses [pre-commit](https://pre-commit.com/) with Ruff, Black, and
isort to maintain code style and quality.

```bash
pre-commit install
pre-commit run --all-files
```

## Roadmap

Planned enhancements include additional analysers, a plugin architecture, and
better CI integrations. See the [roadmap](docs/roadmap.rst) for details.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

