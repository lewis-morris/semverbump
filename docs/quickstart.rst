Quickstart
==========

Start with a tiny example project to see **bumpwright** in action.

#. Install the package.

   .. code-block:: bash

      pip install bumpwright

   Install the CLI from PyPI.

#. Create a minimal repository.

   .. code-block:: bash

      mkdir demo && cd demo
      git init
      cat > pyproject.toml <<'EOF'
      [project]
      name = "demo"
      version = "0.1.0"
      EOF
      git add pyproject.toml
      git commit -m "chore: initial commit"

   Set up Git and a baseline ``pyproject.toml``. The configuration file
   shown here is kept intentionally simple; see :doc:`configuration` for
   detailed options.

#. Initialise configuration.

   .. code-block:: bash

      bumpwright init

   Records a ``chore(release): initialise baseline`` commit so later runs
   know where to start. Learn more about this step in :doc:`usage/index`.

#. Make a change and commit it.

   .. code-block:: bash

      cat > demo.py <<'EOF'
      def greet() -> str:
          return "hi"
      EOF
      git add demo.py
      git commit -m "feat: add greet helper"

   This conventional commit describes a new feature, which usually implies a
   MINOR version bump.

#. Recommend the next version.

   .. code-block:: bash

      bumpwright bump --decide

   .. code-block:: text

      Suggested bump: minor
      - [MINOR] demo:greet: Added public symbol

   ``bumpwright`` inspects commits since the baseline and suggests the next
   semantic version. The lines following the suggestion list the impacts that
   informed it. Note that ``bumpwright bump --decide`` compares ``HEAD`` to the
   last release or ``HEAD^``.

   .. code-block:: bash

      bumpwright bump --decide --format md

   .. code-block:: text

      ## Suggested bump: minor
      - [MINOR] demo:greet: Added public symbol

   .. code-block:: bash

      bumpwright bump --decide --format json

   .. code-block:: json

      {"suggested_bump": "minor", "impacts": [{"scope": "demo:greet", "level": "MINOR", "description": "Added public symbol"}]}

#. Apply the bump and tag the release.

   .. code-block:: bash

      bumpwright bump --commit --tag

   This updates version files, creates a ``chore(release): <version>`` commit,
   and tags the release. When ``--commit`` is used, this is the default commit
   message. Omit ``--commit`` and ``--tag`` to preview the bump without
   modifying the repository.

Flow
----

.. code-block:: text

   Git commit
       |
       v
   bumpwright bump --decide
       |
       v
   Version recommendation
       |
       v
   bumpwright bump --commit --tag
       |
       v
   Release

For deeper explanations of commands, flags, and configuration, see
:doc:`usage/index` and :doc:`configuration`.

