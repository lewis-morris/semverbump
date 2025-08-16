Web Route Analyser
==================

Detects HTTP route changes in Flask or FastAPI apps.

Dependencies
~~~~~~~~~~~~

* ``Flask`` or ``FastAPI``

Enable or disable
~~~~~~~~~~~~~~~~~

Set ``web_routes`` under ``[analysers]``.

.. code-block:: toml

   [analysers]
   web_routes = true  # set to false to disable

Severity rules
~~~~~~~~~~~~~~

* Added route → minor
* Removed route → major
* Added optional param → minor
* Added required param → major
* Removed optional param → minor
* Removed required param → major
* Param became optional → minor
* Param became required → major

Detectable change
~~~~~~~~~~~~~~~~~

.. code-block:: diff

   @@
   @app.get("/users/{user_id}")
   -def get_user(user_id: int):
   -    ...
   +def get_user(user_id: int, verbose: bool = False):
   +    ...

Example output
~~~~~~~~~~~~~~

.. code-block:: text

   - [MINOR] GET /users/{user_id}: Added optional param 'verbose'
