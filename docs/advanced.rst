Advanced Usage
==============

Customize rules for version decisions:

.. code-block:: toml

   [rules]
   return_type_change = "major"

Exclude paths from API scanning:

.. code-block:: toml

   [ignore]
   paths = ["tests/**", "examples/**"]

Apply a bump and commit/tag automatically:

.. code-block:: console

   semverbump bump --base v1.0.0 --head HEAD --commit --tag
