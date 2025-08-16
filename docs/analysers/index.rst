Additional Analysers
====================

The CLI, web route, migration and OpenAPI analysers are **opt-in** and disabled
by default. Enable them in ``bumpwright.toml``:

.. code-block:: toml

   [analysers]
   cli = true        # enable CLI analysis
   web_routes = true # enable web route analysis
   migrations = true # enable migrations analysis
   openapi = true    # enable OpenAPI analysis

   [migrations]
   paths = ["migrations"]  # directories with Alembic scripts

   [openapi]
   paths = ["openapi.yaml"]

You can also toggle analysers per invocation with the command-line flags
``--enable-analyser`` and ``--disable-analyser``.

.. toctree::
   :maxdepth: 1

   cli
   web_routes
   migrations
   openapi
