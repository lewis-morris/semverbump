Configuration examples
======================

Adjust Bumpwright for complex projects using the examples below.

Custom version rules
--------------------

.. code-block:: toml

   [rules]
   return_type_change = "major"

Ignore paths
------------

.. code-block:: toml

   [ignore]
   paths = ["tests/**", "examples/**"]

Version file locations
----------------------

.. code-block:: toml

   [version]
   paths = ["pyproject.toml", "setup.py", "src/pkg/__init__.py"]
   ignore = ["examples/**"]
   scheme = "semver"

Automatic bump with commit and tag
----------------------------------

.. code-block:: console

   bumpwright bump --base v1.0.0 --head HEAD --commit --tag

Need to support multiple packages? See :doc:`monorepos`.
