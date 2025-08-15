Additional Analyzers
====================

Enable optional analyzers in ``bumpwright.toml``:

.. code-block:: toml

   [analyzers]
   cli = true
   web_routes = true

CLI Analyzer
------------
Tracks ``argparse`` or ``click`` command-line interfaces.

Web Route Analyzer
------------------
Detects HTTP route changes in Flask or FastAPI apps.

Migrations Analyzer
-------------------
Scans Alembic migrations for schema impacts. Configure paths:

.. code-block:: toml

   [migrations]
   paths = ["migrations"]
