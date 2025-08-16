Configuration
=============

``bumpwright`` reads settings from ``bumpwright.toml``. If the file is missing
or a section is omitted, built-in defaults are used.

Example configuration showing all available sections and their default values:

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
   web_routes = false

   [migrations]
   paths = ["migrations"]

   [changelog]
   path = ""

   [version]
   paths = ["pyproject.toml", "setup.py", "setup.cfg", "**/*.py"]
   ignore = []

Set an analyser value to ``true`` to enable it.

Sections
--------

Project
~~~~~~~

.. list-table:: Project options
   :header-rows: 1

   * - Key
     - Type
     - Default
     - Description
   * - ``package``
     - str
     - ``""``
     - Importable package containing the project's code. When empty the
       repository layout is used.
   * - ``public_roots``
     - list[str]
     - ``["."]``
     - Paths whose contents constitute the public API.
   * - ``index_file``
     - str
     - ``"pyproject.toml"``
     - File containing project metadata used for version discovery.

Ignore
~~~~~~

.. list-table:: Ignore options
   :header-rows: 1

   * - Key
     - Type
     - Default
     - Description
   * - ``paths``
     - list[str]
     - ``["tests/**", "examples/**", "scripts/**"]``
     - Glob patterns excluded from analysis.

Rules
~~~~~

.. list-table:: Rule options
   :header-rows: 1

   * - Key
     - Type
     - Default
     - Description
   * - ``return_type_change``
     - ``"minor"`` | ``"major"``
     - ``"minor"``
     - Version bump level when a function's return type changes.

Analysers
~~~~~~~~~

Each key under ``[analyzers]`` toggles a plugin. Unknown names raise an error
at run time. Built-in analysers include:

.. list-table:: Available analysers
   :header-rows: 1

   * - Name
     - Description
     - Default
   * - ``cli``
     - Detects changes to command-line interfaces implemented with
       ``argparse`` or ``click``.
     - ``false``
   * - ``web_routes``
     - Tracks additions or removals of web routes in frameworks such as
       Flask or FastAPI.
     - ``false``

Migrations
~~~~~~~~~~

.. list-table:: Migration options
   :header-rows: 1

   * - Key
     - Type
     - Default
     - Description
   * - ``paths``
     - list[str]
     - ``["migrations"]``
     - Directories containing Alembic migration scripts to inspect.

Version
~~~~~~~

Controls where version strings are read and updated.

.. list-table:: Version options
   :header-rows: 1

   * - Key
     - Type
     - Default
     - Description
   * - ``paths``
     - list[str]
     - ``["pyproject.toml", "setup.py", "setup.cfg", "**/__init__.py", "**/version.py", "**/_version.py"]``
     - Glob patterns scanned for version declarations.
   * - ``ignore``
     - list[str]
     - ``[]``
     - Glob patterns excluded from version replacement.

Command-line options ``--version-path`` and ``--version-ignore`` extend these
defaults for one-off runs.

Changelog
~~~~~~~~~

.. list-table:: Changelog options
   :header-rows: 1

   * - Key
     - Type
     - Default
     - Description
   * - ``path``
     - str
     - ``""``
     - Default file appended when running ``bumpwright bump`` with
       ``--changelog`` omitted. Empty string means no default file.

All sections and keys are optional; unspecified values fall back to the
defaults shown above.
