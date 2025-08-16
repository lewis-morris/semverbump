Custom analysers
================

Extend Bumpwright with project-specific logic.

Extension points
----------------
Hook into the analysis pipeline via entry points.

Contract
--------
Each analyser must expose ``impact`` and ``bump`` methods.

Examples
--------
See existing analysers under ``bumpwright/analysers`` for patterns to copy.

