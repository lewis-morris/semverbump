Usage
=====

Suggesting a bump
-----------------

To discover the next semantic version between two git references, run:

.. code-block:: console

   semverbump decide --base origin/main --head HEAD --format text

Example output:

.. code-block:: text

   Suggested bump: minor
   - [MINOR] cli.new_command: added CLI entry 'greet'

Set ``--format md`` for Markdown or ``--format json`` for machine-readable
results.

Applying a bump
---------------

Once the level is known, apply it directly to ``pyproject.toml``:

.. code-block:: console

   semverbump bump --level minor --pyproject pyproject.toml --commit --tag

This prints the old and new versions and, with the flags above, commits and tags
the change.

If ``--level`` is omitted, provide ``--base`` and ``--head`` and the command
will automatically decide in the same fashion as ``decide``.

Full workflow
-------------

A typical release sequence might look like this:

.. code-block:: console

   git checkout -b feature/amazing-change
   # edit code
   git commit -am "feat: add amazing change"
   semverbump decide --base origin/main --head HEAD --format md
   semverbump bump --level minor --commit --tag
   git push --follow-tags origin HEAD

Both commands read configuration from ``semverbump.toml`` by default. Use
``--config`` to specify an alternate file.
