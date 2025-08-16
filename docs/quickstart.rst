Quickstart
==========

Start with a tiny example project to see **bumpwright** in action.

Install
-------

.. code-block:: bash

   pip install bumpwright

**Command**

- ``pip install bumpwright`` – Install the CLI from PyPI.

Set up repo
-----------

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
   bumpwright init

**Commands**

- ``mkdir demo && cd demo`` – Create and enter project directory.
- ``git init`` – Initialise repository.
- ``cat > pyproject.toml <<'EOF' ... EOF`` – Add minimal project metadata.
- ``git add pyproject.toml`` – Stage configuration file.
- ``git commit -m "chore: initial commit"`` – Commit baseline.
- ``bumpwright init`` – Record baseline for bumpwright.

Run analysis
------------

Records a ``chore(release): initialise baseline`` commit so later runs
know where to start. Learn more about this step in :doc:`usage/index`.

   
.. code-block:: bash

   cat > demo.py <<'EOF'
   def greet() -> str:
       return "hi"
   EOF
   git add demo.py
   git commit -m "feat: add greet helper"
   bumpwright bump --decide

.. code-block:: text

   Suggested bump: minor
   - [MINOR] demo:greet: Added public symbol

**Commands**

- ``cat > demo.py <<'EOF' ... EOF`` – Add sample code.
- ``git add demo.py`` – Stage change.
- ``git commit -m "feat: add greet helper"`` – Commit feature indicating MINOR bump.
- ``bumpwright bump --decide`` – Recommend the next version.

Release
-------

.. code-block:: bash

   bumpwright bump --commit --tag

**Command**

- ``bumpwright bump --commit --tag`` – Apply the version bump and tag the release.

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

