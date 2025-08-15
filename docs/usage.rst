Usage
=====

The ``bumpwright`` command-line interface provides three subcommands to help
manage project versions based on public API changes. This section explains each
command, its arguments, and expected outputs.

Global options
--------------

``--config``
    Path to the configuration file. Defaults to ``bumpwright.toml`` in the
    current working directory.

``decide`` – suggest a bump
---------------------------

Compare two git references and report the semantic version level they require.

**Arguments**

``--base BASE``
    Base git reference to compare against, for example ``origin/main``.
    Defaults to the previous commit (``HEAD^``).

``--head HEAD``
    Head git reference. Defaults to ``HEAD``.

``--format {text,md,json}``
    Output style. ``text`` prints plain console output, ``md`` emits Markdown,
    and ``json`` produces machine-readable data. Defaults to ``text``.

**Example**

.. code-block:: console

   bumpwright decide --base origin/main --head HEAD --format md

.. code-block:: text

   **bumpwright** suggests: `minor`
   - [MINOR] cli.new_command: added CLI entry 'greet'

Running ``bumpwright decide`` without ``--base`` compares the current commit
against its parent (``HEAD^``).

.. code-block:: console

   bumpwright decide --format json

.. code-block:: json

   {
     "level": "minor",
     "impacts": [
       {"severity": "minor", "symbol": "cli.new_command", "reason": "added CLI entry 'greet'"}
     ]
   }

Omitting ``--head`` uses the current ``HEAD``:

.. code-block:: console

   bumpwright decide --base origin/main --format json

``bump`` – apply a bump
-----------------------

Update version information in ``pyproject.toml`` and other files.

**Arguments**

``--level {major,minor,patch}``
    Desired bump level. If omitted, ``--base`` and ``--head`` are used to
    determine the level automatically.

``--base BASE``
    Base git reference when auto-deciding the level. Defaults to the current
    branch's upstream.

``--head HEAD``
    Head git reference. Defaults to ``HEAD``.

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

**Example**

.. code-block:: console

   bumpwright bump --level minor --pyproject pyproject.toml --commit --tag

This prints the old and new versions and, when ``--commit`` and ``--tag`` are
set, commits and tags the release.

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

Omitting ``--base`` compares against the branch's upstream; leaving out
``--head`` uses the current ``HEAD``.

``auto`` – decide and bump
----------------------------

Combine ``decide`` and ``bump`` to infer the level and update files in one
command. When ``--base`` is omitted, the current branch's upstream is used.

Supported arguments mirror those of ``decide`` and ``bump``:

``--base``
    Base git reference. Defaults to the upstream of the current branch.

``--head``
    Head git reference. Defaults to ``HEAD``.

``--format``
    Output style, as in ``decide``.

``--pyproject``, ``--version-path``, ``--version-ignore``, ``--commit``, ``--tag``, ``--dry-run``
    Behave the same as in ``bump``.

**Example**

.. code-block:: console

   bumpwright auto --commit --tag

.. code-block:: console

   bumpwright auto --dry-run --format json

.. code-block:: json

   {
     "level": "minor",
     "old_version": "1.2.3",
     "new_version": "1.3.0",
     "impacts": []
   }

Using ``--dry-run`` previews the new version without editing files or creating
commits. Omitting ``--head`` uses the current ``HEAD``; leaving out ``--base``
falls back to the branch's upstream.


Full workflow
-------------

A typical release sequence might look like this:

.. code-block:: console

   git checkout -b feature/amazing-change
   # edit code
   git commit -am "feat: add amazing change"
   bumpwright auto --commit --tag
   git push --follow-tags origin HEAD

Common errors
-------------

* ``pyproject.toml not found`` – ensure the project file exists or provide a
  correct path via ``--pyproject``.
* ``Error: unknown revision`` – verify that the git references supplied to
  ``--base`` and ``--head`` are valid.
* ``Refusing to commit with unclean working tree`` – commit or stash changes
  before using ``--commit`` or ``--tag``.

