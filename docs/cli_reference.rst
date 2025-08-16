CLI reference
=============

The ``bumpwright`` command-line interface helps manage project version bumps.
For an introduction see :doc:`usage` and :doc:`configuration`.

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

Example:

.. code-block:: console

   $ bumpwright bump --level patch
   Bumped version: 0.1.0 -> 0.1.1 (patch)
   Updated files: pyproject.toml

The ``--config`` option reads from :doc:`configuration`, while
``--enable-analyser`` and ``--disable-analyser`` control optional analysers
as described in :doc:`analysers/index`. When ``--commit`` or ``--tag`` is
specified, bumpwright first checks for a clean working tree and aborts if
uncommitted changes are present.
