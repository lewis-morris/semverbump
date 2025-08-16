Quickstart
==========

Set up a tiny project and run Bumpwright in minutes.

Install
-------

.. code-block:: bash

   pip install bumpwright

Minimal project
---------------

.. code-block:: bash

   mkdir demo && cd demo
   git init
   cat > pyproject.toml <<'EOF2'
   [project]
   name = "demo"
   version = "0.1.0"
   EOF2
   git add pyproject.toml
   git commit -m "chore: initial commit"
   bumpwright init
   echo "def greet() -> str:\n    return 'hi'\n" > demo.py
   git add demo.py
   git commit -m "feat: add greet helper"

Interpreting the decision
-------------------------

.. code-block:: bash

   bumpwright bump --decide

.. code-block:: text

   Suggested bump: minor
   - [MINOR] demo:greet: Added public symbol

Bumpwright inspects the public API and recommends the next semantic version.

Apply the bump and tag
----------------------

.. code-block:: bash

   bumpwright bump --commit --tag

The version file is updated and a Git tag is created for the release.

For more detail see :doc:`usage/index` and :doc:`configuration`.

