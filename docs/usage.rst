Usage
=====

The ``bumpwright`` command-line interface provides two subcommands to help
manage project versions based on public API changes. By default, the
``bump`` subcommand compares the current commit against the last release
commit, or the previous commit (``HEAD^``) when no release exists. This section
explains each command, its arguments, and expected outputs.

Global options
--------------

``--config``
    Path to the configuration file. Defaults to ``bumpwright.toml`` in the
    current working directory.

``init`` – create a baseline
-----------------------------

Record an empty ``chore(release): initialise baseline`` commit so that future runs
of bumpwright have a starting point for comparisons. Run this once when first
adopting bumpwright or after importing an existing project without prior
release commits.

**Examples**

.. code-block:: console

   bumpwright init


``bumpwright bump --decide`` – suggest a bump
---------------------------------------------

Compare two git references and report the semantic version level they
require.

**Arguments**

``--base BASE``
    Base git reference to compare against, for example ``origin/main``.
    Defaults to the last release commit if available, otherwise the previous
    commit (``HEAD^``).

``--head HEAD``
    Head git reference. Defaults to ``HEAD``.

``--format {text,md,json}``
    Output style. ``text`` prints plain console output, ``md`` emits Markdown,
    and ``json`` produces machine-readable data. Defaults to ``text``.

``--enable-analyser NAME``
    Enable analyser ``NAME`` in addition to configuration. Repeatable.

``--disable-analyser NAME``
    Disable analyser ``NAME`` even if enabled in configuration. Repeatable.

**Examples**

.. code-block:: console

   # Omitting --head defaults to the current HEAD
   bumpwright bump --decide --base origin/main --format json

.. code-block:: json

   {
     "level": "minor",
     "confidence": 1.0,
     "reasons": ["added CLI entry 'greet'"],
     "impacts": [
       {"severity": "minor", "symbol": "cli.new_command", "reason": "added CLI entry 'greet'"}
     ]
   }

The ``confidence`` value reflects the proportion of impacts that led to the
suggested level, while ``reasons`` summarise those impacts.

Running ``bumpwright bump --decide`` without ``--base`` compares the current
commit against the last release commit or, if none exists, its parent (``HEAD^``).
Because this mode only inspects commits, there is no effect on the filesystem.



``bumpwright bump`` – apply a bump
----------------------------------

Update version information in ``pyproject.toml`` and other files.
By default, ``bumpwright`` also searches ``setup.py``, ``setup.cfg`` and any
``__init__.py``, ``version.py`` or ``_version.py`` files for a version
assignment. Files inside common build artefacts and virtual environments are
ignored by default (``build/**``, ``dist/**``, ``*.egg-info/**``, ``.eggs/**``,
``.venv/**``, ``venv/**``, ``.env/**`` and ``**/__pycache__/**``). These
locations can be customised via the ``[version]`` section in ``bumpwright.toml``
or augmented with ``--version-path`` and ``--version-ignore`` to add or exclude
patterns.


**Arguments**

``--level {major,minor,patch}``
    Desired bump level. If omitted, ``--base`` and ``--head`` are used to
    determine the level automatically.

``--base BASE``
    Base git reference when auto-deciding the level. Defaults to the last
    release commit if available, otherwise the previous commit (``HEAD^``).

``--head HEAD``
    Head git reference. Defaults to ``HEAD``.

``--format {text,md,json}``
    Output style. ``text`` prints plain console output, ``md`` emits Markdown,
    and ``json`` produces machine-readable data. Defaults to ``text``.

``--repo-url URL``
    Base repository URL for linking commit hashes in Markdown output.

``--enable-analyser NAME``
    Enable analyser ``NAME`` in addition to configuration. Repeatable.

``--disable-analyser NAME``
    Disable analyser ``NAME`` even if enabled in configuration. Repeatable.

``--changelog [FILE]``
    Append release notes for the new version to ``FILE``.
    When ``FILE`` is omitted or set to ``-``, the changelog entry is printed to
    standard output. If the option is omitted entirely, the
    ``[changelog].path`` setting provides a default location. See
    :doc:`configuration` for more detail.

``--changelog-template PATH``
    Jinja2 template file used when rendering changelog entries. Defaults to the
    built-in template or ``[changelog].template`` when configured. See
    :doc:`configuration` for more detail.

``--pyproject PATH``
    Path to the project's ``pyproject.toml`` file. Defaults to
    ``pyproject.toml``.

``--version-path GLOB``
    Glob pattern for files that contain the project version. May be repeated to
    update multiple locations.

``--version-ignore GLOB``
    Glob pattern for paths to exclude from version updates.

``--commit``
    Create a git commit for the version change.

    .. note::
        The version will bump on every invocation unless the change is
        committed or reverted.

``--tag``
    Create a git tag for the new version.

``--dry-run``
    Display the new version without modifying any files.

**Examples**

.. code-block:: console

   bumpwright bump --level minor --pyproject pyproject.toml --commit --tag

This prints the old and new versions and, when ``--commit`` and ``--tag`` are
set, commits and tags the release. Omitting ``--base`` compares against the
last release commit or the previous commit (``HEAD^``), and omitting
``--head`` assumes ``HEAD``.

Changelog generation
--------------------

``bumpwright`` can generate Markdown release notes when bumping versions. The
``--changelog`` option controls where these notes go and how they are emitted.

.. code-block:: console

   bumpwright bump --dry-run --format md --repo-url https://github.com/me/project --changelog -

.. code-block:: text

   ## [v1.2.4] - 2024-04-01
   - [abc123](https://github.com/me/project/commit/abc123) feat: change

Entries follow a simple Markdown structure:

.. code-block:: markdown

   ## [v1.2.4] - 2024-09-14
   - a1b2c3d fix: correct typo
   - d4e5f6g feat: add new option

Each entry begins with a version heading and date, followed by a list of commit
shas and subjects since the previous release.

Templates receive the following variables:

``version``
    The new version string.
``date``
    Current date in ISO format.
``commits``
    List of mappings with ``sha``, ``subject``, and optional ``link`` keys for
    commits since the previous release.

Projects can set a default changelog path in ``bumpwright.toml`` so the
``bump`` command writes to that location when ``--changelog`` is omitted:

.. code-block:: toml

   [changelog]
   path = "CHANGELOG.md"
   template = "changelog.j2"

With this configuration, running ``bumpwright bump`` automatically appends the
release notes to ``CHANGELOG.md`` using ``changelog.j2``. To print to stdout
instead, invoke ``bumpwright bump --changelog`` (or pass ``--changelog -`` for
clarity).

To preview changes without touching the filesystem, combine ``--dry-run`` with
JSON output:

.. code-block:: console

   bumpwright bump --dry-run --format json

.. code-block:: json

   {
     "old_version": "1.2.3",
     "new_version": "1.2.4",
     "level": "patch"
   }

Omitting ``--base`` compares against the last release commit or the previous
commit (``HEAD^``); leaving out ``--head`` uses the current ``HEAD``.


Full workflow
-------------

A typical release sequence might look like this:

.. code-block:: console

   git checkout -b feature/amazing-change
   # edit code
   git commit -am "feat: add amazing change"
   bumpwright bump --commit --tag
   git push --follow-tags origin HEAD


All commands read configuration from ``bumpwright.toml`` by default. Use
``--config`` to specify an alternate file.

Common errors
-------------

``pyproject.toml`` not found
    Ensure you run the command at the project root or pass ``--pyproject`` with
    the correct path.

Changes not applied after running
    The ``--dry-run`` flag previews the bump without touching files. Remove it
    and, if desired, add ``--commit`` and ``--tag`` to persist the change.

