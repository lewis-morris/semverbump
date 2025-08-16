GraphQL Analyser
================

Detects changes in GraphQL schema definitions.

Dependencies
~~~~~~~~~~~~

* ``graphql-core``

Enable or disable
~~~~~~~~~~~~~~~~~

Set ``graphql`` under ``[analysers]``.

.. code-block:: toml

   [analysers]
   graphql = true  # set to false to disable

Severity rules
~~~~~~~~~~~~~~

* Added type → minor
* Removed type → major
* Added field → minor
* Removed field → major

Detectable change
~~~~~~~~~~~~~~~~~

.. code-block:: diff

   @@
-  type User { id: ID! }
+  type User { id: ID!, email: String }

Example output
~~~~~~~~~~~~~~

.. code-block:: text

   - [MINOR] User.email: Added field 'email'
