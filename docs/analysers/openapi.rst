OpenAPI Analyser
================

Detects changes in OpenAPI specification files.

Dependencies
~~~~~~~~~~~~

* ``PyYAML``

Enable or disable
~~~~~~~~~~~~~~~~~

Enable the analyser and specify spec paths in ``bumpwright.toml``.

.. code-block:: toml

   [analysers]
   openapi = true

   [openapi]
   paths = ["openapi.yaml"]

Severity rules
~~~~~~~~~~~~~~

* Added endpoint → minor
* Removed endpoint → major
* Added schema → minor
* Removed schema → major
* Changed schema definition → major

Detectable change
~~~~~~~~~~~~~~~~~

.. code-block:: diff

   @@
   paths:
     /pets:
-      get: {}
+      post: {}

Example output
~~~~~~~~~~~~~~

.. code-block:: text

   - [MAJOR] GET /pets: Removed endpoint
