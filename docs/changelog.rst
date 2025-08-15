Changelog
=========

``bumpwright`` can generate Markdown release notes when bumping versions.
The ``--changelog`` option for the ``bump`` subcommand controls where these
notes go and how they are emitted.

Using ``--changelog``
---------------------

``--changelog FILE``
    Append release notes for the new version to ``FILE``.

``--changelog``
    Print the changelog entry to standard output instead of updating a file.

If omitted, no changelog entry is produced.

Format
------

Entries follow a simple Markdown structure:

.. code-block:: markdown

   ## [v1.2.4] - 2024-09-14
   - a1b2c3d fix: correct typo
   - d4e5f6g feat: add new option

Each entry begins with a version heading and date, followed by a list of commit
shas and subjects since the previous release.

Configuration
-------------

Projects can set a default changelog path in ``bumpwright.toml`` so the
``bump`` command writes to that location when ``--changelog`` is omitted:

.. code-block:: toml

   [changelog]
   path = "CHANGELOG.md"

With this configuration, running ``bumpwright bump`` automatically appends the
release notes to ``CHANGELOG.md``. To print to stdout instead, invoke
``bumpwright bump --changelog``.
