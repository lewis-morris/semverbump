Configuration
=============

``bumpwright`` reads settings from ``bumpwright.toml``. The file supports these
sections with defaults shown:

.. code-block:: toml

   [project]
   package = ""
   public_roots = ["."]
   index_file = "pyproject.toml"

   [ignore]
   paths = ["tests/**", "examples/**", "scripts/**"]

   [rules]
   return_type_change = "minor"  # or "major"

   [analyzers]
   cli = false

   [migrations]
   paths = ["migrations"]

Enable an analyser by setting its value to ``true`` under ``[analyzers]``.
