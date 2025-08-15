Configuration
=============

``semverbump`` reads settings from ``semverbump.toml``. The file supports the
sections below with defaults shown:

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

   [version]
   paths = ["pyproject.toml", "setup.py", "setup.cfg", "**/*.py"]
   ignore = []

Section details
---------------

``[project]``
^^^^^^^^^^^^^
* **package** – Name of the Python package to analyze. Determines which
  package's API is examined and where version strings are updated.
* **public_roots** – Directories exposing the public API. Only files under
  these roots influence bump decisions.
* **index_file** – Project metadata file, typically ``pyproject.toml`` or
  ``setup.cfg``.

``[ignore]``
^^^^^^^^^^^^
* **paths** – Glob patterns excluded from scanning. Useful for tests or
  generated code.

``[rules]``
^^^^^^^^^^^
* **return_type_change** – Bump level when only a function's return type
  changes. ``"minor"`` keeps backward compatibility while ``"major"`` treats it
  as breaking.

``[analyzers]``
^^^^^^^^^^^^^^^
Each key enables an optional analyzer plugin when set to ``true``.

* **cli** – Track changes to ``argparse`` or ``click`` command-line
  interfaces.
* **web_routes** – Detect HTTP route changes in Flask or FastAPI apps.

``[migrations]``
^^^^^^^^^^^^^^^^
* **paths** – Locations of database migration scripts used by the migrations
  analyzer.

``[version]``
^^^^^^^^^^^^^
* **paths** – Files containing the project version string to update during
  ``semverbump auto``.
* **ignore** – Glob patterns to skip when replacing version strings.

Real-world example
------------------

The example below enables multiple analyzers and customizes search paths:

.. code-block:: toml

   [project]
   package = "acme"
   public_roots = ["src/acme", "src/cli"]
   index_file = "pyproject.toml"

   [ignore]
   paths = ["tests/**", "docs/_build/**"]

   [analyzers]
   cli = true
   web_routes = true

   [migrations]
   paths = ["src/acme/db/migrations"]

   [version]
   paths = ["pyproject.toml", "src/acme/__init__.py"]

Complete sample ``semverbump.toml``
-----------------------------------

.. code-block:: toml

   # semverbump.toml
   [project]
   package = "acme"                # Root Python package name
   public_roots = ["src/acme"]     # Directories exposing public API
   index_file = "pyproject.toml"   # Project metadata file

   [ignore]
   paths = ["tests/**"]            # Paths to skip during analysis

   [rules]
   return_type_change = "minor"    # Use "major" to treat return-type changes as breaking

   [analyzers]
   cli = true                       # Enable CLI analyzer
   web_routes = true                # Enable Web route analyzer

   [migrations]
   paths = ["src/acme/migrations"] # Location of migration scripts

   [version]
   paths = ["pyproject.toml", "src/acme/__init__.py"]  # Files with version string
   ignore = ["docs/**"]            # Files to leave untouched when bumping version

Enable an analyzer by setting its value to ``true`` under ``[analyzers]``.

