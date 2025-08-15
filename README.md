# bumpwright

Keep your project's version numbers honest by inspecting public interfaces and
recommending the next semantic version. It can even apply the bump for you.

## Why semverbump

Semantic versioning only works when releases accurately reflect the impact of
code changes. Manually tracking public interfaces across a project is tedious
and error-prone. **semverbump** automates this process by scanning source code
for API changes and recommending the appropriate version bump.

Design goals include:

- **Safety** – catch breaking changes before they reach users.
- **Determinism** – produce consistent results across environments.
- **Extensibility** – support new domains through pluggable analysers.
- **Ease of adoption** – require minimal configuration and integrate with
  existing workflows.

## Features

- Static diff of the public API to highlight breaking changes.
- Pluggable analysers for command-line tools, web routes and database
  migrations.
- Optional helpers to update version numbers across common files and tag the release.

## Installation

```bash
pip install bumpwright
```

## Quick start
| Subcommand | Purpose | Key options |
|------------|---------|-------------|
| `decide`   | Recommend a bump between two references | `--base`, `--head`, `--format` |
| `bump`     | Apply a specific version bump | `--level`, `--pyproject`, `--commit`, `--tag` |
| `auto`     | Decide and bump in a single step | `--base`, `--head`, `--commit`, `--tag` |

1. **Create a configuration file** (``bumpwright.toml``) to customise behaviour:

   ```toml
   [analyzers]
   cli = true      # enable CLI analysis
   web_routes = false  # disable route analysis
   ```

2. **Suggest the next version** between two git references:

   ```console
   $ semverbump decide --base origin/main --head HEAD --format text
   semverbump suggests: minor

   - [MINOR] cli.new_command: added CLI entry 'greet'
   ```

   ```console
   $ semverbump decide --base origin/main --head HEAD --format md
   **semverbump** suggests: `minor`


   - [MINOR] cli.new_command: added CLI entry 'greet'
   ```

   ```console
   $ semverbump decide --base origin/main --head HEAD --format json
   {"level": "minor", "changes": [{"severity": "minor", "symbol": "cli.new_command", "description": "added CLI entry 'greet'"}]}
   ```

   If ``--base`` is omitted, the command compares the current commit to its
   immediate parent (``HEAD^``).

3. **Apply the bump** and optionally commit and tag the release:

   ```console
   $ bumpwright bump --level minor --pyproject pyproject.toml --commit --tag
   Bumped version: 1.2.3 -> 1.3.0 (minor)
   ```

   Omitting ``--level`` triggers an automatic decision using ``--base`` and
   ``--head`` in the same manner as the ``decide`` command.

4. **Run everything in one step** with automatic bumping and tagging:

   ```console
   $ semverbump auto --base origin/main --commit --tag --pyproject pyproject.toml
   **semverbump** suggests: `minor`

   - [MINOR] cli.new_command: added CLI entry 'greet'
   Bumped version: 1.2.3 -> 1.3.0 (minor)
   Created tag: v1.3.0
   ```

   The command infers the base reference when ``--base`` is omitted. After the
   tag is created, push it upstream with:

   ```console
   $ git push --follow-tags
   ```

For deeper usage and configuration details, see the [usage guide](docs/usage.rst)
and [configuration reference](docs/configuration.rst).

## Configuration

Only analysers explicitly set to ``true`` run. See ``docs/configuration.rst`` for
full details. The default file name is ``bumpwright.toml`` but you may specify an
alternative with ``--config``.

### Analyser reference

#### CLI (``cli``)

Tracks command-line interfaces defined with ``argparse`` or ``click``.

Severity rules:

- Removed command → **major**
- Added command → **minor**
- Removed required option/argument → **major**
- Removed optional option/argument → **minor**
- Added required option/argument → **major**
- Added optional option/argument → **minor**
- Option/argument became optional → **minor**
- Option/argument became required → **major**

Configuration:

```toml
[analyzers]
cli = true  # enable
# cli = false  # disable
```

Dependencies: analysis of Click applications requires the ``click`` package.

#### Web routes (``web_routes``)

Detects HTTP route changes in Flask or FastAPI applications.

Severity rules:

- Removed route → **major**
- Added route → **minor**
- Removed required parameter → **major**
- Removed optional parameter → **minor**
- Added required parameter → **major**
- Added optional parameter → **minor**
- Parameter became optional → **minor**
- Parameter became required → **major**

Configuration:

```toml
[analyzers]
web_routes = true  # enable
# web_routes = false  # disable
```

Dependencies: requires ``flask`` or ``fastapi``.

#### Migrations

Analyses Alembic migration scripts for schema changes.

Severity rules:

- ``op.drop_column`` → **major**
- ``op.add_column`` (non-nullable without default) → **major**
- ``op.add_column`` (otherwise) → **minor**
- ``op.create_index`` → **minor**

Configuration:

```toml
[migrations]
paths = ["migrations"]  # directories containing Alembic scripts
# paths = []             # disable migration analysis
```

Dependencies: expects migrations generated by ``alembic``.

### Third-party dependencies

Ensure project dependencies for analysers are installed:

- ``click`` for the CLI analyser
- ``flask`` or ``fastapi`` for the web route analyser
- ``alembic`` for the migrations analyser
- Other plugins may require additional libraries such as ``jsonschema``

## Roadmap

Planned enhancements and ideas for future development include:

- **Additional analysers**: support for GraphQL schemas, gRPC services,
  and OpenAPI specifications to broaden coverage of public interfaces.
- **Plugin architecture**: allow projects to register custom analysers and
  severity rules through a stable extension API.
- **Configurable severity**: enable user-defined mapping of changes to
  semantic version levels.
- **Rich reports**: emit machine-readable JSON or human-friendly HTML
  summaries of detected changes.
- **CI integration**: provide streamlined helpers for GitHub Actions and
  other CI systems.
- **Performance improvements**: caching mechanisms and smarter diffing to
  handle large repositories efficiently.

For more background and advanced usage, see the full documentation in the
``docs`` directory.
