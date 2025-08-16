Additional Analysers
====================

Enable optional analysers in ``bumpwright.toml``:

.. code-block:: toml

   [analysers]
   cli = true
   web_routes = true
   migrations = true

   [migrations]
   paths = ["migrations"]

You can also toggle analysers per invocation with the command-line flags
``--enable-analyser`` and ``--disable-analyser``.

.. toctree::
   :maxdepth: 1

   cli
   web_routes
   migrations
