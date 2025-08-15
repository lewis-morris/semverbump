Basic Usage
===========

To suggest a version bump between two git references:

.. code-block:: console

   semverbump decide --base origin/main --head HEAD

To apply a bump directly to ``pyproject.toml``:

.. code-block:: console

   semverbump bump --level minor --pyproject pyproject.toml

Both commands read configuration from ``semverbump.toml`` by default. Use
``--config`` to specify an alternate file.
