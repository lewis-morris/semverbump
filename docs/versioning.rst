Versioning
==========

``bumpwright`` supports multiple versioning schemes. The CLI defaults to
Semantic Versioning (``semver``) but can operate in `PEP 440`_ mode by setting
``[version].scheme = "pep440"`` in ``bumpwright.toml``. Release-level bumps
(``major``, ``minor``, ``patch``) reset any prerelease or build/local segments.
Library callers may use the dedicated ``pre`` and ``build`` levels to update
those segments independently.

.. note::

   The :func:`bumpwright.versioning.bump_string` helper accepts the extra
   ``pre`` and ``build`` levels. The command-line interface exposes only the
   ``major``, ``minor``, and ``patch`` options.

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
   * - ``pre``
     - incremented
     - unchanged
   * - ``build``
     - unchanged
     - incremented

Examples using the default SemVer scheme:

.. code-block:: python

   from bumpwright.versioning import bump_string
   bump_string("1.0.0-alpha.1", "pre", scheme="semver")    # 1.0.0-alpha.2
   bump_string("1.0.0+build.1", "build", scheme="semver")  # 1.0.0+build.2

Return type changes are treated as a ``minor`` bump by default. Override this
behavior via ``rules.return_type_change`` in :doc:`configuration`:

.. code-block:: toml

   [rules]
   return_type_change = "major"

SemVer
------

The :class:`~bumpwright.version_schemes.SemverScheme` tracks prerelease and

build identifiers. Both parts can be incremented independently. Numeric
components are validated against the SemVer spec, so leading zeros such as
``01.0.0`` raise :class:`ValueError`:

.. code-block:: python

   from bumpwright.versioning import bump_string
   bump_string("1.0.0-alpha.1", "pre", scheme="semver")  # 1.0.0-alpha.2
   bump_string("1.0.0+build.1", "build", scheme="semver")  # 1.0.0+build.2
   bump_string("1.0.0-alpha.1+build.1", "patch", scheme="semver")  # 1.0.1

PEP 440
-------

The :class:`~bumpwright.version_schemes.Pep440Scheme` also manages pre-release
segments (``a1``, ``rc1``) and local version identifiers. As with SemVer,
release bumps drop these components:

.. code-block:: python

   bump_string("1.0.0rc1", "pre", scheme="pep440")    # 1.0.0rc2
   bump_string("1.0.0+local.1", "build", scheme="pep440")  # 1.0.0+local.2
   bump_string("1.0.0rc1+local.1", "patch", scheme="pep440")  # 1.0.1

Use these bump levels to manage prerelease and build metadata without altering
the main release components.

.. _PEP 440: https://peps.python.org/pep-0440/
