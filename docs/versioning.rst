Versioning
==========

``bumpwright`` supports multiple versioning schemes. The CLI defaults to Semantic Versioning (``semver``) but can operate in `PEP 440`_ mode by setting ``[version].scheme = "pep440"`` in ``bumpwright.toml``. Release-level bumps (``major``, ``minor``, ``patch``) reset any prerelease or build/local segments.

.. list-table:: Bump level effects
   :header-rows: 1

   * - Level
     - Prerelease segment
     - Build/local segment
   * - ``major``
     - cleared
     - cleared
   * - ``minor``
     - cleared
     - cleared
   * - ``patch``
     - cleared
     - cleared

Return type changes are treated as a ``minor`` bump by default. Override this behaviour via ``rules.return_type_change`` in :doc:`configuration`.

SemVer
------

Semantic Versioning uses ``MAJOR.MINOR.PATCH`` segments with optional prerelease or build metadata. Release bumps drop any prerelease or build segments.

PEP 440
-------

PEP 440 follows a similar structure using identifiers like ``rc1`` for prereleases and ``+local`` for local versions. Release bumps remove these segments.

.. _PEP 440: https://peps.python.org/pep-0440/
