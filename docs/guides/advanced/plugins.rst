Custom severity mapping and plugin analysers
============================================

1. Create a plugin that reports ``print`` usage:

.. code-block:: python

   from bumpwright.analyzers import Analyzer, register
   from bumpwright.compare import Impact

   @register("no_prints", "Report usage of print statements")
   class NoPrints(Analyzer):
       def __init__(self, cfg):
           self.severity = getattr(cfg.rules, "print_call", "patch")

       def collect(self, ref):
           return Path("example.py").read_text()

       def compare(self, old, new):
           if "print(" in new and "print(" not in old:
               return [Impact(self.severity, "example.py", "Added print call")]
           return []

The optional description makes the plugin discoverable via
``get_analyzer_info("no_prints")`` and the :func:`available` helper.

2. Enable the plugin and map its finding to a version bump:

.. code-block:: toml

   [analyzers]
   no_prints = true

   [rules]
   print_call = "patch"

3. Execute the analyser:

.. code-block:: console

   bumpwright bump --decide --base HEAD^ --head HEAD

.. code-block:: text

   **bumpwright** suggests: `patch`
   - [PATCH] example.py: Added print call
