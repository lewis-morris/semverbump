Advanced Usage
==============

Customize rules for version decisions:

.. code-block:: toml

   [rules]
   return_type_change = "major"

Exclude paths from API scanning:

.. code-block:: toml

   [ignore]
   paths = ["tests/**", "examples/**"]

Specify additional version file locations:

.. code-block:: toml

   [version]
   paths = ["pyproject.toml", "setup.py", "src/pkg/__init__.py"]
   ignore = ["examples/**"]

Apply a bump and commit/tag automatically:

.. code-block:: console

   semverbump auto --base v1.0.0 --head HEAD --commit --tag
