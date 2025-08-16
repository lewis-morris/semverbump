Additional Analyzers
====================

Enable optional analyzers in ``bumpwright.toml``:

.. code-block:: toml

   [analyzers]
   cli = true
   web_routes = true
   migrations = true

   [migrations]
   paths = ["migrations"]

.. toctree::
   :maxdepth: 1

   cli
   web_routes
   migrations
