Versioning
==========

``bumpwright`` provides multiple versioning schemes. Release-level bumps
(``major``, ``minor``, ``patch``) reset any prerelease or build/local segments.
Use the dedicated ``pre`` and ``build`` levels to update those segments
independently.

SemVer
------

The :class:`~bumpwright.version_schemes.SemverScheme` tracks prerelease and
build identifiers. Use ``pre`` and ``build`` to manage these segments while
release bumps clear them:

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
