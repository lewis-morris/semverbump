Examples & Recipes
==================

Monorepo or multi-package layout
--------------------------------

.. code-block:: bash

   bumpwright bump --pyproject packages/pkg_a/pyproject.toml

Analyse a single package in a monorepo while keeping other packages untouched.

Commit and tag
--------------

.. code-block:: bash

   bumpwright bump --level patch --commit --tag

Create a release commit and matching tag.

Running locally vs CI
---------------------

.. code-block:: bash

   bumpwright bump --base main --head HEAD~1

Compare the latest commit against ``main`` for local checks.

JSON output + machine consumption
---------------------------------

.. code-block:: bash

   bumpwright bump --format json | jq '.level'

Pipe structured results into other tools or CI steps.
