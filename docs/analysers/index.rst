Additional Analysers
====================

The CLI, gRPC, web route and migration analysers are **opt-in** and disabled by
default. Enable them in ``bumpwright.toml``:

.. code-block:: toml

   [analysers]
   cli = true        # enable CLI analysis
   grpc = true       # enable gRPC analysis
   web_routes = true # enable web route analysis
   migrations = true # enable migrations analysis

   [migrations]
   paths = ["migrations"]  # directories with Alembic scripts

You can also toggle analysers per invocation with the command-line flags
``--enable-analyser`` and ``--disable-analyser``.

.. toctree::
   :maxdepth: 1

   cli
   grpc
   web_routes
   migrations
