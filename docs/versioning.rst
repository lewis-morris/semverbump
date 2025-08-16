Versioning
==========

``bumpwright`` provides multiple versioning schemes and preserves prerelease
and build metadata when bumping versions.

.. note::

   The :func:`bumpwright.versioning.bump_string` utility supports
   additional ``pre`` and ``build`` increments. The CLI exposes only the
   ``major``, ``minor``, and ``patch`` levels.

SemVer
------

The :class:`~bumpwright.version_schemes.SemverScheme` tracks prerelease and
build identifiers. Both parts can be incremented independently:

.. code-block:: python

   from bumpwright.versioning import bump_string
   bump_string("1.0.0-alpha.1", "pre", scheme="semver")  # 1.0.0-alpha.2
   bump_string("1.0.0+build.1", "build", scheme="semver")  # 1.0.0+build.2

PEP 440
-------

The :class:`~bumpwright.version_schemes.Pep440Scheme` also manages pre-release
segments (``a1``, ``rc1``) and local version identifiers:

.. code-block:: python

   bump_string("1.0.0rc1", "pre", scheme="pep440")    # 1.0.0rc2
   bump_string("1.0.0+local.1", "build", scheme="pep440")  # 1.0.0+local.2

Use these additional bump levels to manage prerelease and build metadata without
altering the main release components.
