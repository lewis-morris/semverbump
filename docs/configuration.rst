Configuration
=============

``semverbump`` reads settings from ``semverbump.toml``. The file supports these
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

   [version]
   paths = ["pyproject.toml", "setup.py", "setup.cfg", "**/*.py"]
   ignore = []

Enable an analyzer by setting its value to ``true`` under ``[analyzers]``.

[project]
---------

Project metadata and layout.

``package``
    Name of the top-level Python package. Used for version discovery when the
    package exposes ``__version__``.

``public_roots``
    Directories containing public API modules. Only files under these paths are
    scanned when comparing APIs.

``index_file``
    Primary project metadata file, typically ``pyproject.toml``. Used by version
    tooling.

[ignore]
--------

``paths``
    Glob patterns excluded from all analyzers. Useful for skipping tests,
    examples, or generated code.

[rules]
-------

Rules influencing the suggested semantic version.

``return_type_change``
    Impact level when a function or method return type changes. ``minor`` treats
    the change as a backwards-compatible enhancement, while ``major`` marks it as
    a breaking change.

[analyzers]
-----------

Enable optional analyzer plugins. Each key corresponds to an analyzer name and
its boolean value toggles it on or off.

Common built-in analyzers include:

``cli``
    Tracks ``argparse`` or ``click`` command-line interfaces.

``web_routes``
    Detects HTTP route changes in Flask or FastAPI applications.

[migrations]
-----------

Configuration for the Alembic migrations analyzer.

``paths``
    Directories containing migration scripts. Set to an empty list to disable
    migration analysis.

[version]
--------

Control how ``semverbump version`` searches for and updates version strings.

``paths``
    Glob patterns scanned for version declarations.

``ignore``
    Glob patterns excluded from version scanning.

Real-world example
------------------

A FastAPI service may expose CLI entry points and manage database migrations in
custom directories. This configuration enables multiple analyzers and custom
paths:

.. code-block:: toml

   [project]
   package = "acme"
   public_roots = ["src/acme", "plugins/acme_ext"]
   index_file = "pyproject.toml"

   [ignore]
   paths = ["tests/**", "docs/**"]

   [rules]
   return_type_change = "major"

   [analyzers]
   cli = true
   web_routes = true

   [migrations]
   paths = ["database/migrations", "plugins/**/migrations"]

   [version]
   paths = ["pyproject.toml", "src/acme/__init__.py"]
   ignore = ["**/draft_*.py"]

Sample ``semverbump.toml``
-------------------------

.. code-block:: toml

   # semverbump.toml
   [project]
   package = "acme"                        # project package name
   public_roots = ["src/acme"]             # public API roots
   index_file = "pyproject.toml"           # main project metadata file

   [ignore]
   paths = ["tests/**", "docs/**"]         # directories to skip

   [rules]
   return_type_change = "major"            # major bump on return type change

   [analyzers]
   cli = true                              # enable CLI analyzer
   web_routes = true                       # enable web route analyzer

   [migrations]
   paths = ["database/migrations"]         # Alembic migration locations

   [version]
   paths = ["pyproject.toml", "src/acme/__init__.py"]  # files with version strings
   ignore = ["**/draft_*.py"]              # exclude draft files
