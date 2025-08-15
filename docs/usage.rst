Usage
=====

The ``semverbump`` command-line interface provides three subcommands to help
manage project versions based on public API changes. This section explains each
command, its arguments, and expected outputs.

Global options
--------------

``--config``
    Path to the configuration file. Defaults to ``semverbump.toml`` in the
    current working directory.

``decide`` – suggest a bump
---------------------------

Compare two git references and report the semantic version level they require.

**Arguments**

``--base BASE``
    Base git reference to compare against, for example ``origin/main``.
    Required.

``--head HEAD``
    Head git reference. Defaults to ``HEAD``.

``--format {text,md,json}``
    Output style. ``text`` prints plain console output, ``md`` emits Markdown,
    and ``json`` produces machine-readable data. Defaults to ``text``.

**Example**

.. code-block:: console

   semverbump decide --base origin/main --head HEAD --format md

.. code-block:: text

   **semverbump** suggests: `minor`
   - [MINOR] cli.new_command: added CLI entry 'greet'

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

``--tag``
    Create a git tag for the new version.

``--dry-run``
    Display the new version without modifying any files.

**Example**

.. code-block:: console

   semverbump bump --level minor --pyproject pyproject.toml --commit --tag

This prints the old and new versions and, when ``--commit`` and ``--tag`` are
set, commits and tags the release.

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

   semverbump auto --commit --tag

Full workflow
-------------

A typical release sequence might look like this:

.. code-block:: console

   git checkout -b feature/amazing-change
   # edit code
   git commit -am "feat: add amazing change"
   semverbump auto --commit --tag
   git push --follow-tags origin HEAD

All commands read configuration from ``semverbump.toml`` by default. Use
``--config`` to specify an alternate file.
