CLI reference
=============

The ``bumpwright`` command-line interface helps manage project version bumps.
For an introduction see :doc:`usage/index` and :doc:`configuration`.

Top-level command
-----------------

.. click:: _bumpwright_click:cli
   :prog: bumpwright

init
----

Create a baseline release commit.

.. click:: _bumpwright_click:init
   :prog: bumpwright init

Example:

.. code-block:: console

   $ bumpwright init
   Created baseline release commit.

bump
----

Apply a version bump and update project files.

.. click:: _bumpwright_click:bump
   :prog: bumpwright bump

Examples:

Create a patch release, link commits to the repository, and append release
notes to ``CHANGELOG.md``:

.. code-block:: console

   $ bumpwright bump --level patch --repo-url https://github.com/me/project --changelog CHANGELOG.md
   Bumped version: 0.1.0 -> 0.1.1 (patch)
   Updated files: pyproject.toml, CHANGELOG.md

Suggest a bump without modifying files:

.. code-block:: console

   $ bumpwright bump --decide --base origin/main --format text
   Suggested bump: patch

   - [PATCH] docs: clarify usage

By default the command searches for version strings in ``pyproject.toml``,
``setup.py``, ``setup.cfg``, and any ``__init__.py``, ``version.py``, or
``_version.py`` files. Extra paths may be supplied with ``--version-path`` and
individual files can be omitted with ``--version-ignore``.

The ``--config`` option reads from :doc:`configuration`, while
``--enable-analyser`` and ``--disable-analyser`` control optional analysers
as described in :doc:`analysers/index`. When ``--commit`` or ``--tag`` is
specified, bumpwright first checks for a clean working tree and aborts if
uncommitted changes are present.
