Examples & Recipes
==================

Monorepo or multi-package layout
--------------------------------

.. code-block:: bash

   bumpwright bump --public-roots pkg_a src/pkg_b

Run analyses across multiple packages while keeping their APIs distinct.

Pre-releases and tags
---------------------

.. code-block:: bash

   bumpwright bump --level prerelease --suffix rc

Create release candidates without touching the stable version line.

Ignoring paths / narrowing public roots
---------------------------------------

.. code-block:: bash

   bumpwright bump --ignore tests/fixtures --public-roots src

Exclude helper code and limit scanning to your public modules.

Running locally vs CI
---------------------

.. code-block:: bash

   bumpwright bump --base main --head HEAD~1

Compare the latest commit against ``main`` for local checks.

JSON output + machine consumption
---------------------------------

.. code-block:: bash

   bumpwright bump --format json | jq '.suggested'

Pipe structured results into other tools or CI steps.

