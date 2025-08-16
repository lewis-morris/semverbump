Usage
=====

The ``bumpwright`` command-line interface provides tools for suggesting and
applying semantic version bumps based on public API changes.

.. autoprogram:: bumpwright.cli:build_parser
   :prog: bumpwright

Examples
--------

Initialise a baseline release commit:

.. code-block:: console

   bumpwright init

Suggest a bump between two refs:

.. code-block:: console

   bumpwright bump --decide --base origin/main --format json

Apply a bump and preview the result:

.. code-block:: console

   bumpwright bump --dry-run --format json
