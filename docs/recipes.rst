Examples & Recipes
==================

Standard release workflow
-------------------------

.. code-block:: bash

   bumpwright init
   bumpwright bump --decide
   bumpwright bump --commit --tag

Handling pre-release branches
-----------------------------

.. code-block:: bash

   git checkout -b release-branch
   bumpwright bump --level prerelease --suffix alpha

Edge cases and best practices
-----------------------------

- Ensure the working tree is clean before running ``bumpwright bump --commit``.
- Pin analyser dependencies in CI to avoid unexpected diffs.

