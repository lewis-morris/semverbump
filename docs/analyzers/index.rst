Additional Analysers
====================

Enable optional analysers in ``bumpwright.toml``:

.. code-block:: toml

   [analyzers]
   cli = true
   web_routes = true
   migrations = true

   [migrations]
   paths = ["migrations"]

You can also toggle analysers per invocation with the command-line flags
``--enable-analyzer`` and ``--disable-analyzer``.

.. toctree::
   :maxdepth: 1

   cli
   web_routes
   migrations
