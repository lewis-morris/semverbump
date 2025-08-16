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


``bump --decide`` – suggest a bump
----------------------------------

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

``--repo-url URL``
    Base repository URL for linking commit hashes in Markdown output.

``--enable-analyzer NAME``
    Enable analyzer ``NAME`` in addition to configuration. Repeatable.

``--disable-analyzer NAME``
    Disable analyzer ``NAME`` even if enabled in configuration. Repeatable.

**Examples**

.. code-block:: console

   # Omitting --head defaults to the current HEAD
   bumpwright bump --decide --base origin/main --format json

.. code-block:: json

   {
     "level": "minor",
     "impacts": [
       {"severity": "minor", "symbol": "cli.new_command", "reason": "added CLI entry 'greet'"}
     ]
   }

Running ``bumpwright bump --decide`` without ``--base`` compares the current
commit against the last release commit or, if none exists, its parent (``HEAD^``).
Because this mode only inspects commits, there is no effect on the filesystem.

.. code-block:: console

   bumpwright bump --decide --format json

.. code-block:: json

   {
     "level": "minor",
     "impacts": [
       {"severity": "minor", "symbol": "cli.new_command", "reason": "added CLI entry 'greet'"}
     ]
   }

Omitting ``--head`` uses the current ``HEAD``:

.. code-block:: console

   bumpwright bump --decide --base origin/main --format json

``bump`` – apply a bump
-----------------------

Update version information in ``pyproject.toml`` and other files.
By default, ``bumpwright`` also searches ``setup.py``, ``setup.cfg`` and any
``__init__.py``, ``version.py`` or ``_version.py`` files for a version
assignment. These locations can be customised via the ``[version]`` section in
``bumpwright.toml`` or augmented with ``--version-path`` and
``--version-ignore`` to add or exclude patterns.

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

``--enable-analyzer NAME``
    Enable analyzer ``NAME`` in addition to configuration. Repeatable.

``--disable-analyzer NAME``
    Disable analyzer ``NAME`` even if enabled in configuration. Repeatable.

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

Generate a Markdown changelog with commit links:

.. code-block:: console

   bumpwright bump --dry-run --format md --repo-url https://github.com/me/project --changelog -

.. code-block:: text

   ## [v1.2.4] - 2024-04-01
   - [abc123](https://github.com/me/project/commit/abc123) feat: change

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

