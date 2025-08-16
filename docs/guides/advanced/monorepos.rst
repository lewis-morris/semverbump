Handling multi-package repositories
===================================

1. Configure version file paths for each package in ``bumpwright.toml``:

.. code-block:: toml

   [version]
   paths = [
     "packages/pkg_a/pyproject.toml",
     "packages/pkg_b/pyproject.toml",
   ]

2. Run ``bumpwright`` for the package that changed:

.. code-block:: console

   bumpwright bump --level minor --pyproject packages/pkg_a/pyproject.toml

.. code-block:: text

   Updated packages/pkg_a/pyproject.toml from 0.4.1 to 0.5.0
