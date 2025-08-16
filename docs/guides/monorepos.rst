Handling multi-package repositories
===================================

Bumpwright works in monorepos with several packages by targeting each package
independently.

Configure version file paths
----------------------------

Define where versions are stored for each package in ``bumpwright.toml``:

.. code-block:: toml

   [version]
   paths = [
     "packages/pkg_a/pyproject.toml",
     "packages/pkg_b/pyproject.toml",
   ]
   scheme = "semver"

Run Bumpwright for the changed package
--------------------------------------

Invoke Bumpwright against the package that changed:

.. code-block:: console

   bumpwright bump --level minor --pyproject packages/pkg_a/pyproject.toml

.. code-block:: text

   Updated packages/pkg_a/pyproject.toml from 0.4.1 to 0.5.0
