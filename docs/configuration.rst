Configuration
=============

``bumpwright`` reads settings from ``bumpwright.toml``. If the file is missing
or a section is omitted, built-in defaults are used. To use a different
location, pass ``--config`` on the command line or supply a ``config_path`` or
loaded :class:`bumpwright.config.Config` object when calling library APIs.

Example configuration showing all available sections and their default values:

.. code-block:: toml

    [project]
    package = ""
    public_roots = ["."]

    [ignore]
    paths = ["tests/**", "examples/**", "scripts/**"]

    [rules]
    return_type_change = "minor"  # or "major"

    [analysers]
    cli = false
    web_routes = false
    migrations = false

    [migrations]
    paths = ["migrations"]

    [changelog]
    path = ""
    template = ""

    [version]
    paths = ["pyproject.toml", "setup.py", "setup.cfg", "**/__init__.py", "**/version.py", "**/_version.py"]
    ignore = ["build/**", "dist/**", "*.egg-info/**", ".eggs/**", ".venv/**", "venv/**", ".env/**", "**/__pycache__/**"]
    scheme = "semver"

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

By default, ``bumpwright`` skips ``tests/**``, ``examples/**``, and ``scripts/**``
when scanning for public API changes.

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

Each key under ``[analysers]`` toggles a plugin. Unknown names raise an error
at run time. Command-line flags ``--enable-analyser`` and ``--disable-analyser``
temporarily override these settings. Built-in analysers include:

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
   * - ``migrations``
     - Scans Alembic migrations for schema impacts.
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

Controls where version strings are read and updated and which versioning
scheme is applied.

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
     - ``["build/**", "dist/**", "*.egg-info/**", ".eggs/**", ".venv/**", "venv/**", ".env/**", "**/__pycache__/**"]``
     - Glob patterns excluded from version replacement.
   * - ``scheme``
     - str
     - ``"semver"``
     - Versioning scheme used when bumping. Supported values include
       ``"semver"`` and ``"pep440"``. See :doc:`../versioning` for details.

Version replacement ignores build and environment artefacts by default:
``build/**``, ``dist/**``, ``*.egg-info/**``, ``.eggs/**``, ``.venv/**``,
``venv/**``, ``.env/**``, and ``**/__pycache__/**``.

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
     - Default file appended when running ``bumpwright bump`` with ``--changelog``
       omitted. Empty string means no default file.
   * - ``template``
     - str
     - ``""``
     - Jinja2 template file for changelog entries. Empty string selects the
       built-in template.

All sections and keys are optional; unspecified values fall back to the
defaults shown above.
